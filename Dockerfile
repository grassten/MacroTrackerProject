FROM python:3.8

WORKDIR /app

COPY requirements.txt config.py macroapp.py ./
COPY app/ app/
COPY entrypoint.sh entrypoint.sh

RUN pip install -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["entrypoint.sh"]