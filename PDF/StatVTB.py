import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import os
import csv
import re
import matplotlib.colors as mcolors
from colorama import Fore, Back, Style, init

# Инициализация colorama для цветного вывода в консоль
init(autoreset=True)


def pdf_to_csv(pdf_path, csv_path):
    """
    Функция для извлечения данных из PDF-файла и сохранения их в CSV-файл.

    Args:
        pdf_path (str): Путь к PDF-файлу с банковской выпиской
        csv_path (str): Путь для сохранения CSV-файла с данными

    Returns:
        tuple: (total_info, transactions) - словарь с итоговой информацией и список транзакций
    """
    transactions = []
    skipped_lines = []  # Список для хранения пропущенных строк
    total_info = {
        'initial_balance': 0.0,  # Начальный баланс
        'total_income': 0.0,  # Общая сумма пополнений
        'total_expense': 0.0,  # Общая сумма списаний
        'final_balance': 0.0  # Конечный баланс
    }

    # Открываем PDF-файл
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        # Извлекаем текст из всех страниц
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            full_text += text + "\n"

            # Обрабатываем каждую строку на странице
            lines = text.split('\n')
            for i in range(len(lines) - 1):
                line = lines[i].strip()
                next_line = lines[i + 1].strip()

                # Ищем строки транзакций с помощью регулярного выражения
                transaction_match = re.match(
                    r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+(\d{6})\s+(.+?)\s+([+-]?[\d ,]+,\d+)\s+([\d ,]+,\d+)$",
                    line
                )
                if transaction_match:
                    # Извлекаем информацию о транзакции
                    date = transaction_match.group(1)
                    time = transaction_match.group(2)
                    category = transaction_match.group(4)
                    amount_str = transaction_match.group(5).replace(' ', '').replace(',', '.')
                    balance_str = transaction_match.group(6).replace(' ', '').replace(',', '.')

                    # Определяем сумму с учетом знака
                    amount = float(amount_str[1:]) if amount_str.startswith('+') else -float(amount_str)

                    try:
                        balance = float(balance_str)
                    except ValueError:
                        balance = 0.0

                    # Описание транзакции находится в следующей строке
                    description = next_line
                    transactions.append([f"{date} {time}", category, description, amount, balance])
                else:
                     skipped_lines.append(line)

        # Извлечение блока итогов
        summary_block_match = re.search(r"START DATE\s+(\d{2}\.\d{2}\.\d{4})\s+TOTAL INCOME\s+([\d.]+)\s+TOTAL EXPENSES\s+([\d.]+)\s+END DATE\s+(\d{2}\.\d{2}\.\d{4})", full_text, re.DOTALL)

        if summary_block_match:
            start_date = summary_block_match.group(1)
            total_income = float(summary_block_match.group(2))
            total_expense = float(summary_block_match.group(3))
            end_date = summary_block_match.group(4)

            print(f"Totals block: START DATE {start_date} TOTAL INCOME {total_income} TOTAL EXPENSES {total_expense} END DATE {end_date}")
            
            total_info['total_income'] = total_income
            total_info['total_expense'] = total_expense
            # В этих выписках нет информации по начальному и конечному балансу.
            # total_info['initial_balance'] = ...
            # total_info['final_balance'] = ...
        else:
            print("Totals block not found in the document.")
           

            print("Unable to determine total income.")
            print("Unable to determine total expense.")


    # Сохраняем данные в CSV-файл
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Записываем общую информацию
        writer.writerow(["Общая информация"])
        writer.writerow(["Остаток на 01.01.2025", total_info['initial_balance']])
        writer.writerow(["Всего пополнений", total_info['total_income']])
        writer.writerow(["Всего списаний", total_info['total_expense']])
        writer.writerow(["Остаток на 08.03.2025", total_info['final_balance']])
        writer.writerow([])
        # Записываем заголовки столбцов и транзакции
        writer.writerow(["Дата", "Категория", "Описание", "Сумма", "Остаток"])
        writer.writerows(transactions)

    # Выводим количество найденных транзакций
    num_transactions = len(transactions)
    print(f"\nNumber of transaction lines found in PDF: {num_transactions}")

    if skipped_lines:
        print("\nSkipped Malformed Lines:")
        for line in skipped_lines:
            print(line)

    return total_info, transactions


