from cat.simulation.interaction.interaction import InteractionManager
from cat.simulation.common.intents import *
from cat.simulation.common.constants import *
from cat.simulation.interaction.goals import *
import logging
import threading
import random
import numpy as np

logger = logging.getLogger('user-simulator')


class UserProfile:
    def __init__(self, ambiguity: float, indecision: float, experience: float, cooperation: float, flexibility: float,
                 give_up_probability: float, informativity_mu: int, informativity_sd: float,
                 max_propose_transaction_deny: int = 1, max_select_deny: int = 1,
                 max_choice_deny: int = 1, max_transaction_deny: int = 1, max_options_scroll=3, max_rephrase=3,
                 max_followup_tasks=1):
        self.ambiguity = ambiguity
        self.indecision = indecision
        self.experience = experience
        self.cooperation = cooperation
        self.flexibility = flexibility
        self.give_up_probability = give_up_probability
        self.informativity_mu = informativity_mu
        self.informativity_sd = informativity_sd
        self.max_propose_transaction_deny = max_propose_transaction_deny
        self.max_select_deny = max_select_deny
        self.max_choice_deny = max_choice_deny
        self.max_transaction_deny = max_transaction_deny
        self.max_rephrase = max_rephrase
        self.max_options_scroll = max_options_scroll
        self.max_followup_tasks = max_followup_tasks
        self.options_position = 0

    @staticmethod
    def random_profile():
        ambiguity = random.uniform(0.0, 1.0)
        indecision = random.uniform(0.0, 1.0)
        experience = random.uniform(0.0, 1.0)
        cooperation = random.uniform(0.0, 1.0)
        flexibility = random.uniform(0.0, 1.0)
        give_up_probability = random.uniform(0.0, 0.3)
        informativity_mu = random.randint(1, 3)
        informativity_sd = random.uniform(1.0, 2.0)
        return UserProfile(ambiguity, indecision, experience, cooperation, flexibility, give_up_probability,
                           informativity_mu, informativity_sd)

    def do_cooperate(self):
        return random.uniform(0.0, 1.0) > self.cooperation

    def do_rephrase(self):
        give_up = self.do_give_up()
        if give_up:
            return False
        if self.max_rephrase > 0:
            self.max_rephrase -= 1
            return True
        return False

    def do_ask_options(self):
        if random.uniform(0.0, 1.0) < self.experience:
            return False
        return True

    def do_ask_different_options(self):
        if self.max_options_scroll > 0:
            if random.uniform(0.0, 1.0) < self.indecision:
                self.max_options_scroll -= 1
                return True
        return False

    def do_ask_previous_options(self):
        # only ask previous options if have scrolled forward
        # returning false, the options will be scrolled forward
        do_prev = self.options_position > 0 and random.uniform(0.0, 1.0) > 0.5
        if do_prev:
            self.options_position -= 1
            return True
        self.options_position += 1
        return False

    def do_ask_next_task(self):
        if self.max_followup_tasks > 0:
            return random.choice([True, False])
        return False

    def do_deny_proposed_transaction(self):
        deny = self._do_deny() and self.max_propose_transaction_deny > 0
        if deny:
            self.max_propose_transaction_deny -= 1
        return deny

    def do_deny_select(self):
        deny = self._do_deny() and self.max_select_deny > 0
        if deny:
            self.max_select_deny -= 1
        return deny

    def do_deny_choice(self):
        deny = self._do_deny() and self.max_choice_deny > 0
        if deny:
            self.max_choice_deny -= 1
        return deny

    def do_deny_transaction(self):
        deny = self._do_deny() and self.max_transaction_deny > 0
        if deny:
            self.max_transaction_deny -= 1
        return deny

    def _do_deny(self):
        return random.uniform(0.0, 1.0) < self.indecision

    def do_ambiguous_choice(self):
        return random.uniform(0.0, 1.0) > self.ambiguity

    def do_give_up(self):
        return random.uniform(0.0, 1.0) < self.give_up_probability

    def do_resample(self):
        return random.uniform(0.0, 1.0) > self.flexibility

    def inform_n(self):
        n = np.random.normal(self.informativity_mu, self.informativity_sd)
        return max(1, int(n))


