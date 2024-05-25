FROM python:3.10-slim-buster
# Install python packages
COPY requirements.txt /tmp

RUN apt update

RUN apt install -y libpq-dev python-dev gcc

RUN pip install --upgrade pip

RUN pip install -r /tmp/requirements.txt

CMD mlflow ui --host 0.0.0.0
# CMD python main.py