import os
import ssl
import random
import string

from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate, COMMASPACE

from telebot.types import InputMediaDocument

from assistbot.bot.constants.answers.assistbot_mail_answers import AssistbotMailAnswers
from assistbot.bot.constants.assistbot_commands import AssistbotCommands
from assistbot.bot.constants.assistbot_config import AssistbotConfig
from assistbot.bot.constants.assistbot_message_types import AssistbotMessageTypes
from assistbot.bot.entities.assistbot_mail import AssistbotMail
from assistbot.bot.entities.assistbot_message import AssistbotMessage
from assistbot.bot.entities.assistbot_message_queue import AssistbotMessageQueue


class AssistbotMailService:
    def __init__(self, bot, config, files_folder):
        self._bot = bot
        self._config = config
        self._assistbot_mail = AssistbotMail.create_empty()

        queue_reset_timer = int(
            config[AssistbotConfig.Messaging.section_name()][AssistbotConfig.Messaging.QUEUE_RESET_TIMER]
        )
        self._telebot_message_queue = AssistbotMessageQueue(queue_reset_timer)

        self._files_folder = files_folder
        if not os.path.exists(self._files_folder):
            os.mkdir(self._files_folder)


    def process_common_message(self, message):
        # message can contain text or file description
        if message.text is not None:
            text = message.text if message.text is not None else message.caption

            telebot_message = AssistbotMessage(AssistbotMessageTypes.TEXT, text)
            self._telebot_message_queue.append(telebot_message)
        else:
            is_file_attached = message.document is not None or message.photo is not None or message.video is not None
            if is_file_attached:
                # create folder for files
                folder = f'{self._files_folder}/{self._telebot_message_queue.get_folder_name()}'
                if not os.path.exists(folder):
                    try:
                        os.mkdir(folder)
                    except Exception as e:
                        print(e)

                # process file info
                file_id = None
                file_name = None
                message_type = None
                if message.document is not None:
                    file_id = message.document.file_id
                    file_name = message.document.file_name
                    message_type = AssistbotMessageTypes.DOCUMENT
                elif message.photo is not None:
                    file_id = message.photo[-1].file_id
                    file_name = self._get_encoded_uuid(message.photo[-1].file_unique_id) + '.jpg'
                    message_type = AssistbotMessageTypes.PHOTO
                elif message.video is not None:
                    file_id = message.video.file_id
                    file_name = message.video.file_name
                    message_type = AssistbotMessageTypes.VIDEO

                for telebot_message in self._telebot_message_queue.messages:
                    if file_name == telebot_message.data.split('/')[-1]:
                        file_name = 'copy_' + file_name

                # save file
                file_info = self._bot.get_file(file_id)
                downloaded_file = self._bot.download_file(file_info.file_path)
                file_path = f'{folder}/{file_name}'
                with open(file_path, 'wb') as file:
                    file.write(downloaded_file)

                telebot_message = AssistbotMessage(message_type, file_path)
                self._telebot_message_queue.append(telebot_message)

                if message.caption is not None:
                    text = message.caption
                    telebot_message = AssistbotMessage(AssistbotMessageTypes.TEXT, text)
                    self._telebot_message_queue.append(telebot_message)

    def process_email_message(self, message):
        message_words = ['']
        if message.text is not None:
            message_words = message.text.split()

        if len(message_words) > 1 and message_words[1].lower() in AssistbotCommands.EmailArguments.CLEAR:
            self._clear()
            self._bot.reply_to(message, AssistbotMailAnswers.QueueStatus.CLEARED)
        elif len(message_words) < 3:
            self._bot.reply_to(message, AssistbotMailAnswers.Error.NO_SUBJECT_SPECIFIED)
        else:
            recipients_keyword = message_words[1]
            subject = ' '.join(message_words[2:])

            # check recipients
            recipients = ''
            for (key, value) in self._config.items(AssistbotConfig.Recipients.section_name()):
                if recipients_keyword.lower() == key:
                    recipients = value
                    break
            if recipients == '':
                self._bot.reply_to(message, AssistbotMailAnswers.RecipientsStatus.MISSING)
                return
            if len(recipients) == 1 and recipients[0] == '':
                self._bot.reply_to(message, AssistbotMailAnswers.RecipientsStatus.EMPTY)
                return

            # create message text
            text = ''
            files_list = []
            for telebot_message in self._telebot_message_queue.messages:
                if telebot_message.type == AssistbotMessageTypes.TEXT:
                    text += telebot_message.data
                    text += '\n\n'
                else:
                    files_list.append(telebot_message.data)

            text += self._config[AssistbotConfig.Email.section_name()][AssistbotConfig.Email.MAIL_END]\
                .replace('\\n', '\n')

            # mail DTO
            self._assistbot_mail = AssistbotMail(
                self._config[AssistbotConfig.Email.section_name()][AssistbotConfig.Email.LOGIN],
                recipients,
                subject,
                text,
                files_list
            )

            # send request to user acceptance
            files_string = ''
            for file_data in files_list:
                files_string += f'*) {file_data}\n'
            answer = f'<Получатели>: {recipients}\n' \
                     f'<Тема письма>: {subject}\n' \
                     f'<Текст>:\n{text}\n\n' \
                     f'<Список файлов>:\n{files_string}'

            self._bot.reply_to(message, answer)

            # send files in blocks of 10 docs per message
            media_group = []
            for i, file in enumerate(files_list):
                media_group.append(InputMediaDocument(open(file, 'rb')))
                if i != 0 and i % 9 == 0:
                    self._bot.send_media_group(message.chat.id, media=media_group)
                    media_group = []

            if len(media_group) != 0:
                self._bot.send_media_group(message.chat.id, media=media_group)

            self._bot.send_message(message.chat.id, AssistbotMailAnswers.Confirmation.REQUEST)
            self._bot.register_next_step_handler(message, self._request_sending_confirmation)



    def _request_sending_confirmation(self, message):
        if message.text.lower() == AssistbotCommands.Acceptance.YES:
            self._send_email(message)
            self._bot.reply_to(message, AssistbotMailAnswers.MailStatus.SUCCESS)
            self._clear()
            self._bot.send_message(message.chat.id, AssistbotMailAnswers.QueueStatus.CLEARED)
        elif message.text.lower() == AssistbotCommands.Acceptance.NO:
            self._bot.reply_to(message, AssistbotMailAnswers.QueueStatus.HELD)
        else:
            self._bot.reply_to(message, AssistbotMailAnswers.Confirmation.REPEATANCE)
            self._bot.register_next_step_handler(message, self._request_sending_confirmation)

    def _send_email(self, message):
        try:
            host = self._config[AssistbotConfig.Email.section_name()][AssistbotConfig.Email.HOST]
            port_tls = self._config[AssistbotConfig.Email.section_name()][AssistbotConfig.Email.PORT_TLS]
            login = self._config[AssistbotConfig.Email.section_name()][AssistbotConfig.Email.LOGIN]
            password = self._config[AssistbotConfig.Email.section_name()][AssistbotConfig.Email.PASSWORD]
            recipients = self._assistbot_mail.get_recipients().split(', ')

            msg = MIMEMultipart()
            msg['From'] = login
            msg['To'] = COMMASPACE.join(recipients)
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = self._assistbot_mail.get_subject()
            msg.attach(MIMEText(self._assistbot_mail.get_text()))

            files = self._assistbot_mail.get_files_list()
            for f in files or []:
                with open(f, "rb") as fil:
                    part = MIMEApplication(
                        fil.read(),
                        Name=os.path.basename(f)
                    )
                # After the file is closed
                part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
                msg.attach(part)

            # connect and send via smtp
            smtp = SMTP(host, port_tls)
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(login, password)

            smtp.sendmail(login, recipients, msg.as_string())
            smtp.close()
        except Exception as e:
            self._bot.reply_to(message, f'{AssistbotMailAnswers.Error.UNKNOWN}{str(e)}')

    def _get_encoded_uuid(self, input: str) -> str:
        encoded_output = ''
        for letter in input:
            if letter in string.ascii_letters or letter in string.digits:
                if letter == 'Z':
                    letter = 'A'
                elif letter == 'z':
                    letter = 'a'
                elif letter == '9':
                    letter = '0'
                else:
                    letter = chr(ord(letter) + 1)
            encoded_output += letter
            encoded_output += random.choice(string.ascii_letters + string.digits)

        for i in range(5):
            random_index = random.randrange(len(encoded_output))
            random_letter = random.choice(string.ascii_letters)
            encoded_output = encoded_output[:random_index] + random_letter + encoded_output[random_index:]

        return encoded_output[::-1]
        
    def _clear(self):
        self._telebot_message_queue.clear()
        self._assistbot_mail = None

