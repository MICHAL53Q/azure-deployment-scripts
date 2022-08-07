FROM python:3.9-alpine

RUN apk update && apk add \
    libffi-dev \
    build-base \
    py3-setuptools

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
