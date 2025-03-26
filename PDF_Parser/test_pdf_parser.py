#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest
import tempfile
from pdf_parser import PDFParser, TextBlock

# Для создания тестового PDF-файла
import fitz


class TestPDFParser(unittest.TestCase):
    """Тесты для PDFParser."""
    
    @classmethod
    def setUpClass(cls):
        """Создание тестовых PDF-файлов перед запуском тестов."""
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.sample_pdf_path = os.path.join(cls.temp_dir.name, "sample.pdf")
        cls.large_pdf_path = os.path.join(cls.temp_dir.name, "large.pdf")
        
        # Создаем простой PDF-файл
        doc = fitz.open()
        page = doc.new_page()
        
        # Добавляем текст на страницу
        text_rect = fitz.Rect(50, 50, 550, 750)
        page.insert_text(
            text_rect.tl,  # top-left point
            "Это тестовый PDF-документ для проверки парсера.\n"
            "Вторая строка текста.\n"
            "Третья строка текста с кириллицей.",
            fontsize=12
        )
        
        # Сохраняем PDF
        doc.save(cls.sample_pdf_path)
        doc.close()
        
        # Создаем "большой" PDF-файл (для тестирования многопоточности)
        large_doc = fitz.open()
        for i in range(150):  # 150 страниц
            page = large_doc.new_page()
            text_rect = fitz.Rect(50, 50, 550, 750)
            page.insert_text(
                text_rect.tl,
                f"Страница {i+1}\n"
                f"Это тестовый текст на странице {i+1}.\n"
                f"Еще одна строка с текстом.",
                fontsize=12
            )
        
        large_doc.save(cls.large_pdf_path)
        large_doc.close()
    
    @classmethod
    def tearDownClass(cls):
        """Удаление временных файлов после тестов."""
        cls.temp_dir.cleanup()
    
    def test_extract_text(self):
        """Тест извлечения текста."""
        parser = PDFParser()
        text = parser.extract_text(self.sample_pdf_path)
        
        # Проверяем, что текст извлечен успешно
        self.assertIn("Это тестовый PDF-документ", text)
        self.assertIn("Вторая строка", text)
        self.assertIn("Третья строка текста с кириллицей", text)
    
    def test_extract_text_with_metadata(self):
        """Тест извлечения текста с метаданными."""
        parser = PDFParser()
        blocks = parser.extract_text_with_metadata(self.sample_pdf_path)
        
        # Проверяем, что получены блоки с правильной структурой
        self.assertIsInstance(blocks, list)
        self.assertTrue(len(blocks) > 0)
        
        for block in blocks:
            self.assertIsInstance(block, TextBlock)
            self.assertIsInstance(block.text, str)
            self.assertIsInstance(block.page_num, int)
            self.assertIsInstance(block.x0, float)
            self.assertIsInstance(block.y0, float)
            self.assertIsInstance(block.x1, float)
            self.assertIsInstance(block.y1, float)
    
    def test_extract_large_pdf(self):
        """Тест обработки большого PDF-файла с многопоточностью."""
        parser = PDFParser(use_multithreading=True)
        text = parser.extract_text(self.large_pdf_path)
        
        # Проверяем, что текст извлечен успешно
        self.assertIn("Страница 1", text)
        self.assertIn("Страница 50", text)
        self.assertIn("Страница 150", text)
    
    def test_batch_processing(self):
        """Тест пакетной обработки нескольких PDF-файлов."""
        parser = PDFParser()
        pdf_files = [self.sample_pdf_path, self.large_pdf_path]
        results = parser.batch_process(pdf_files)
        
        # Проверяем, что все файлы обработаны
        self.assertEqual(len(results), len(pdf_files))
        self.assertIn(self.sample_pdf_path, results)
        self.assertIn(self.large_pdf_path, results)
        
        # Проверяем содержимое
        self.assertIn("Это тестовый PDF-документ", results[self.sample_pdf_path])
        self.assertIn("Страница 1", results[self.large_pdf_path])


def create_test_pdf(output_path, num_pages=1, text_per_page="Test page"):
    """Утилита для создания тестовых PDF-файлов."""
    doc = fitz.open()
    
    for i in range(num_pages):
        page = doc.new_page()
        text_rect = fitz.Rect(50, 50, 550, 750)
        page.insert_text(
            text_rect.tl,
            f"{text_per_page} {i+1}",
            fontsize=12
        )
    
    doc.save(output_path)
    doc.close()


if __name__ == "__main__":
    unittest.main() 