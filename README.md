# hw05_final

[![CI](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)

Yatube - социальная сеть для публикации постов. Проект выполнен с использованием фреймворка Django. Посты выводятся на странице в хронологическом порядке публикации. Новые - выше. Пагинация настроена на вывод десяти постов на странице. Посты могут публиковаться в разных тематических группах или вне каких-либо групп. Группы может создавать только администратор сайта. 

## Технологии
- Python 3.7 
- Django 2.2
- Pytest 6.2
- Pillow 8.3

## Запуск проекта в dev-режиме

- Установите и активируйте виртуальное окружение
- Установите зависимости из файла requirements.txt 
- `pip install -r requirements.txt`
В папке с файлом manage.py выполните миграции:
`python3 manage.py migrate`
В папке с файлом manage.py выполните команду:
`python3 manage.py runserver`

Автор: Варкулевич Михаил
