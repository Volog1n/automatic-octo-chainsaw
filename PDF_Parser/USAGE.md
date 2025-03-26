# Руководство по использованию PDF Parser

## Установка

### Стандартная установка

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/pdf_parser.git
cd pdf_parser

# Установка зависимостей
pip install -r requirements.txt

# Установка пакета
pip install .
```

### Установка с помощью скрипта

```bash
# Установка в обычном режиме
python install_and_setup.py

# Установка с созданием виртуального окружения
python install_and_setup.py --venv

# Установка в режиме разработчика
python install_and_setup.py --dev
```

## Использование в командной строке

После установки парсер PDF можно использовать через командную строку:

```bash
# Базовое использование
pdf_parser path/to/file.pdf

# Сохранение извлеченного текста в файл
pdf_parser path/to/file.pdf -o output.txt

# Извлечение текста с метаданными
pdf_parser path/to/file.pdf -m

# Использование более точного (но медленного) метода извлечения
pdf_parser path/to/file.pdf -m -d

# Обработка всех PDF в директории
pdf_parser path/to/directory/with/pdfs/

# Запрет многопоточности
pdf_parser path/to/file.pdf -s
```

## Использование в коде Python

### Простое извлечение текста

```python
from pdf_parser import PDFParser

# Инициализация парсера
parser = PDFParser()

# Извлечение текста из PDF-файла
text = parser.extract_text("path/to/file.pdf")
print(text)
```

### Извлечение текста с метаданными

```python
from pdf_parser import PDFParser

parser = PDFParser()

# Извлечение текста с информацией о форматировании
blocks = parser.extract_text_with_metadata("path/to/file.pdf")

for block in blocks:
    print(f"Страница {block.page_num}, позиция: ({block.x0}, {block.y0})-({block.x1}, {block.y1})")
    print(f"Текст: {block.text}")
    if block.font:
        print(f"Шрифт: {block.font}, размер: {block.font_size}")
    print("-" * 50)
```

### Пакетная обработка нескольких файлов

```python
from pdf_parser import PDFParser
import glob

parser = PDFParser()

# Поиск всех PDF-файлов в директории
pdf_files = glob.glob("path/to/directory/*.pdf")

# Пакетная обработка
results = parser.batch_process(pdf_files)

for file_path, content in results.items():
    print(f"Файл: {file_path}")
    print(f"Размер извлеченного текста: {len(content)} символов")
    print("-" * 50)
```

### Использование с отключенной многопоточностью

```python
from pdf_parser import PDFParser

# Отключение многопоточности (для больших файлов, когда есть проблемы с памятью)
parser = PDFParser(use_multithreading=False)

text = parser.extract_text("path/to/large/file.pdf")
```

## Рекомендации

1. Для больших файлов (более 100 МБ) рекомендуется использовать многопоточную обработку (включена по умолчанию)
2. Для более точного извлечения текста используйте параметр `detailed=True` в методе `extract_text_with_metadata`
3. При обработке большого количества файлов используйте функцию `batch_process` для оптимального использования ресурсов

## Известные ограничения

1. Извлечение таблиц находится в экспериментальном состоянии и может работать не со всеми форматами таблиц
2. Некоторые PDF-файлы с нестандартным форматированием могут обрабатываться некорректно
3. Очень большие файлы (более 1 ГБ) могут требовать значительных системных ресурсов 