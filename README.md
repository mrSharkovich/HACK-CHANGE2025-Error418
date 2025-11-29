# HACK-CHANGE2025-Error418
[![License](https://img.shields.io/badge/license-MIT-orange)](https://github.com/Krekep/degann/blob/main/LICENSE)

Репозиторий для проекта хакатона HACK & CHANGE 2025 команды **Error418** по созданию образовательного веб-сайта, трек Студент.
## Команда
### Название команды: _Error 418_
### Состав команды:
- Гнатив Мария _backend-разработчик_
- Паксялина Дарья _frontend-разработчик, UX/UI дизайнер_
- Шабанова Ксения _Проектировщик баз данных, тестировщик_
---
## Install

>Для запуска проекта необходим установленный Python 3.11

Скачайте репозиторий в виде zip-архива, распакуйте и выполните команду из корня репозитория
```bash
pip install -r requirements.txt
```

Рекомендуется использовать виртуальное окружение для изоляции зависимостей проекта.

Для Windows (Command Prompt):
```bash
python -m venv .venv
.venv\Scripts\activate
```


Для запуска программы выполните в корне проекта
```bash
python app.py
```

---
## Structure

#### Структура проекта:
```
error/
│
├── app.py          # Главный файл приложения на Flask
├── database.py     # Файл для работы с БД
├── schema.sql	    # Скрипт для инициализации структуры БД
├── templates/      # Папка для HTML-шаблонов
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── course.html
├── instance/	    # Папка для хранения БД
│   └── learning_platform.db 
├── materials/	    # Папка с материалами для уроков
│   ├── images/
│   │   └── image_1.png
│   └── pdfs/
│       └── pdf_1.pdf
├── .venv/          # Папка с виртуальным окружением
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Demonstration
Демонстрацию работы проекта можно посмотреть по [ссылке](<https://drive.google.com/file/d/1zTqDb1-aqgpTr8NwROs6TcTuwSdP4z0t/view>).

