# Проект парсинга pep
Парсер сайта python.org

## Режимы Парсера

### whats-new
Собирает ссылки на статьи о нововведениях с их авторами.

### latest-versions
Собриает ссылки на документации различных версий Python с их статусом.

### download
Скачивает документацию в формате PDF.

### pep
Собриает общую сводку по документам PEP.


## Закуск проекта
Клонировать репозиторий и перейти в него в командной строке:
```bash
git clone git@github.com:zamaev/bs4_parser_pep.git
cd bs4_parser_pep
```

Установить и активировать виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```

Установить зависимости из файла requirements.txt:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Перейти в папку со скриптом
```bash
cd src
```

## Использование парсера
```bash
usage: main.py [-h] [-c] [-o {pretty,file}]
               {whats-new,latest-versions,download,pep}

Парсер документации Python

positional arguments:
  {whats-new,latest-versions,download,pep}
                        Режимы работы парсера

optional arguments:
  -h, --help            show this help message and exit
  -c, --clear-cache     Очистка кеша
  -o {pretty,file}, --output {pretty,file}
                        Дополнительные способы вывода данных
```

## Авторы
- [Айдрус](https://github.com/zamaev)