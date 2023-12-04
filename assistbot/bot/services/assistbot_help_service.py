from assistbot.bot.constants.answers.assistbot_help_answers import AssistbotHelpAnswers
from assistbot.bot.constants.assistbot_commands import AssistbotCommands
from assistbot.bot.constants.assistbot_config import AssistbotConfig


class AssistbotHelpService:
    def __init__(self, bot, config):
        self._bot = bot
        self._config = config

    def process_help_request(self, message):
        message_words = ['']
        if message.text is not None:
            message_words = message.text.split()

        if len(message_words) == 1:
            self._process_common_help_request(message)
        elif len(message_words) > 1 and message_words[1].lower() in AssistbotCommands.EMAIL:
            self._process_email_help_request(message)
        else:
            ...

    def _process_common_help_request(self, message):
        text = f'{AssistbotHelpAnswers.COMMON}:\n'
        text += f'/{AssistbotCommands.HELP[0]} {AssistbotCommands.EMAIL[0]}'
        self._bot.reply_to(message, text)

    def _process_email_help_request(self, message):
        queue_reset_timer = \
            self._config[AssistbotConfig.Messaging.section_name()][AssistbotConfig.Messaging.QUEUE_RESET_TIMER]

        text = ''
        text += f'{AssistbotHelpAnswers.Email.QUEUE_INFO}: ' \
                f'{queue_reset_timer}\n\n'
        text += f'{AssistbotHelpAnswers.Email.SENDING}:\n' \
                f'/{AssistbotCommands.EMAIL[0]} получатель Тема письма\n\n'
        text += f'{AssistbotHelpAnswers.Email.CLEAR}:\n' \
                f'/{AssistbotCommands.EMAIL[0]} {AssistbotCommands.EmailArguments.CLEAR[0]}\n\n'

        text += f'{AssistbotHelpAnswers.Email.RECIPIENTS}:\n'
        for (key, value) in self._config.items(AssistbotConfig.Recipients.section_name()):
            text += f'- {key}: {value};\n'


        self._bot.reply_to(message, text)
