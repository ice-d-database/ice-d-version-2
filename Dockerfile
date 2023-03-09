FROM python:3.9.6 as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DOCKER=true


WORKDIR /var/www/berkeley-geo/app
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc
COPY ./django-app/Pipfile .
COPY ./django-app/Pipfile.lock .
# ADD data_migration /var/www/berkeley-geo/data_migration
RUN pipenv install
