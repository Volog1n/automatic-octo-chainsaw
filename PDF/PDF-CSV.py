import os
import tabula
import pandas as pd

def pdf_to_csv(pdf_path, csv_path):
    """Конвертирует PDF в CSV, используя tabula-py."""
    try:
        # Читаем все таблицы из PDF
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)

        # Если таблиц нет, или возникла ошибка.
        if not tables:
            print(f"В файле '{pdf_path}' не найдено табличных данных или произошла ошибка.")
            return False

        # Конкатенируем все таблицы в один DataFrame
        df = pd.concat(tables, ignore_index=True)

        # Сохраняем DataFrame в CSV
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"Файл '{pdf_path}' успешно конвертирован в '{csv_path}'")
        return True
    except Exception as e:
        print(f"Ошибка при конвертации файла '{pdf_path}': {e}")
        return False

def main():
    """Основная функция скрипта."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_files = [f for f in os.listdir(current_dir) if f.endswith('.pdf')]

    if not pdf_files:
        print("В текущей папке не найдено PDF файлов.")
        return

    print("Доступные PDF файлы:")
    for i, file in enumerate(pdf_files):
        print(f"{i + 1}. {file}")

    while True:
        choice = input("Введите номер файла для конвертации или его название (без .pdf): ")
        try:
            # если пользователь ввел число
            file_index = int(choice) - 1
            if 0 <= file_index < len(pdf_files):
                selected_pdf = pdf_files[file_index]
                break
            else:
                print("Неверный номер файла.")
        except ValueError:
            # если пользователь ввел название
            selected_pdf = choice + ".pdf"
            if selected_pdf in pdf_files:
                break
            else:
                print("Файл с таким именем не найден.")

    pdf_path = os.path.join(current_dir, selected_pdf)

    folder_name = input("Введите название папки для сохранения CSV файла: ")
    output_folder = os.path.join(current_dir, folder_name)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    csv_filename = os.path.splitext(selected_pdf)[0] + ".csv"
    csv_path = os.path.join(output_folder, csv_filename)

    pdf_to_csv(pdf_path, csv_path)

if __name__ == "__main__":
    main()