def analyze_csv(csv_path):
    """
    Функция для анализа данных из CSV-файла с транзакциями.

    Args:
        csv_path (str): Путь к CSV-файлу с данными
    """
    try:
        # Читаем транзакции, пропуская шапку с общей информацией
        df = pd.read_csv(csv_path, skiprows=6, encoding='utf-8')
        df['Дата'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y %H:%M', errors='coerce')

        # Удаляем строки с некорректной датой
        df = df.dropna(subset=['Дата'])
        
        # Разделяем на расходы и доходы
        expenses = df[df['Сумма'] < 0].copy()
        incomes = df[df['Сумма'] > 0].copy()

        # Рассчитываем фактические суммы
        calculated_income = incomes['Сумма'].sum()
        calculated_expense = expenses['Сумма'].sum()

        # Читаем общую информацию из начала CSV-файла
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            total_info = {}
            for i, row in enumerate(reader):
                if i == 1:
                    total_info['initial_balance'] = float(row[1]) if row[1] else 0.0
                elif i == 2:
                    total_info['total_income'] = float(row[1]) if row[1] else 0.0
                elif i == 3:
                    total_info['total_expense'] = float(row[1]) if row[1] else 0.0
                elif i == 4:
                    total_info['final_balance'] = float(row[1]) if row[1] else 0.0
                elif i > 4:
                    break

        calculated_final_balance = total_info['initial_balance'] + calculated_income + calculated_expense

        # Выводим общую статистику
        print(Fore.CYAN + "\nGeneral Statistics:")
        print(f"{Fore.WHITE}Starting Balance: {total_info['initial_balance']:.2f} RUB")
        print(f"Total Income: {total_info['total_income']:.2f} RUB")
        print(f"Total Expenses: {abs(total_info['total_expense']):.2f} RUB")
        print(f"Ending Balance: {calculated_final_balance:.2f} RUB\n")

        # Анализируем расходы по категориям
        expense_by_category = expenses.groupby('Категория')['Сумма'].sum().abs().sort_values(ascending=False)

        print(Fore.CYAN + "Expense Statistics by Category:")
        if not expense_by_category.empty:
            total_expenses_cat = expense_by_category.sum()
            for category, amount in expense_by_category.items():
                count = len(expenses[expenses['Категория'] == category])
                percentage = amount / total_expenses_cat * 100
                if percentage > 20:
                    print(
                        f"{Fore.GREEN}{category}:{Fore.WHITE} -{amount:.2f} RUB ({count} operations, {Back.YELLOW + Fore.BLACK}{percentage:.1f}%{Style.RESET_ALL})")
                else:
                    print(f"{Fore.GREEN}{category}:{Fore.WHITE} -{amount:.2f} RUB ({count} operations, {percentage:.1f}%)")
        else:
            print("No expense data found.")
        print()

        # Анализируем расходы по месяцам
        expenses['Месяц'] = expenses['Дата'].dt.strftime('%m.%Y')
        expense_by_month = expenses.groupby('Месяц')['Сумма'].sum().abs().sort_values(ascending=False)

        print(Fore.CYAN + "Expense Statistics by Month:")
        if not expense_by_month.empty:
            total_expenses_month = expense_by_month.sum()
            for month, amount in expense_by_month.items():
                count = len(expenses[expenses['Месяц'] == month])
                percentage = amount / total_expenses_month * 100
                if percentage > 20:
                    print(
                        f"{Fore.GREEN}{month}:{Fore.WHITE} -{amount:.2f} RUB ({count} operations, {Back.YELLOW + Fore.BLACK}{percentage:.1f}%{Style.RESET_ALL})")
                else:
                    print(f"{Fore.GREEN}{month}:{Fore.WHITE} -{amount:.2f} RUB ({count} operations, {percentage:.1f}%)")
        else:
            print("No expense data found.")

        # Создаем график расходов по категориям
        if not expense_by_category.empty:
            # Генерируем пастельные цвета для графика
            colors = generate_pastel_colors(len(expense_by_category))

            plt.figure(figsize=(10, 6))
            bars = expense_by_category.plot(kind='bar', color=colors, title='Expenses by Category')
            plt.ylabel('Amount (RUB)')
            plt.xlabel('Category')
            plt.xticks(rotation=45)

            # Подсвечиваем максимальное значение красным цветом
            max_amount = expense_by_category.max()
            max_category = expense_by_category.idxmax()
            for bar in bars.patches:
                if bar.get_height() == max_amount:
                    bar.set_color('red')

            plt.tight_layout()
            plt.savefig(os.path.join(os.path.dirname(csv_path), 'expense_by_category.png'))
            print("\nExpense by category graph saved as 'expense_by_category.png'")

        # Создаем график расходов по месяцам
        if not expense_by_month.empty:
            plt.figure(figsize=(10, 6))
            bars = expense_by_month.plot(kind='bar', color=generate_pastel_colors(len(expense_by_month)),
                                         title='Expenses by Month')
            plt.ylabel('Amount (RUB)')
            plt.xlabel('Month')
            plt.xticks(rotation=45)

            # Подсвечиваем максимальное значение красным цветом
            max_amount = expense_by_month.max()
            max_month = expense_by_month.idxmax()
            for bar in bars.patches:
                if bar.get_height() == max_amount:
                    bar.set_color('red')

            plt.tight_layout()
            plt.savefig(os.path.join(os.path.dirname(csv_path), 'expense_by_month.png'))
            print("Expense by month graph saved as 'expense_by_month.png'")

    except FileNotFoundError:
        print(f"Error: File {csv_path} not found.")
    except pd.errors.EmptyDataError:
        print(f"Error: File {csv_path} is empty or contains no data.")
    except pd.errors.ParserError:
        print(f"Error: Could not parse file {csv_path}.")
    except KeyError as e:
        print(f"Error: Column {e} is missing in the data.")
    except ValueError as e:
        print(f"Error: Invalid data format: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



def generate_pastel_colors(n):
    """
    Генерирует список из n пастельных цветов для графиков.

    Args:
        n (int): Количество цветов для генерации

    Returns:
        list: Список hex-кодов цветов
    """
    pastel_colors = []
    for i in range(n):
        hue = i / n  # Равномерно распределяем оттенки
        saturation = 0.5  # Уменьшаем насыщенность для пастельности
        value = 0.9  # Увеличиваем яркость для пастельности
        rgb_color = mcolors.hsv_to_rgb((hue, saturation, value))
        hex_color = mcolors.to_hex(rgb_color)
        pastel_colors.append(hex_color)
    return pastel_colors


if __name__ == "__main__":
    # Находим PDF-файл в текущей директории
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.pdf')]

    # Проверяем, что нашли ровно один PDF-файл
    if not pdf_files:
        print("Error: No PDF files found in the current folder!")
    else:
        for i, file_name in enumerate(pdf_files):
            print(f"{i + 1}. {file_name}")
        while True:
            choice = input(
                "Enter the file number to analyze, its name (without .pdf) or 'q' to quit: ").lower()
            if choice == 'q':
                break
            try:
                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(pdf_files):
                        selected_file = pdf_files[index]
                        break
                    else:
                        print("Invalid file number. Please select a file number from the list")
                elif choice + '.pdf' in pdf_files:
                    selected_file = choice + '.pdf'
                    break
                else:
                    print("File not found. Please enter a number or file name from the list")
            except ValueError:
                print('Invalid input.Please enter a number or "q" to exit')

        # Задаем пути к файлам
        pdf_path = os.path.join(current_dir, selected_file)
        output_dir = os.path.join(current_dir, 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        csv_path = os.path.join(output_dir, 'transactions.csv')

        # Конвертируем PDF в CSV
        print(f"Converting {pdf_path} to {csv_path}...")
        total_info, transactions = pdf_to_csv(pdf_path, csv_path)
        print(f"Conversion completed. File created: {csv_path}\n")

        # Анализируем данные
        print("Analyzing data from CSV...")
        analyze_csv(csv_path)

