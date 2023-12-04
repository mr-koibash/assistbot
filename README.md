# AssistBot

Bot sends messages from telegram to email.

## 1. Install

1.1 Create config.ini file:
```bash
cp -p configs/config-example.ini configs/config.ini 
```
And fill config.ini by own data.

1.2 Build docker image:
```bash
docker build . --tag assistbot
```

1.3 Run docker image:
```bash
docker run -d \
          --restart unless-stopped \
          -v ./configs:/assistbot/configs \
          -v ./files:/assistbot/files \
          assistbot
```
## 2. Usage

Just write to bot:
```
/help
```