class UserSimulator:

    def __init__(self, isim: InteractionManager, tasks: List[Task]):
        self.isim = isim
        self.state = None
        self.tasks = tasks

    def prepare(self, goal, profile: UserProfile = None):
        goal.resample()
        if not profile:
            profile = UserProfile.random_profile()
        self.state = UserState(goal, profile)

    def run(self):
        self.isim.send_intent(Greet())
        while True:
            while not self.state.is_satisfied():
                actions = self.isim.read_actions()
                next_intent = self.state.next_intent(actions)
                self.isim.send_intent(next_intent)
                if isinstance(next_intent, Bye):
                    return
            actions = self.isim.read_actions()
            next_intent = self.state.next_intent(actions)
            self.isim.send_intent(next_intent)
            if isinstance(next_intent, Bye):
                return


class UserState:

    def __init__(self, goal: TransactionGoal, profile=None):
        self.goal = goal
        self.transaction_agenda = UserAgenda(goal, profile)
        self.sub_agendas = [UserAgenda(goal, profile) for goal in goal.subgoals]
        self.profile = profile
        self.history = []
        self.agent_history = []

    def next_intent(self, turn):
        # update state based on last actions
        self.agent_history.append(turn)
        self.update_goals(turn)

        for action in turn:
            if isinstance(action, UtterGreet):
                return self.transaction_agenda.on_greet()
            if isinstance(action, UtterAskNextTask):
                return self.transaction_agenda.on_ask_next_task()
            if isinstance(action, UtterProposeBeginTransaction):
                return self.transaction_agenda.on_propose_begin_transaction(action.frame.name)
            if isinstance(action, UtterAskRephrase):
                agenda, frame = self.get_agenda()
                return agenda.on_ask_rephrase(frame)
            if isinstance(action, ActionSelect):
                agenda, frame = self.get_agenda(action.frame)
                if frame.is_filled():
                    continue
                return agenda.on_form_request(frame)
            if isinstance(action, UtterRequestChoice):
                agenda, frame = self.get_agenda(action.frame)
                return agenda.on_request(frame)
            if isinstance(action, ActionProposeForm):
                agenda, frame = self.get_agenda(action.frame)
                return agenda.on_propose_form(frame.data, frame.single_result)
            if isinstance(action, UtterProposeChoice):
                agenda, frame = self.get_agenda(action.frame)
                return agenda.on_propose_choice(frame.data)
            if isinstance(action, ActionProposeTransaction):
                agenda, frame = self.get_agenda(action.frame)
                return agenda.on_propose_transaction(frame.data)
            if isinstance(action, ActionFailedTransaction):
                agenda, frame = self.get_agenda(action.frame)
                return agenda.on_failed_transaction(frame)
            if isinstance(action, ActionSuccessfulTransaction):
                agenda, frame = self.get_agenda(action.frame)
                return agenda.on_success_transaction(frame)
            if isinstance(action, UtterBye):
                return Bye()

    def is_satisfied(self):
        return self.transaction_agenda.is_satisfied()

    def update_goals(self, turn):
        frame_actions = [action for action in turn if hasattr(action, 'frame')]
        for action in frame_actions:
            agenda, frame = self.get_agenda(action.frame)
            agenda.goal.update(action)

    def get_agenda(self, frame=None):
        if not frame:
            frame = self.get_last_frame()
        if isinstance(frame, TransactionFrame):
            return self.transaction_agenda, frame
        elif isinstance(frame, SubFrame):
            for agenda in self.sub_agendas:
                if agenda.goal.transaction_name == frame.transaction_name and agenda.goal.transaction_slot == frame.reference:
                    return agenda, frame

    def get_last_frame(self):
        for turn in reversed(self.agent_history):
            for action in reversed(turn):
                if isinstance(action, UtterProposeBeginTransaction):
                    return action.frame
                if isinstance(action, ActionSelect):
                    return action.frame
                if isinstance(action, UtterRequestChoice):
                    return action.frame
        return None


