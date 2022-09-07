import os

from cat.simulation.builder import RasaBuilder
from cat.simulation.generator import IntentGenerator, ResponseGenerator
from cat.simulation.common.persistence import Persistor
from cat.simulation.interaction.user import UserProfile
from cat.simulation.simulator import DialogSimulator
from cat.simulation.interaction.frames import TransactionFrame
from cat.simulation.common.transform import *

from argparse import ArgumentParser
from cat.db.database import PostgreSQLDatabase
from typing import List, Dict
from cat.common.utils import add_db_arguments, load_json, str2bool
import logging

logger = logging.getLogger('simulator')
logging.basicConfig(level=logging.DEBUG)


class BotGenerator:

    def __init__(self, bot_name: str,
                 num_dialogs_per_task: int,
                 tasks: List[Task],
                 schema: Dict,
                 response_templates: Dict,
                 intent_templates: Dict,
                 num_nlu_samples: int,
                 transaction_failure_ratio: float = 0.5,
                 user_profile: UserProfile = None,
                 paraphrasers: List[str] = [],
                 pivot_languages = [],
                 schema_name='public',
                 deploy=False):
        self.bot_name = bot_name
        self.tasks = tasks
        self.frames = [TransactionFrame(task) for task in self.tasks]
        self.schema = schema
        self.schema_name = schema_name
        self.utterance_templates = response_templates
        self.intent_templates = intent_templates
        self.num_dialogs = num_dialogs_per_task
        self.num_nlu_samples = num_nlu_samples
        self.transaction_failure_ratio = transaction_failure_ratio
        self.user_profile = user_profile

        self.persistor = Persistor(bot_name)

        self.simulator = DialogSimulator(tasks=self.tasks, persistor=self.persistor)
        self.response_generator = ResponseGenerator(frames=self.frames,
                                                    response_templates=response_templates,
                                                    schema_name=schema_name,
                                                    schema=schema,
                                                    persistor=self.persistor)
        self.intent_generator = IntentGenerator(frames=self.frames,
                                                intent_templates=intent_templates,
                                                paraphrasers=paraphrasers,
                                                pivot_languages=pivot_languages,
                                                persistor=self.persistor)

    def generate(self):
        # Run dialog simulation
        if self.num_dialogs > 0:
            self.simulator.run(num_dialogs=self.num_dialogs, tasks=self.tasks)
        # Run NLU generation/intent extraction
        intents = self.intent_generator.generate_intents(
            num_samples=self.num_nlu_samples
        )

        # extract actions and code
        responses, actions = self.response_generator.generate_responses_actions()
        self.rasa_builder = RasaBuilder(frames=self.frames,
                                        responses=responses,
                                        actions=actions,
                                        intents=intents,
                                        schema_name=self.schema_name,
                                        persistor=self.persistor)
        self.rasa_builder.build_files()
        self.rasa_builder.persist()


if __name__ == '__main__':
    parser = ArgumentParser()

    add_db_arguments(parser)

    parser.add_argument('-b', '--bot_name', type=str, help='The name of the bot to train', required=True)
    parser.add_argument('-n', '--num_task_dialogs', type=int, default=0,
                        help='The number of dialogs to simulate per task')
    parser.add_argument('-s', '--num_nlu_samples', type=int, default=0,
                        help='The number of NLU samples to generate per intent template')
    parser.add_argument('-tasks', '--task_config', type=str, help='File with the task configuration (.json)',
                        required=True)
    parser.add_argument('-config', '--schema_config', type=str, help='File with the schema configuration (.json)',
                        required=True)
    parser.add_argument('-nlg', '--template_config', type=str,
                        help='File with the response and intent templates (.json)', required=True)
    parser.add_argument('-p', '--paraphrasers', type=str, nargs='*', default=[],
                        help='The type of paraphraser "g" for Google translate "p" for PPDB')
    parser.add_argument('-l', '--pivot_languages', type=str, nargs='*', default=['en', 'de', 'fr'])
    parser.add_argument('-f', '--failure_ratio', type=int, default=0.5,
                        help='The ratio of failing transactions during simulation')
    parser.add_argument('-d', '--deploy', type=str2bool, nargs='?', const=True, default=False,
                        help='Whether to move bot to test directory', required=False)

    args = parser.parse_args()

    db = PostgreSQLDatabase.get_instance(db_name=args.db_name, schema_name=args.db_schema, user=args.db_user,
                                         password=args.db_password, host=args.db_host, port=args.db_port)

    task_config = load_json(args.task_config)
    schema_config = load_json(args.schema_config)
    template_config = load_json(args.template_config)

    tasks = transform_tasks(task_config)
    schema = transform_config(schema_config)
    response_templates, intent_templates = transform_templates(template_config)

    generator = BotGenerator(bot_name=args.bot_name,
                             tasks=tasks,
                             schema=schema,
                             response_templates=response_templates,
                             intent_templates=intent_templates,
                             num_dialogs_per_task=args.num_task_dialogs,
                             num_nlu_samples=args.num_nlu_samples,
                             transaction_failure_ratio=args.failure_ratio,
                             user_profile=None,
                             paraphrasers=args.paraphrasers,
                             pivot_languages=args.pivot_languages,
                             schema_name=args.db_schema,
                             deploy=args.deploy)
    generator.generate()
