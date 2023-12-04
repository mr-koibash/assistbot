FROM python:3.11.5

# prepare folder structure
RUN mkdir -p assistbot
WORKDIR /assistbot
RUN mkdir -p configs
RUN mkdir -p files

# install requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# copy code
COPY assistbot assistbot
COPY main.py main.py

CMD ["python3", "main.py"]
