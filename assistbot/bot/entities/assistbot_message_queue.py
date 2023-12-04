import os
import shutil

from datetime import datetime
from assistbot.bot.constants.assistbot_message_types import AssistbotMessageTypes
from assistbot.bot.entities.assistbot_message import AssistbotMessage


today = datetime.now()

class AssistbotMessageQueue:
    def __init__(self, queue_reset_timer: int):
        self._queue_reset_timer = queue_reset_timer

        self.messages = []
        self._first_message_time = datetime.now()
        self._photos_counter = 0

    def append(self, message: AssistbotMessage):
        self._reset_queue_if_necessary()
        self.messages.append(message)

        if message.type == AssistbotMessageTypes.PHOTO:
            self._photos_counter += 1

    def get_folder_name(self) -> str:
        self._reset_queue_if_necessary()
        return self._create_folder_name()

    def get_photos_number(self) -> int:
        return self._photos_counter

    def clear(self):
        self._reset_queue()

    def _reset_queue_if_necessary(self):
        if self._first_message_time is None or \
                (datetime.now() - self._first_message_time).seconds > self._queue_reset_timer:
            self._reset_queue()

    def _reset_queue(self):
        folder_name = self._create_folder_name()
        if os.path.exists(folder_name):
            shutil.rmtree(f'{folder_name}')
        self.messages.clear()
        self._first_message_time = datetime.now()

        self._photos_counter = 0

    def _create_folder_name(self) -> str:
        return str(self._first_message_time.strftime('%Y.%m.%d_%H.%M.%S'))
