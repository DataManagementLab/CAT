import json
import logging
from datetime import datetime
import time
import os
from threading import Lock
from typing import List, Dict
from shutil import copytree, copyfile, move

import yaml

from cat.simulation.common.actions import AbstractAction
from cat.simulation.common.intents import Intent

BOTS_DIR = '../../bots'
DATA_DIR = 'data'
MODEL_DIR = 'models'
LOOKUP_TABLE_DIR = 'lookup_tables'
STORIES_FILE = 'stories.md'
NLU_FILE = 'nlu.json'
if not os.path.exists(BOTS_DIR):
    os.mkdir(BOTS_DIR)

logger = logging.getLogger('persistence')


class Persistor:

    def __init__(self, bot_name: str, timestamp=True):
        self.bot_name = bot_name
        unix_timestamp = int(time.mktime(datetime.now().timetuple()))
        self.bot_dir = os.path.join(BOTS_DIR, f'{bot_name}_{unix_timestamp}' if timestamp else bot_name)
        self.data_dir = os.path.join(self.bot_dir, DATA_DIR)
        self.stories_file = os.path.join(self.data_dir, STORIES_FILE)
        self.nlu_file = os.path.join(self.data_dir, NLU_FILE)
        self.lt_dir = os.path.join(self.data_dir, LOOKUP_TABLE_DIR)
        self.stories_file_lock = Lock()
        self.story_id = 1
        self._init_directories_()
        self._init_rasa_files()

    def _init_directories_(self):
        model_dir = os.path.join(self.bot_dir, MODEL_DIR)
        for path in [self.bot_dir, self.data_dir, self.lt_dir, model_dir]:
            if not os.path.exists(path):
                os.mkdir(path)

    def _init_rasa_files(self):
        self.config_file = os.path.join(self.bot_dir, 'config.yml')
        self.domain_file = os.path.join(self.bot_dir, 'domain.yml')
        self.actions_file = os.path.join(self.bot_dir, 'actions.py')
        self.credentials_file = os.path.join(self.bot_dir, 'credentials.yml')
        self.endpoints_file = os.path.join(self.bot_dir, 'endpoints.yml')
        self.schema_config_file = os.path.join(self.bot_dir, 'schema_config.json')

    def persist_nlu_data(self, nlu_data: Dict, lookup_tables: List[Dict]):
        for lookup_table in lookup_tables:
            lookup_file = os.path.join(self.lt_dir, lookup_table['file'])
            with open(lookup_file, mode='w', encoding='utf-8') as f:
                for element in lookup_table['elements']:
                    f.writelines(f'{element}\n')

        with open(self.nlu_file, mode='w', encoding='utf-8') as f:
            json.dump(nlu_data, f, indent=2)

    def persist_action_code(self, action_code: str):
        with open(self.actions_file, mode='w', encoding='utf-8') as f:
            f.write(action_code)

    def perist_schema_file(self, config):
        with open(self.schema_config_file, mode='w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    def persist_domain(self, domain):
        with open(self.domain_file, mode='w', encoding='utf-8') as f:
            yaml.dump(domain, f)

    def persist_endpoints(self, endpoints):
        with open(self.endpoints_file, mode='w', encoding='utf-8') as f:
            yaml.dump(endpoints, f)

    def persist_config(self, config):
        with open(self.config_file, mode='w', encoding='utf-8') as f:
            yaml.dump(config, f)

    def persist_credentials(self, credentials):
        with open(self.credentials_file, mode='w', encoding='utf-8') as f:
            yaml.dump(credentials, f)

    # bootstrapping
    def copy_utils(self):
        copytree(os.path.abspath('../db'), os.path.abspath(os.path.join(self.bot_dir, 'db')))
        copyfile(os.path.abspath('../common/duckling.py'),
                 os.path.abspath(os.path.join(self.bot_dir, 'duckling.py')))
        copyfile(os.path.abspath('../common/rasa_utils.py'),
                 os.path.abspath(os.path.join(self.bot_dir, 'rasa_utils.py')))
        copyfile(os.path.abspath('../common/policies.py'),
                 os.path.abspath(os.path.join(self.bot_dir, 'policies.py')))
        with open(os.path.abspath(os.path.join(self.bot_dir, '__init__.py')), mode='w') as f:
            f.close()

    def deploy_test_bot(self):
        if not os.path.exists('../../archive'):
            os.mkdir('../../archive')
        if os.path.exists('../../testbot'):
            unix_timestamp = int(time.mktime(datetime.now().timetuple()))
            old_test_bot = move(os.path.abspath('../../testbot'),
                                os.path.abspath(f'archive/testbot_{unix_timestamp}'))
            logger.info(f'Archived previous test bot to {old_test_bot}')
        new_test_bot = move(self.trainer.directory, 'testbot')
        logger.info(f'Moved training data to {new_test_bot}')

    # Log during simulation
    def new_story(self):
        with open(self.stories_file, mode='a', encoding='utf-8') as f:
            if self.story_id > 1:
                f.write('\n')
            f.write(f'## story_{self.story_id}\n')
            self.story_id += 1

    def log_intent(self, intent: Intent):
        # file lock to
        while True:
            self.stories_file_lock.acquire()
            if intent.do_log():
                with open(self.stories_file, mode='a', encoding='utf-8') as f:
                    f.write(f'* {intent}\n')
            self.stories_file_lock.release()
            return

    def log_actions(self, actions: List[AbstractAction]):
        while True:
            self.stories_file_lock.acquire()
            with open(self.stories_file, mode='a', encoding='utf-8') as f:
                for action in actions:
                    if action.do_log():
                        f.write(f'\t- {str(action)}\n')
            self.stories_file_lock.release()
            return
