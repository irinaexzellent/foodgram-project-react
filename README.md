![example workflow](https://github.com/irinaexzellent/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)

# О ПРОЕКТЕ

Cайт Foodgram, «Продуктовый помощник». На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд. 

Проект доступен по адресу:

```
http://158.160.0.245
```

# ОПИСАНИЕ КОМАНД ДЛЯ ЗАПУСКА ПРИЛОЖЕНИЯ

1. Клонировать проект:
```
git@github.com:irinaexzellent/foodgram-project-react.git
```
2. Добавить **Action secrets** в репозитории на GitHub в разделе settings -> Secrets:

```
DOCKER_PASSWORD - пароль от DockerHub;
DOCKER_USERNAME - имя пользователя на DockerHub;
HOST - ip-адрес сервера;
SSH_KEY - приватный ssh ключ (публичный должен быть на сервере);
TELEGRAM_TO - id своего телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
TELEGRAM_TOKEN - токен бота (получить токен можно у @BotFather, /token, имя бота)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=new_user(установить свой)
POSTGRES_PASSWORD=new_password(установить свой)
DB_HOST=postgres
DB_PORT=5432
```
3. Установить соединение с сервером по протоколу ssh:
```
ssh username@server_address
```
username - имя пользователя, под которым будет выполнено подключение к серверу,
    
server_address - IP-адрес сервера или доменное имя.
```
*  Добавить файлы docker-compose.yaml и nginx/default.conf из проекта на сервер в home/<ваш_username>/docker-compose.yaml и home/<ваш_username>/nginx/default.conf соответственно
```
# Проверка работы приложения

Внести любые изменения в проект и выполнить:
```
git add .
git commit -m "..."
git push
```
Комманда git push является триггером workflow проекта.
При выполнении команды git push запустится набор блоков комманд jobs (см. файл yamdb_workflow.yaml).
Последовательно будут выполнены следующие этапы:
* tests - тестирование проекта на соответствие PEP8 и тестам pytest.
* build_and_push_to_docker_hub - после успешного прохождения тестов собирается образ (image) для docker контейнера 
и отправлятеся в DockerHub
* deploy - после отправки образа на DockerHub начинается деплой проекта на сервере.
* send_message - после сборки и запуска контейнеров происходит отправка сообщения в 
  телеграм об успешном окончании workflow

После выполнения вышеуказанных процедур необходимо установить соединение с сервером:
```
ssh username@server_address
```
Отобразить список работающих контейнеров:
```
sudo docker container ls
```
Статус контейнеров будет в состоянии Up:
```
CONTAINER ID   IMAGE                                    COMMAND                  CREATED             STATUS             PORTS
  NAMES
314c96e0700d   nginx:1.19.3                             "/docker-entrypoint.…"   About an hour ago   Up About an hour   0.0.0.0:80->80/tcp, :::80->80/tcp
  irina-nginx-1
a9292559bac8   irinaexcellent/foodgram_backend:latest   "/bin/sh -c 'gunicor…"   About an hour ago   Up About an hour
  irina-backend-1
35c7760850ea   postgres:13.0-alpine                     "docker-entrypoint.s…"   2 hours ago         Up About an hour   0.0.0.0:5432->5432/tcp, :::5432->5432/tcp 
  irina-db-1
```
Выполнить миграции в контейнере web:
```
sudo docker compose exec backend python manage.py migrate
```
Для создания нового суперпользователя можно выполнить команду:
```
sudo docker compose exec backend python manage.py createsuperuser
```
и далее указать: 
```
Email:
Username:
Password:
Password (again):
```
Для остановки и удаления контейнеров и образов на сервере:
```
sudo docker stop $(sudo docker ps -a -q) && sudo docker rm $(sudo docker ps -a -q) && sudo docker rmi $(sudo docker images -q)
```
Для удаления volume базы данных:
```
sudo docker volume rm логин_сервера_postgres_data
```

## Автор

* **Ирина Иконникова** - (https://github.com/irinaexzellent)
