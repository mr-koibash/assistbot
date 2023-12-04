class AssistbotConfig:
    class __AssistbotSection:
        @classmethod
        def section_name(cls) -> str:
            return cls.__name__

    class Telebot(__AssistbotSection):
        TOKEN = 'token'
        ADMINS = 'admins'

    class Email(__AssistbotSection):
        LOGIN = 'login'
        PASSWORD = 'password'
        HOST = 'host'
        PORT_SSL = 'port_ssl'
        PORT_TLS = 'port_tls'
        MAIL_END = 'mail_end'

    class Messaging(__AssistbotSection):
        QUEUE_RESET_TIMER = 'queue_reset_timer'

    class Recipients(__AssistbotSection):
        ...
