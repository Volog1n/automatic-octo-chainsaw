#!python
# -*- coding: utf-8 -*-

import os
import time
import concurrent.futures
from typing import Dict, List, Tuple, Union, Optional, Any
from dataclasses import dataclass
import logging
from tqdm import tqdm

# PyMuPDF для быстрого извлечения текста
import fitz

# PDFMiner для более точного извлечения в сложных случаях
from pdfminer.high_level import extract_pages, extract_text as pdfminer_extract_text
from pdfminer.layout import LTTextContainer, LTPage, LTFigure, LTTextBox, LTTextLine

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pdf_parser')


@dataclass
class TextBlock:
    """Класс для хранения извлеченного текста с метаданными."""
    text: str
    page_num: int
    x0: float
    y0: float
    x1: float
    y1: float
    font: Optional[str] = None
    font_size: Optional[float] = None
    block_type: str = "text"  # тип блока (text, heading, etc.)


class PDFParser:
    """
    Быстрый и точный парсер PDF-файлов с поддержкой обработки больших документов.
    
    Использует комбинацию PyMuPDF (быстрый) и PDFMiner (более точный) для
    обеспечения оптимального баланса скорости и точности.
    """
    
    def __init__(self, use_multithreading: bool = True, max_workers: int = None):
        """
        Инициализация PDF парсера.
        
        Args:
            use_multithreading: Использовать многопоточную обработку для больших файлов
            max_workers: Максимальное количество потоков (None = автоматическое определение)
        """
        self.use_multithreading = use_multithreading
        self.max_workers = max_workers or min(32, os.cpu_count() + 4)
        logger.info(f"Инициализирован PDF Parser (многопоточность: {use_multithreading}, "
                    f"потоков: {self.max_workers})")
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Быстрое извлечение текста из PDF-файла.
        
        Args:
            pdf_path: Путь к PDF-файлу
            
        Returns:
            str: Извлеченный текст
        """
        try:
            start_time = time.time()
            logger.info(f"Начало извлечения текста из {pdf_path}")
            
            # Используем PyMuPDF (fitz) для быстрого извлечения
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            if total_pages > 100 and self.use_multithreading:
                # Для больших документов используем многопоточную обработку
                return self._extract_text_multithread(doc)
            else:
                # Для небольших документов - однопоточная обработка
                text = ""
                for page in tqdm(doc, total=total_pages, desc="Извлечение текста"):
                    text += page.get_text()
            
            doc.close()
            elapsed = time.time() - start_time
            logger.info(f"Извлечение завершено за {elapsed:.2f} секунд. "
                         f"Объем текста: {len(text)} символов")
            return text
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста: {str(e)}")
            raise
    
    def _extract_text_multithread(self, doc: fitz.Document) -> str:
        """
        Многопоточное извлечение текста для больших PDF-файлов.
        
        Args:
            doc: Открытый PDF-документ
            
        Returns:
            str: Извлеченный текст
        """
        total_pages = len(doc)
        logger.info(f"Запуск многопоточного извлечения для документа с {total_pages} страницами")
        results = [""] * total_pages
        
        def process_page(page_idx):
            page = doc[page_idx]
            return page_idx, page.get_text()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(process_page, i) for i in range(total_pages)]
            
            for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="Извлечение текста"
            ):
                page_idx, text = future.result()
                results[page_idx] = text
        
        return "".join(results)
    
    def extract_text_with_metadata(self, pdf_path: str, detailed: bool = False) -> List[TextBlock]:
        """
        Извлечение текста с сохранением метаданных (позиция, шрифт и др.)
        
        Args:
            pdf_path: Путь к PDF-файлу
            detailed: Использовать более детальное извлечение (медленнее, но точнее)
            
        Returns:
            List[TextBlock]: Список блоков текста с метаданными
        """
        logger.info(f"Начало извлечения текста с метаданными из {pdf_path}")
        start_time = time.time()
        
        if detailed:
            # Используем PDFMiner для более точного извлечения
            return self._extract_with_pdfminer(pdf_path)
        else:
            # Используем PyMuPDF (быстрее)
            return self._extract_with_pymupdf(pdf_path)
    
    def _extract_with_pymupdf(self, pdf_path: str) -> List[TextBlock]:
        """
        Извлечение текста с метаданными с помощью PyMuPDF.
        
        Args:
            pdf_path: Путь к PDF-файлу
            
        Returns:
            List[TextBlock]: Список блоков текста с метаданными
        """
        blocks = []
        doc = fitz.open(pdf_path)
        
        for page_idx, page in enumerate(tqdm(doc, desc="Извлечение блоков текста")):
            blocks_dict = page.get_text("dict")
            
            for block in blocks_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            blocks.append(TextBlock(
                                text=span["text"],
                                page_num=page_idx + 1,
                                x0=span["bbox"][0],
                                y0=span["bbox"][1],
                                x1=span["bbox"][2],
                                y1=span["bbox"][3],
                                font=span["font"],
                                font_size=span["size"],
                                block_type="text"
                            ))
        
        doc.close()
        logger.info(f"Извлечено {len(blocks)} текстовых блоков за "
                     f"{time.time() - start_time:.2f} секунд")
        return blocks
    
    def _extract_with_pdfminer(self, pdf_path: str) -> List[TextBlock]:
        """
        Извлечение текста с метаданными с помощью PDFMiner (более точное).
        
        Args:
            pdf_path: Путь к PDF-файлу
            
        Returns:
            List[TextBlock]: Список блоков текста с метаданными
        """
        blocks = []
        
        for page_layout in extract_pages(pdf_path):
            page_num = page_layout.pageid
            
            for element in page_layout:
                if isinstance(element, LTTextBox):
                    for text_line in element:
                        if isinstance(text_line, LTTextLine):
                            blocks.append(TextBlock(
                                text=text_line.get_text().strip(),
                                page_num=page_num,
                                x0=text_line.bbox[0],
                                y0=text_line.bbox[1],
                                x1=text_line.bbox[2],
                                y1=text_line.bbox[3],
                                block_type="text"
                            ))
        
        logger.info(f"Извлечено {len(blocks)} текстовых блоков с PDFMiner за "
                     f"{time.time() - start_time:.2f} секунд")
        return blocks
    
    def batch_process(self, pdf_files: List[str]) -> Dict[str, str]:
        """
        Пакетная обработка нескольких PDF-файлов.
        
        Args:
            pdf_files: Список путей к PDF-файлам
            
        Returns:
            Dict[str, str]: Словарь {путь_к_файлу: извлеченный_текст}
        """
        logger.info(f"Начало пакетной обработки {len(pdf_files)} файлов")
        start_time = time.time()
        
        results = {}
        
        if self.use_multithreading and len(pdf_files) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(pdf_files), self.max_workers)) as executor:
                future_to_file = {
                    executor.submit(self.extract_text, file): file for file in pdf_files
                }
                
                for future in tqdm(
                    concurrent.futures.as_completed(future_to_file),
                    total=len(pdf_files),
                    desc="Обработка файлов"
                ):
                    file = future_to_file[future]
                    try:
                        results[file] = future.result()
                    except Exception as e:
                        logger.error(f"Ошибка при обработке {file}: {str(e)}")
                        results[file] = f"ОШИБКА: {str(e)}"
        else:
            for file in tqdm(pdf_files, desc="Обработка файлов"):
                try:
                    results[file] = self.extract_text(file)
                except Exception as e:
                    logger.error(f"Ошибка при обработке {file}: {str(e)}")
                    results[file] = f"ОШИБКА: {str(e)}"
        
        logger.info(f"Пакетная обработка завершена за {time.time() - start_time:.2f} секунд")
        return results
    
    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """
        Извлечение таблиц из PDF-файла (экспериментальная функция).
        
        Args:
            pdf_path: Путь к PDF-файлу
            
        Returns:
            List[Dict]: Список таблиц с метаданными
        """
        logger.warning("Функция извлечения таблиц находится в экспериментальном состоянии")
        # Реализация извлечения таблиц может быть добавлена в будущем
        # Это сложнее, чем простое извлечение текста, и требует дополнительной логики
        return [] 