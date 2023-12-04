from __future__ import annotations


class AssistbotMail:
    def __init__(self, user_from: str, recipients: str, subject: str, text: str, files_list: list):
        self._user_from = user_from
        self._recipients = recipients
        self._subject = subject
        self._text = text
        self._files_list = files_list

    def get_user_from(self) -> str:
        return self._user_from

    def get_recipients(self) -> str:
        return self._recipients

    def get_subject(self) -> str:
        return self._subject

    def get_text(self) -> str:
        return self._text

    def get_files_list(self) -> list:
        return self._files_list

    @classmethod
    def create_empty(cls) -> AssistbotMail:
        telebot_mail = AssistbotMail('', '', '', '', [])
        return telebot_mail
