FROM python:3.7.2

WORKDIR /usr/local/app/
COPY ./ /usr/local/app/

RUN pip install -r requirements.txt

ENTRYPOINT [ "python3", "uniexecutor_cli/main.py"]
