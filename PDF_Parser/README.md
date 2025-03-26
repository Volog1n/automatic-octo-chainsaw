# PDF Parser

Быстрый и точный парсер PDF-документов на Python, способный обрабатывать большие файлы (более 1000 страниц и 100 МБ).

## Характеристики

- Высокая скорость обработки
- Точное извлечение текста
- Обработка больших файлов
- Многопоточная обработка для увеличения производительности

## Установка

```bash
pip install -r requirements.txt
```

## Использование

```python
from pdf_parser import PDFParser

# Создание парсера
parser = PDFParser()

# Извлечение текста из PDF-файла
text = parser.extract_text("path/to/file.pdf")
print(text)

# Извлечение текста с метаданными
text_with_metadata = parser.extract_text_with_metadata("path/to/file.pdf")
```

## Опции

- `extract_text`: Быстрое извлечение чистого текста
- `extract_text_with_metadata`: Извлечение текста с информацией о форматировании
- `extract_tables`: Извлечение таблиц из PDF (экспериментальная функция)
- `batch_process`: Обработка нескольких PDF-файлов 