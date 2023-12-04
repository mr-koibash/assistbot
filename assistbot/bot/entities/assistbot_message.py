from assistbot.bot.constants.assistbot_message_types import AssistbotMessageTypes

class AssistbotMessage:
    def __init__(self, message_type: AssistbotMessageTypes, data: str):
        self.type = message_type
        self.data = data
