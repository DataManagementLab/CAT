from cat.simulation.interaction.interaction import InteractionManager
from cat.simulation.common.intents import *
from cat.simulation.common.actions import *
from cat.simulation.common.constants import *
from cat.simulation.interaction.frames import *
import numpy.random as random
import time
import logging

logger: logging.Logger = logging.getLogger('agent')


class AgentSimulator:

    def __init__(self, isim: InteractionManager, tasks: List[Task], failure_ratio: float = 0.5):
        self.isim = isim
        self.tasks = tasks
        self.transaction_frame: TransactionFrame = None
        self.failure_ratio = failure_ratio
        self.history = []
        self.actions = []

    def prepare(self, transaction_frame: TransactionFrame):
        self.transaction_frame = transaction_frame
        self.transaction_frame.clear()
        self.actions = []
        self.history = []

    def run(self):
        # first intent is always Greet
        self.isim.read_intent()
        self._enqueue_action(UtterGreet())
        self._send()

        while True:
            time.sleep(0.1)
            found_task = self.run_top_level_dialog()
            # if the user refuses to find the task just end the conversation
            if found_task:
                self.run_process_frames()
            # the end dialog might result in a new conversation ("Can i do anything else for you")
            next_task = self.run_end_dialog()
            # if the user denies end the dialog
            if not next_task:
                return
            # reset the dialog
            self.transaction_frame.clear(clear_subframe=True, unaffirm=True)

    def get_last_turn(self):
        return self.history[-1] if len(self.history) > 0 else None

    def get_last_action(self):
        last_turn = self.get_last_turn()
        return self.last_turn[-1] if last_turn and len(last_turn) > 0 else None

    def get_next_frame(self):
        for frame in self.transaction_frame.subframes:
            if not frame.is_affirmed():
                return frame
        if not self.transaction_frame.is_affirmed():
            return self.transaction_frame
        return None

    def complete_frame(self, frame):
        if isinstance(frame, SelectFrame):
            return self.run_select_dialog(frame)
        elif isinstance(frame, ChoiceFrame):
            return self.run_choice_dialog(frame)
        elif isinstance(frame, TransactionFrame):
            return self.run_transaction_dialog(frame)

    def run_top_level_dialog(self):
        while True:
            intent = self.isim.read_intent()

            if isinstance(intent, Transaction):
                self.transaction_frame.update_data(intent.data)
                self.actions = [UtterProposeBeginTransaction(self.transaction_frame)]
                self._send()

            if isinstance(intent, Affirm):
                return True

            if isinstance(intent, Deny):
                self._enqueue_action(UtterAskRephrase())
                self._send()

            if isinstance(intent, GiveUp):
                return False

            if isinstance(intent, Done):
                return False

    def run_process_frames(self):
        current_frame: Frame = self.get_next_frame()
        do_continue = True
        while current_frame and not current_frame.is_affirmed() and do_continue:
            do_continue = self.complete_frame(current_frame)
            current_frame = self.get_next_frame()

    def run_end_dialog(self):
        self._enqueue_action(UtterAskNextTask())
        self._send()
        time.sleep(0.1)

        # see if the user wants to try something else
        next_intent = self.isim.read_intent()
        if isinstance(next_intent, Affirm):
            self._enqueue_action(ActionRestartConversation())
            self._enqueue_action(UtterGreet())
            self._send()
            time.sleep(0.1)
            return True
        # just bye
        else:
            self._enqueue_action(UtterBye())
            self._send()
            # wait for a response
            next_intent = self.isim.read_intent()
            # clear the conversation
            if isinstance(next_intent, Bye):
                self._enqueue_action(ActionRestartConversation())
                self._send()

    def run_select_dialog(self, frame: SelectFrame):
        # ask for the param and start the form
        self._handle_select_dialog_start(frame)

        # handle dialog until the frame is affirmed
        while not frame.is_affirmed():
            # wait for the next user input
            while not self.isim.peek_intent():
                time.sleep(0.01)
            next_intent = self.isim.read_intent()

            # the user might have asked for options (filled frame or not), continue if did so
            if self._try_handle_select_options(next_intent, frame):
                continue

            # ask for frame values, if the user informed a value continue
            was_request = any([isinstance(action, ActionSelect) or isinstance(action, UtterAskRephrase) for action in self.history[-1]])
            if was_request:
                if not frame.is_filled() and self._try_handle_select_inform(next_intent, frame):
                    continue

            # the user might have affirmed the frame or uttered a choice from proposals, continue
            if self._try_handle_select_affirmation(next_intent, frame):
                continue

            if isinstance(next_intent, Deny):
                self._enqueue_actions([ActionClear(frame).run(unaffirm=True), ActionStartSelectForm(frame),
                                       ActionSelect(frame).run()])
                self._send()
                continue

            # if the user gives up return false, the global dialog will be stopped
            if isinstance(next_intent, GiveUp):
                return False
        # when the frame is affirmed, the global dialog can continue with the next subdialog
        return True

    def _handle_select_dialog_start(self, frame):
        ask_param_slot = UtterAskParameter(self.transaction_frame.get_slot(frame.reference))
        start_action = ActionStartSelectForm(frame)
        activate_action = ActionActivateSelectForm(frame)
        form_action = ActionSelect(frame).run()
        self._enqueue_actions([ask_param_slot, start_action, activate_action, form_action])
        result = self._handle_select_frame_filled(form_action.frame)
        self._send()

    def _try_handle_select_inform(self, intent: Intent, frame: SelectFrame) -> bool:
        last_requested_slot = frame.requested_slot
        # boolean slots are handled differently
        if last_requested_slot.data_type == 'bool':
            if isinstance(intent, InformBool):
                choice = intent.value
            elif isinstance(intent, Affirm):
                choice = True
            elif isinstance(intent, Deny):
                choice = False
            else:
                logger.error(f'Trying to update boolean slot but user did not respond with affirm or deny.\n'
                             f'intent: "{intent}"')
            frame.update_data(last_requested_slot.name, choice)
            # self._enqueue_action(ActionSetSlot(last_requested_slot, choice, True))
        # if the user informs a value for the requested slot
        elif isinstance(intent, InformForm):
            # update the value and ask for the next one
            frame.update_data(intent.values)
        else:
            return False
        form_action = ActionSelect(frame).run()
        # if all values are informed
        result = self._handle_select_frame_filled(form_action.frame)
        # otherwise continue
        if not result:
            self._enqueue_action(form_action)
        self._send()
        return True

    def _handle_select_frame_filled(self, frame):
        if frame.is_filled():
            # propose the result (one or more values)
            self._enqueue_action(ActionSetSlot(OPTION_RESULTS_SLOT, DUMMY_VALUE, True))
            frame.single_result = random.choice([True, False])
            self._enqueue_action(ActionProposeForm(frame))
            self._enqueue_action(ActionSetSlot(OPTION_OFFSET_SLOT, 0, True))
            return True
        return False

    def _try_handle_select_options(self, intent: Intent, frame: SelectFrame) -> bool:
        if isinstance(intent, AskOptions):
            # start the form first. this will realize ask options is required and close itself
            self._enqueue_action(ActionStartSelectForm(frame))
            self._enqueue_action(ActionActivateSelectForm(frame))
            self._enqueue_action(ActionSetSlot(OPTION_OFFSET_SLOT, 0, True))
            self._enqueue_action(ActionSetSlot(OPTION_RESULTS_SLOT, "dummy", True))
            self._enqueue_action(ActionSetSlot(REQUESTED_SLOT, None, True))
            self._enqueue_action(ActionDeactivateSelectForm())
            self._enqueue_action(ActionQuitSelectForm())
            self._enqueue_action(ActionProposeForm(frame))
            self._send()
            return True

        # if the user asks for options propose the options
        elif isinstance(intent, AskPreviousOptions) or isinstance(intent, AskMoreOptions):
            self._enqueue_action(ActionProposeForm(frame))
            self._enqueue_action(ActionSetSlot(OPTION_OFFSET_SLOT, 5))
            self._send()
            return True
        return False

    def _try_handle_select_affirmation(self, intent: Intent, frame: SelectFrame) -> bool:
        # if the user selects option/affirms single option save it and transfer value to the top level dialog
        if isinstance(intent, SelectOption):
            frame.affirm()
            # on selection the slot is set directly by the user action (button)
            self._enqueue_actions([ActionSetSlot(OPTION_CHOICE_SLOT, intent.value, True),
                                   ActionSaveOption(frame),
                                   ActionTransferSlot(frame, self.transaction_frame),
                                   ActionClear(frame).run()]
                                  )
            self._send()
            return True
        elif isinstance(intent, Affirm) or isinstance(intent, Done):
            frame.affirm()
            # on affirmation the choice slot is set within the save action
            self._enqueue_actions([ActionSaveOption(frame),
                                   ActionSetSlot(OPTION_CHOICE_SLOT, 1, True),
                                   ActionTransferSlot(frame, self.transaction_frame),
                                   ActionClear(frame).run()]
                                  )
            self._send()
            return True
        return False

    def run_choice_dialog(self, frame: ChoiceFrame):
        # utter for the parameter and request the users choice
        self._handle_choice_dialog_start(frame)

        # while the choice is not affirmed continue
        while not frame.is_affirmed():
            while not self.isim.peek_intent():
                time.sleep(0.01)
            next_intent = self.isim.read_intent()

            # affirm can be used to utter values for the boolean choice or affirmation
            was_request = any([isinstance(action, UtterRequestChoice) or isinstance(action, UtterAskRephrase) for action in self.history[-1]])
            if was_request:
                if self._try_handle_choice_inform(next_intent, frame):
                    continue

            if self._try_handle_choice_affirmation(next_intent, frame):
                continue

            if isinstance(next_intent, Deny):
                self._enqueue_actions([ActionClear(frame).run(unaffirm=True), UtterAskRephrase()])
                self._send()
                continue

            if isinstance(next_intent, GiveUp):
                return False
        return True

    def _handle_choice_dialog_start(self, frame: ChoiceFrame):
        self._enqueue_action(UtterAskParameter(self.transaction_frame.get_slot(frame.reference)))
        self._enqueue_action(UtterRequestChoice(frame))
        self._send()

    def _try_handle_choice_inform(self, intent: Intent, frame: ChoiceFrame):
        # Informing a boolean choice is handled by two intents (true and false choice), no validation
        if isinstance(intent, InformBool) or isinstance(intent, Affirm) or isinstance(intent, Deny):
            if isinstance(intent, InformBool):
                choice = intent.value
            elif isinstance(intent, Affirm):
                choice = True
            elif isinstance(intent, Deny):
                choice = False
            set_bool_choice = ActionSetBoolChoice(frame, intent.entity, choice).run()
            self._enqueue_action(set_bool_choice)
            self._enqueue_action(ActionSetSlot(intent.entity, choice, True))
            if frame.is_filled():
                self._enqueue_action(UtterProposeChoice(frame))
            else:
                self._enqueue_actions([ActionClear(frame).run(unaffirm=True), UtterAskRephrase()])
            self._send()
            return True

        # check if user is informing his choice
        if isinstance(intent, Inform):
            # validate the result
            entity = frame.get_slot().name
            value = intent.values[entity]
            validation = ActionValidateChoice(frame, entity, value).run()
            self._enqueue_action(validation)
            # if the validation succeeded
            if validation.frame.valid:
                # set the result slot
                self._enqueue_action(ActionSetSlot(entity, value="normalized", log=True))
                self._enqueue_action(ActionSetSlot(VALIDATION_RESULT_SLOT, value=True, log=True))
                frame.update_data({entity: value})
                # we should be done, propose the choice
                if frame.is_filled():
                    self._enqueue_action(UtterProposeChoice(frame))
                    self._send()
                # otherwise if no value was uttered, ask the user to rephrase
                else:
                    self._enqueue_actions([ActionClear(frame).run(unaffirm=True), UtterAskRephrase()])
                    self._send()

            # if the validation failed reset the slot and ask the user to rephrase
            else:
                self._enqueue_actions(
                    [ActionSetSlot(VALIDATION_RESULT_SLOT, value=False, log=True),
                     ActionClear(frame).run(unaffirm=True),
                     UtterAskRephrase()])
                self._send()
            return True
        return False

    def _try_handle_choice_affirmation(self, intent: Intent, frame: ChoiceFrame):
        # if the choice is affirmed by the user transfer the value to the top level
        if isinstance(intent, Affirm) or isinstance(intent, Done):
            frame.affirm()
            self._enqueue_action(ActionTransferSlot(frame, self.transaction_frame))
            self._enqueue_action(ActionClear(frame).run())
            self._send()
            return True
        return False

    def run_transaction_dialog(self, frame: TransactionFrame):
        # propose the transaction
        self._enqueue_action(ActionProposeTransaction(frame))
        self._send()

        # wait for the user to affirm it
        while not frame.is_affirmed():
            while not self.isim.peek_intent():
                time.sleep(0.01)
            next_intent = self.isim.read_intent()
            # execute the transaction on affirmation
            if isinstance(next_intent, Affirm) or isinstance(next_intent, Done):
                frame.affirm()
                call_result: ActionExecuteTransaction = ActionExecuteTransaction(frame).run()
                self._enqueue_action(call_result)
                # if the transaction fails stop the conversation
                if call_result.frame.error:
                    self._enqueue_actions([ActionSetSlot(TRANSACTION_ERROR_SLOT, call_result.frame.error, True),
                                           ActionFailedTransaction(call_result.frame).run()])
                # also stop on success
                else:
                    if call_result.frame.operation == OPERATION_SELECT:
                        self._enqueue_action(
                            ActionSetSlot(TRANSACTION_RESULT_SLOT, [call_result.frame.return_data], True))
                    self._enqueue_action(ActionSuccessfulTransaction(call_result.frame).run())
                self._send()
            # if the user denies the propose transaction stop the conversation
            if isinstance(next_intent, GiveUp) or isinstance(next_intent, Deny):
                return False
        # after the transaction is execute the user might respond
        next_intent = self.isim.read_intent()
        if isinstance(next_intent, Done) or isinstance(next_intent, GiveUp):
            return False
        return True

    def _send(self, clear=True):
        if self.actions:
            self.history.append([a for a in self.actions])
            self.isim.send_actions(self.actions)
            if clear:
                self._clear_actions()

    def _enqueue_action(self, action: AbstractAction):
        self.actions.append(action)

    def _enqueue_actions(self, actions: List[AbstractAction]):
        for action in actions:
            self._enqueue_action(action)

    def _clear_actions(self):
        if self.actions:
            del self.actions[:]
