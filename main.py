import telebot
import configparser

from assistbot.bot.constants.assistbot_commands import AssistbotCommands
from assistbot.bot.services.assistbot_list_service import AssistbotMailService
from assistbot.bot.services.assistbot_help_service import AssistbotHelpService
from assistbot.bot.constants.assistbot_config import AssistbotConfig


# reading configs
config = configparser.ConfigParser()
config.read('configs/config.ini')

# initializing bot
bot = telebot.TeleBot(config[AssistbotConfig.Telebot.section_name()][AssistbotConfig.Telebot.TOKEN], parse_mode=None)
telebot_list_service = AssistbotMailService(bot, config, files_folder='files')
telebot_help_service = AssistbotHelpService(bot, config)


all_content_types = ['text', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice',
                     'location', 'contact', 'new_chat_members', 'left_chat_member', 'new_chat_title',
                     'new_chat_photo', 'delete_chat_photo', 'group_chat_created',
                     'supergroup_chat_created', 'channel_chat_created', 'migrate_to_chat_id',
                     'migrate_from_chat_id', 'pinned_message']


@bot.message_handler(commands=AssistbotCommands.HELP)
def help_handler(message):
    if verify_user(message):
        telebot_help_service.process_help_request(message)


@bot.message_handler(commands=AssistbotCommands.EMAIL)
def email_handler(message):
    if verify_user(message):
        telebot_list_service.process_email_message(message)


@bot.message_handler(content_types=all_content_types)
def common_message_handler(message):
    if verify_user(message):
        telebot_list_service.process_common_message(message)


def verify_user(message):
    admins_uid_strings = config[AssistbotConfig.Telebot.section_name()][AssistbotConfig.Telebot.ADMINS].split(', ')
    admins_list = [int(uid) for uid in admins_uid_strings]

    uid = message.from_user.id
    if uid not in admins_list:
        return False
    return True


if __name__ == '__main__':
    bot.infinity_polling()
