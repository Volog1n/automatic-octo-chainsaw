#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse
import platform
from pathlib import Path


def parse_args():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(description='Установка и настройка PDF Parser')
    parser.add_argument('--venv', action='store_true', help='Создать виртуальное окружение')
    parser.add_argument('--dev', action='store_true', help='Установить в режиме разработчика')
    return parser.parse_args()


def create_venv():
    """Создание виртуального окружения."""
    print("Создание виртуального окружения...")
    venv_dir = Path('venv')
    
    if venv_dir.exists():
        print(f"Виртуальное окружение уже существует в {venv_dir}")
        return venv_dir
    
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print(f"Виртуальное окружение создано в {venv_dir}")
        return venv_dir
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании виртуального окружения: {e}")
        sys.exit(1)


def get_pip_cmd(venv_path=None):
    """Получить команду pip с учетом виртуального окружения."""
    if venv_path:
        if platform.system() == 'Windows':
            pip_path = venv_path / 'Scripts' / 'pip'
        else:
            pip_path = venv_path / 'bin' / 'pip'
        return str(pip_path)
    else:
        return 'pip'


def install_dependencies(pip_cmd, dev_mode=False):
    """Установка зависимостей."""
    print("Установка зависимостей...")
    
    try:
        # Обновление pip
        subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True)
        
        # Установка зависимостей
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        
        # Установка пакета
        if dev_mode:
            subprocess.run([pip_cmd, 'install', '-e', '.'], check=True)
            print("PDF Parser установлен в режиме разработчика")
        else:
            subprocess.run([pip_cmd, 'install', '.'], check=True)
            print("PDF Parser успешно установлен")
            
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке зависимостей: {e}")
        sys.exit(1)


def main():
    """Основная функция установки."""
    args = parse_args()
    
    print("=" * 50)
    print("Установка PDF Parser")
    print("=" * 50)
    
    # Проверка наличия файлов проекта
    if not Path('requirements.txt').exists():
        print("Ошибка: requirements.txt не найден. Убедитесь, что скрипт запущен из корневой директории проекта.")
        sys.exit(1)
    
    venv_path = None
    if args.venv:
        venv_path = create_venv()
    
    pip_cmd = get_pip_cmd(venv_path)
    install_dependencies(pip_cmd, args.dev)
    
    # Создаем тестовый PDF-файл для демонстрации
    create_test_pdf = Path('samples') / 'test.pdf'
    if not create_test_pdf.parent.exists():
        os.makedirs(create_test_pdf.parent)
    
    print("=" * 50)
    print("Установка завершена!")
    print(f"Используйте пример: python example.py samples/test.pdf")
    print("=" * 50)


def create_test_pdf():
    """Попытка создать тестовый PDF-файл."""
    try:
        import fitz
        
        test_pdf_path = Path('samples') / 'test.pdf'
        if not test_pdf_path.parent.exists():
            os.makedirs(test_pdf_path.parent)
        
        doc = fitz.open()
        page = doc.new_page()
        
        # Добавляем тестовый текст
        text_rect = fitz.Rect(50, 50, 550, 750)
        page.insert_text(
            text_rect.tl,
            "Это тестовый PDF-документ для проверки парсера.\n\n"
            "PDF Parser - быстрый и точный парсер PDF-документов на Python.\n\n"
            "Этот PDF был создан автоматически при установке парсера.",
            fontsize=12
        )
        
        doc.save(str(test_pdf_path))
        doc.close()
        
        print(f"Создан тестовый PDF-файл: {test_pdf_path}")
    except ImportError:
        print("Модуль PyMuPDF не установлен, пропускаем создание тестового PDF")
    except Exception as e:
        print(f"Ошибка при создании тестового PDF: {e}")


if __name__ == "__main__":
    main()
    try:
        create_test_pdf()
    except:
        pass 