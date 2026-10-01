import mido
from typing import List, Tuple

class VirtualMidiPort():
    port_name: str
    port = None
    # The last message sent for each slot of the tuple the mapper produces
    # (one per channel), so unchanged values are not resent
    last_messages: List[mido.Message | None]

    def __init__(self, port_name: str) -> None:
        self.port_name = port_name
        self.last_messages = [None, None]

    def open(self):
        self.port = mido.open_output(self.port_name, virtual=True)
        ... # add print message?

    def close(self):
        if self.port is None:
            print("Port is not open, so nothing closed")
            return

        self.port.close()
        self.port = None

    def send_message(self, messages: Tuple[mido.Message | None, mido.Message | None]):
        if self.port is None:
            raise RuntimeError("Port is not open")

        for slot, message in enumerate(messages):
            # None means nothing to control on that channel this frame
            if message is None:
                continue

            # mido refuses to compare a message against None, so only check
            # for a repeat once there is something to compare against
            last = self.last_messages[slot]
            if last is not None and message == last:
                continue

            self.port.send(message)
            self.last_messages[slot] = message