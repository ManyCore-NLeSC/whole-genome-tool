from praline.core import Manager, BeginMessage, CompleteMessage, ProgressMessage
from praline.component import TreeMultipleSequenceAligner

_INTERCEPT_TIDS = {TreeMultipleSequenceAligner.tid}

class ConstellationManager(Manager):
    def execute_many(self, requests, parent_tag):
        for tid, inputs, tag, env in requests:
            # We're not handling these tasks in this manager, so execute them
            # normally using the functionality of the superclass.
            if not tid in _INTERCEPT_TIDS:
                gen = super(ConstellationManager, self).execute_many(self,
                                                                     requests,
                                                                     parent_tag)
                for message in gen:
                    yield message

            # We want to intercept execution of these tasks and send them off
            # to constellation. First pass a message saying we've begun
            # executing the tasks.
            for tid, inputs, tag, env in requests:
                begin_message = BeginMessage(parent_tag)
                begin_message.tag = tag
                yield begin_message


            # TODO: convert task inputs to constellation format, send it to
            # Constellation and wait for completion. Yield ProgressMessage
            # instances to report progress to the UI if applicable.


            # Yield completion messages for the tasks, containing the outputs
            # returned by Constellation.
            for tid, inputs, tag, env in requests:
                # TODO: convert Constellation results into PRALINE objects.
                outputs = None

                complete_message = CompleteMessage(outputs=outputs)
                complete_message.tag = tag
                yield complete_message