class UserAgenda:

    def __init__(self, goal: Goal, profile: UserProfile):
        self.goal = goal
        self.profile = profile

    def is_satisfied(self):
        return self.goal.satisfied

    def on_greet(self):
        if isinstance(self.goal, TransactionGoal):
            num_inform = self.profile.inform_n()
            inform_values = {}
            for _ in range(num_inform):
                available_slots = set(self.goal.get_informable_slot_names()) - inform_values.keys()
                if available_slots:
                    slot_name = random.choice(list(available_slots))
                    inform_values[slot_name] = DUMMY_VALUE
            return Transaction(transaction=self.goal.transaction_name, entity_values=inform_values)
        return Bye()

    def on_ask_next_task(self):
        if self.profile.do_ask_next_task():
            self.goal.resample()
            return Affirm()
        self.goal.satisfied = True
        return Deny()

    def on_ask_rephrase(self, frame: Frame):
        if not self.profile.do_rephrase():
            return GiveUp()
        if isinstance(self.goal, TransactionGoal):
            return self.on_greet()
        if isinstance(self.goal, SelectGoal):
            return self.on_form_request(frame)
        if isinstance(self.goal, ChooseGoal):
            return self.on_request(frame)
        return GiveUp()

    def on_form_request(self, frame: SelectFrame):
        if isinstance(self.goal, SelectGoal):
            requested_slot = frame.requested_slot
            if self.profile.do_ask_options():
                return AskOptions()
            if requested_slot.data_type == 'bool':
                return self.on_bool_request(requested_slot)
            if self.profile.do_cooperate():
                num_slots = self.profile.inform_n()
                informed_values = {requested_slot.name: DUMMY_VALUE}
                for _ in range(num_slots - 1):
                    informable_values = frame.get_informable_slot_names(informed_values.keys())
                    if len(informable_values) > 0:
                        rnd_slot = random.choice(informable_values)
                        informed_values[rnd_slot] = DUMMY_VALUE
                return InformForm(informed_values)
            else:
                if random.choice([True, False]):
                    return InformForm({requested_slot.name: DONT_CARE})
                else:
                    available_slots = frame.get_informable_slot_names()
                    if available_slots:
                        rnd_slot = random.choice(available_slots)
                    else:
                        rnd_slot = requested_slot.name
                    return InformForm({rnd_slot: DUMMY_VALUE})
        return GiveUp()

    def on_request(self, frame: ChoiceFrame):
        if isinstance(self.goal, ChooseGoal):
            requested_slot = frame.get_slot()
            # handle boolean slots differently.
            if requested_slot.data_type == 'bool':
                return self.on_bool_request(requested_slot)
            return Inform({requested_slot.name: DUMMY_VALUE})
        return GiveUp()

    def on_bool_request(self, slot: Slot):
        response = random.choice([True, False])
        # allow just yes or no answers
        use_affirm_deny = random.choice([True, False])
        if use_affirm_deny:
            return Affirm(entity=slot.name) if response else Deny(entity=slot.name)
        else:
            # explicit phrasing
            return InformBool(slot.name, response)

    def on_propose_begin_transaction(self, transaction_name):
        if isinstance(self.goal, TransactionGoal) and self.goal.transaction_name == transaction_name:
            if self.profile.do_deny_proposed_transaction():
                return Deny()
            # todo do ask transaction options
            return Affirm()
        return Deny()

    def on_propose_form(self, entity, single_result):
        if isinstance(self.goal, SelectGoal):
            if single_result:
                if self.profile.do_deny_select():
                    return Deny()
                return Affirm()
            else:
                if self.profile.do_ask_different_options():
                    if self.profile.do_ask_previous_options():
                        return AskPreviousOptions()
                    return AskMoreOptions()
                else:
                    return SelectOption(random.randint(0, MAX_RESULTS))
        return Deny()

    def on_propose_choice(self, entity):
        if isinstance(self.goal, ChooseGoal):
            if self.profile.do_deny_choice():
                return Deny()
            return random.choice([Affirm(), Done()])
        return Deny()

    def on_propose_transaction(self, data):
        if isinstance(self.goal, TransactionGoal):
            if self.profile.do_deny_transaction():
                return Deny()
            return random.choice([Affirm(), Done()])
        return Deny()

    def on_failed_transaction(self, data):
        return GiveUp()

    def on_success_transaction(self, data):
        return Done()
