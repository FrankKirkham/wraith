import mido
from typing import Tuple

class VirtualMidiPort():
    port_name: str
    port = None
    last_l_message = None
    last_r_message = None

    def __init__(self, port_name: str) -> None:
        self.port_name = port_name

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

        l_message, r_message = messages

        if l_message is not None and (self.last_l_message is None or l_message != self.last_l_message):
            self.port.send(l_message)
            self.last_l_message = l_message

        if r_message is not None and (self.last_r_message is None or r_message != self.last_r_message):
            self.port.send(r_message)
            self.last_r_message = r_message