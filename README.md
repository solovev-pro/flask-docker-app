# Flask + Docker Project

Проект мини-приложения "Догоняй" на Flask

## Стек технологий
* Python 3.10
* Flask
* Flask-SQLAlchemy
* Docker

## Инструкция по запуску
Откройте терминал в корневой папке проекта и выполните команду:
'''bash
docker build -t flask-app .
docker run -d -p 5000:8000 --name my-flask flask-app
Откройте браузер и перейдите пл адресу: http://localhost:5000