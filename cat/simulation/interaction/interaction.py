from cat.simulation.common.intents import Intent
from cat.simulation.common.actions import AbstractAction
from cat.simulation.common.constants import *
from cat.simulation.common.persistence import Persistor
from typing import List
from threading import Lock
import time


class InteractionManager:

    def __init__(self, persistor: Persistor):
        self.persistor = persistor
        self.actions = []
        self.intents = []
        self.action_lock = Lock()
        self.intent_lock = Lock()

    def prepare(self):
        self.actions = []
        self.intents = []
        self.action_lock = Lock()
        self.intent_lock = Lock()

    def send_intent(self, intent: Intent):
        self.intent_lock.acquire()
        if intent:
            self.persistor.log_intent(intent)
            self.intents.append(intent)
        self.intent_lock.release()

    def send_actions(self, actions: List[AbstractAction]):
        self.action_lock.acquire()
        self.persistor.log_actions(actions)
        self.actions += actions
        self.action_lock.release()

    def read_intent(self):
        # acquire and release lock until intent can be read
        while True:
            self.intent_lock.acquire()
            if self.intents:
                intent = self.intents.pop()
                self.intent_lock.release()
                return intent
            self.intent_lock.release()
            # give other thread a chance to continue
            time.sleep(0.02)

    def read_actions(self):
        # acquire and release lock until actions can be read
        while True:
            self.action_lock.acquire()
            if self.actions:
                send_actions, self.actions = self.actions, []
                self.action_lock.release()
                return send_actions
            self.action_lock.release()
            time.sleep(0.01)

    def peek_intent(self):
        return self.intents[-1] if len(self.intents) > 0 else None

    def peek_actions(self):
        return self.actions