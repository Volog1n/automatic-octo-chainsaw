#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import time
from typing import List, Dict

from pdf_parser import PDFParser


def parse_args() -> argparse.Namespace:
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(description='PDF Parser - быстрое и точное извлечение текста из PDF')
    
    parser.add_argument('pdf_file', type=str, nargs='*',
                        help='Путь к PDF-файлу или директории с PDF-файлами')
    
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='Путь для сохранения результата (по умолчанию выводится в stdout)')
    
    parser.add_argument('-m', '--metadata', action='store_true',
                        help='Извлекать текст вместе с метаданными (позиция, шрифт и т.д.)')
    
    parser.add_argument('-d', '--detailed', action='store_true',
                        help='Использовать более детальное извлечение (медленнее, но точнее)')
    
    parser.add_argument('-t', '--tables', action='store_true',
                        help='Извлекать таблицы (экспериментальная функция)')
    
    parser.add_argument('-s', '--single-thread', action='store_true',
                        help='Запретить многопоточность')
    
    return parser.parse_args()


def get_pdf_files(paths: List[str]) -> List[str]:
    """
    Получение списка PDF-файлов из указанных путей.
    
    Args:
        paths: Список путей к файлам или директориям
        
    Returns:
        List[str]: Список путей к PDF-файлам
    """
    pdf_files = []
    
    for path in paths:
        if os.path.isdir(path):
            # Если путь указывает на директорию, добавляем все PDF-файлы из неё
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
        elif os.path.isfile(path) and path.lower().endswith('.pdf'):
            # Если путь указывает на PDF-файл, добавляем его
            pdf_files.append(path)
        else:
            print(f"Предупреждение: {path} не является PDF-файлом или директорией с PDF-файлами")
    
    return pdf_files


def main():
    """Основная функция программы."""
    args = parse_args()
    
    if not args.pdf_file:
        print("Ошибка: не указан PDF-файл или директория")
        sys.exit(1)
    
    # Получаем список PDF-файлов для обработки
    pdf_files = get_pdf_files(args.pdf_file)
    
    if not pdf_files:
        print("Ошибка: не найдено ни одного PDF-файла")
        sys.exit(1)
    
    # Инициализируем парсер
    parser = PDFParser(use_multithreading=not args.single_thread)
    
    start_time = time.time()
    
    # Обрабатываем файлы
    if len(pdf_files) == 1:
        # Если только один файл
        pdf_path = pdf_files[0]
        
        if args.metadata:
            # Извлечение текста с метаданными
            result = parser.extract_text_with_metadata(pdf_path, detailed=args.detailed)
            
            # Форматируем вывод
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    for block in result:
                        f.write(f"Страница {block.page_num}, ({block.x0}, {block.y0})-({block.x1}, {block.y1}): {block.text}\n")
            else:
                for block in result:
                    print(f"Страница {block.page_num}, ({block.x0:.1f}, {block.y0:.1f})-({block.x1:.1f}, {block.y1:.1f}): {block.text}")
        
        elif args.tables:
            # Извлечение таблиц
            tables = parser.extract_tables(pdf_path)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    for i, table in enumerate(tables):
                        f.write(f"Таблица {i+1}:\n{table}\n\n")
            else:
                for i, table in enumerate(tables):
                    print(f"Таблица {i+1}:")
                    print(table)
                    print()
        
        else:
            # Простое извлечение текста
            text = parser.extract_text(pdf_path)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(text)
            else:
                print(text)
    else:
        # Если несколько файлов, используем пакетную обработку
        results = parser.batch_process(pdf_files)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                for file, content in results.items():
                    f.write(f"=== {file} ===\n")
                    f.write(content)
                    f.write("\n\n")
        else:
            for file, content in results.items():
                print(f"=== {file} ===")
                print(content[:1000] + "..." if len(content) > 1000 else content)
                print("\n")
    
    elapsed = time.time() - start_time
    print(f"Обработка завершена за {elapsed:.2f} секунд")


if __name__ == "__main__":
    main() 