![API YamDB workflow](https://github.com/holohup/foodgram-project-react/actions/workflows/foodgram.yml/badge.svg)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)

# Diploma project - Foodgram backend

## Problem statement

The goal of this project is to build a backend for an existing frontend application, Foodgram. Foodgram is a convenient service for food lovers where users can add recipes, tag them, add them to favorites, follow their favorite authors, and create shopping lists. The site automatically calculates how much of each ingredient is needed and allows users to download this information in a single file.

## Technologies

The project has been tested on Python 3.7, but the author sees no reason why it should not work on later versions within the 3 branch.

## Installation and project launch

There are three levels of familiarity with the project:

### To see how it works

Simply visit the website http://ondeletecascade.ru. Recipes are already uploaded to the site, so you can click on buttons, download shopping lists, and use the available functionality.

### Running on your own computer using docker-compose

#### Downloading and running the project:

```
git clone https://github.com/holohup/foodgram-project-react.git && cd foodgram-project-react/infra && cp .env.sample .env && docker-compose up -d --remove-orphans
```
Note: the file .env.sample contains test settings necessary for running the project in "see how it works" mode. If you want something more, edit them to your liking; the variable names are quite clear. If you want to run the project on a server or any computer other than your current one, make sure you uncomment the last line of this file and enter an IP address or hostname.

#### Collect static files, do migrations:

```
docker-compose exec -it backend python manage.py collectstatic --noinput && docker-compose exec -it backend python manage.py migrate
```
After a successful launch, you can familiarize yourself with the detailed specification for endpoints at http://localhost/api/docs/

For now, the project is empty, so there's not much to see. For convenience, a file with ready-made data - recipes, users, etc. - is attached to the project. Apply it:
```
docker-compose exec -it backend fixtures/presets.sh
```
**!NB** You should load presets before performing any operations with the database, such as registering a user or creating a recipe, etc. If you have already done something on the project, it will not be possible to perform this operation. In this case, it is best to start the installation process again, clearing the computer of existing volumes that may contain old data.

Now you can:
- Log in as an administrator at: http://localhost/admin/ with the credentials admin@ngs.ru / admin and see how everything is organized there.
- Browse recipes and register: http://localhost/

### Do everything by yourself (the hardest and most honorable way)

To begin with, you need to clone the repository:
```
git clone https://github.com/holohup/foodgram-project-react.git
```
Follow these steps after:
- Install Python: You can download Python from the official website and install it on your system.
- Create a virtual environment: You can create a virtual environment using virtualenv or pipenv to manage project dependencies.
- Install the required dependencies.
```pip install -r requirements.txt```
- Create a PostgreSQL database: You can create a PostgreSQL database using the command line or a PostgreSQL client like pgAdmin.
- Edit the settings.py file to your liking. 

After that, run:
```bash
python manage.py runserver
```
This will run the backend without nginx and the frontend. You can edit the code and test how the requests work. This is the closest way to get familiar with the project. Don't forget to set the value of the variable DJANGO_DEBUG_MODE to True in your system so that all the functionality of the project is available without collecting static files and the project works in DEBUG mode.

## Testing

If you are planning to make changes to the project, it is recommended to test them before they are pushed to the repository. Tests have been written for the project's endpoints, main models, and functions. To run them, activate the virtual environment of the project from the backend folder, or in the backend container, run the command:
```
python manage.py test
```
To execute it in Docker:
```
docker-compose exec -it backend python manage.py test
```
It is also recommended to configure your project's GitHub action to automatically run these tests before deployment. This will help avoid many frustrating misunderstandings.
