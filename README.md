![API YamDB workflow](https://github.com/holohup/foodgram_project_react/actions/workflows/foodgram.yml/badge.svg)

# Дипломный проект - бэкэнд для Foodgram

## Постановка задачи

К имеющемуся фронтэнду нужно написать бэкэнд по подробной спецификации на нужные эндпоинты и описанию проекта. Проект представляет из себя удобный сервис для любителей готовить. На сайт можно добавлять рецепты, ставить к ним тэги, добавлять в избранное, подписываться на любимых авторов, а также добавлять рецепты в списки покупок - сайт автоматически считает, сколько и чего нужно купить и позволяет скачать эту информацию одним файлом. 

### Язык проекта

Проект будет драгоценным камнем в короне моих работ на гитхабе, которые собрались к окончанию курса на Yandex.practicum, поэтому, как и остальные проекты для портфолио, он пишется на английском языке. Для публично-доступной версии будут убраны ссылки на redoc, ингридиенты, любезно предоставленные Яндексом и пр. конфиденциальные данные, будет переведен без купюр и этот текст.

## Технологии

## Установка и запуск проекта

Существует три уровня знакомства с проектом:

### Посмотреть, как работает

Просто зайдите на сайт http://ondeletecascade.ru . На сайте уже загружены рецепты, можно понажимать на кнопки, скачать список покупок и вообще, воспользоваться доступным функционалом.

### Запустить на своем компьютере при помощи docker-compose

```
git clone https://github.com/holohup/foodgram-project-react.git && cd foodgram-project-react/infra && mv .env.sample .env && docker-compose up -d --remove-orphans
```
Обратите внимание: в файле _.env.sample_ лежат тестовые настройки, необходимые для запуска проекта. Отредактируйте их для себя. Если Вы хотите запустить проект на сервере, или вообще любом компьютере, отличным от Вашего текущего, убедитесь, что Вы раскомментировали последнюю строчку этого файла.

После успешной установки можно сразу посмотреть, как проект работает: http://localhost
Ознакомиться с подробной спецификацией на эндпоинты можно по адресу http://localhost/api/docs

Для удобства ознакомления к проекту прилагается файл с готовыми данными - рецептами, пользователями и т.д. - при выборе этого способа ознакомления с проектом, он автоматически загружается в базу и можно сразу смотреть, как что работает.

### Сделать все своими руками (самый трудный и почетный путь)


## Тестирование

Если Вы планируете вносить изменения в проекте, рекомендуется тестировать их прежде, чем они попадут в репозиторий. Для эндпоинтов, основных моделей и функций проекта написаны тесты. Чтобы их запустить, в виртуальном окружении проекта из папки _backend_, или в контейнере backend выполните команду:
`
python manage.py test
`
Также рекомендуется настроить Ваш github action проекта так, чтобы эти тесты автоматически запускались перед деплоем, это позволит избежать многих досадных недоразумений.