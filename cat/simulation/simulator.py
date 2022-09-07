import logging
from threading import Thread
from typing import List

from cat.simulation.common.model import Task
from cat.simulation.common.persistence import Persistor
from cat.simulation.interaction.agent import AgentSimulator
from cat.simulation.interaction.interaction import InteractionManager
from cat.simulation.interaction.user import UserSimulator
from cat.simulation.interaction.frames import TransactionFrame
from cat.simulation.interaction.goals import TransactionGoal

logger = logging.getLogger('simulator')


class DialogSimulator:

    def __init__(self, tasks: List[Task], persistor: Persistor, failure_ratio=0.5):
        self.persistor = persistor
        self.tasks = tasks
        self.interaction = InteractionManager(persistor=persistor)
        self.agent = AgentSimulator(self.interaction, self.tasks, failure_ratio=failure_ratio)
        self.user = UserSimulator(self.interaction, self.tasks)
        self.user_profile = None

    def run(self, num_dialogs: int, tasks: List[Task]):
        total_dialogs = len(tasks) * num_dialogs
        story_number = 0

        for task in tasks:
            transaction_frame = TransactionFrame(task)
            transaction_goal = TransactionGoal(task)

            for i in range(num_dialogs):
                story_number += 1
                self.persistor.new_story()
                logger.info(f'Simulating dialog {story_number}/{total_dialogs}')

                self.user.prepare(transaction_goal, profile=self.user_profile)
                self.agent.prepare(transaction_frame)

                # threading to run user and agent simulator
                user_thread = Thread(target=self.user.run)
                agent_thread = Thread(target=self.agent.run)

                user_thread.start()
                agent_thread.start()

                # wait for tasks to finish before continuing
                agent_thread.join()
                user_thread.join()
