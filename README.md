# XLSX Mailings Assessment

Django проект для импорта email-рассылок из XLSX файлов.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd src
python manage.py migrate
```

## Использование

```bash
python manage.py import_mailings /path/to/file.xlsx
```

## Тесты

```bash
python manage.py test
```
