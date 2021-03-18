#FROM python:3.9-buster

FROM python:3.9
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/pip_cache
WORKDIR /opt/app

COPY documentHandlerService/requirements.txt /opt/app
COPY documentHandlerService /opt/app

RUN pip install -r requirements.txt

RUN python manage.py makemigrations
RUN python manage.py migrate

RUN python manage.py test
