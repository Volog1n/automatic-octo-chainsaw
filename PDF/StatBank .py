import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import os
import csv
import re
import matplotlib.colors as mcolors
from colorama import Fore, Back, Style, init

# Инициализация colorama
init(autoreset=True)

def pdf_to_csv(pdf_path, csv_path):
    """
    Извлекает данные из PDF-файла и сохраняет их в CSV-файл.

    Параметры:
    - pdf_path: путь к PDF-файлу с выпиской
    - csv_path: путь для сохранения CSV-файла

    Возвращает:
    - total_info: словарь с общей информацией (начальный остаток, сумма пополнений, сумма списаний, конечный остаток)
    - transactions: список транзакций
    """
    transactions = []
    total_info = {
        'initial_balance': 0.0,
        'total_income': 0.0,
        'total_expense': 0.0,
        'final_balance': 0.0
    }

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            full_text += text + "\n"

            lines = text.split('\n')
            for i in range(len(lines) - 1):
                line = lines[i].strip()
                next_line = lines[i + 1].strip()

                transaction_match = re.match(
                    r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+(\d{6})\s+(.+?)\s+([+-]?[\d ,]+,\d+)\s+([\d ,]+,\d+)$",
                    line
                )
                if transaction_match:
                    date = transaction_match.group(1)
                    time = transaction_match.group(2)
                    category = transaction_match.group(4)
                    amount_str = transaction_match.group(5).replace(' ', '').replace(',', '.')
                    balance_str = transaction_match.group(6).replace(' ', '').replace(',', '.')
                    #добавлена проверка на знак
                    amount = float(amount_str[1:]) if amount_str.startswith('+') else -float(amount_str)

                    try:
                        balance = float(balance_str)
                    except ValueError:
                        balance = 0.0

                    description = next_line
                    transactions.append([f"{date} {time}", category, description, amount, balance])

        # Извлечение блока итогов
        summary_block_match = re.search(r"ОСТАТОК НА 01\.01\.2025.*?ОСТАТОК НА 08\.03\.2025", full_text, re.DOTALL)
        if summary_block_match:
            summary_text = summary_block_match.group(0)
            print("Блок итогов:", summary_text)
            
            # Extract numbers from the lines after the summary header
            # Изменено что бы правильно захватывались числа.
            summary_lines = full_text.split(summary_text)[1].strip()
            
            numbers_str = re.split(r'\s{2,}',summary_lines)
            numbers = []
            for item in numbers_str:
               numbers.append(item)
           
            
            if len(numbers) >= 4:
                total_info['initial_balance'] = float(numbers[0].replace(' ', '').replace(',', '.'))
                total_info['total_income'] = float(numbers[1].replace(' ', '').replace(',', '.'))
                total_info['total_expense'] = float(numbers[2].replace(' ', '').replace(',', '.'))
                total_info['final_balance'] = float(numbers[3].replace(' ', '').replace(',', '.'))
            else:
                print("Недостаточно данных для вычисления итоговых значений.")
        else:
            print("Блок итогов не найден в документе.")

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Общая информация"])
        writer.writerow(["Остаток на 01.01.2025", total_info['initial_balance']])
        writer.writerow(["Всего пополнений", total_info['total_income']])
        writer.writerow(["Всего списаний", total_info['total_expense']])
        writer.writerow(["Остаток на 08.03.2025", total_info['final_balance']])
        writer.writerow([])
        writer.writerow(["Дата", "Категория", "Описание", "Сумма", "Остаток"])
        writer.writerows(transactions)
    
    # Добавлено: подсчет количества строк транзакций
    num_transactions = len(transactions)
    print(f"\nКоличество строк с транзакциями, найденных в PDF: {num_transactions}")
    return total_info, transactions

def analyze_csv(csv_path):
    """
    Анализирует данные из CSV-файла и создает графики.

    Параметры:
    - csv_path: путь к CSV-файлу с данными
    """
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        total_info = {}
        for i, row in enumerate(reader):
            if i == 1:
                total_info['initial_balance'] = float(row[1])
            elif i == 2:
                total_info['total_income'] = float(row[1])
            elif i == 3:
                total_info['total_expense'] = float(row[1])
            elif i == 4:
                total_info['final_balance'] = float(row[1])
            elif i > 4:
                break

    df = pd.read_csv(csv_path, skiprows=6, encoding='utf-8')
    df['Дата'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y %H:%M')
    expenses = df[df['Сумма'] < 0].copy()
    incomes = df[df['Сумма'] > 0].copy()
    
    calculated_income = incomes['Сумма'].sum()
    calculated_expense = expenses['Сумма'].sum()
    calculated_final_balance = total_info['initial_balance'] + calculated_income + calculated_expense

    print(Fore.CYAN + "Общая статистика:")
    print(f"{Fore.WHITE}Остаток на начало периода: {total_info['initial_balance']:.2f} руб.")
    print(f"Всего пополнений: {calculated_income:.2f} руб.")
    print(f"Всего списаний: {abs(calculated_expense):.2f} руб.")
    print(f"Остаток на конец периода: {calculated_final_balance:.2f} руб.\n")

    expense_by_category = expenses.groupby('Категория')['Сумма'].sum().abs()
    print(Fore.CYAN + "Статистика трат по категориям:")
    if not expense_by_category.empty:
        total_expenses = expense_by_category.sum()
        for category, amount in expense_by_category.items():
            count = len(expenses[expenses['Категория'] == category])
            percentage = amount / total_expenses * 100
            if percentage > 20 :
                print(f"{Fore.GREEN}{category}:{Fore.WHITE} -{amount:.2f} руб. ({count} операций, {Back.YELLOW + Fore.BLACK}{percentage:.1f}%{Style.RESET_ALL})")
            else:
                print(f"{Fore.GREEN}{category}:{Fore.WHITE} -{amount:.2f} руб. ({count} операций, {percentage:.1f}%)")

    else:
        print("Нет данных о расходах.")
    print()

    expenses['Месяц'] = expenses['Дата'].dt.strftime('%m.%Y')
    expense_by_month = expenses.groupby('Месяц')['Сумма'].sum().abs()
    print(Fore.CYAN + "Статистика трат по месяцам:")
    if not expense_by_month.empty:
        total_expenses = expense_by_month.sum()
        for month, amount in expense_by_month.items():
            count = len(expenses[expenses['Месяц'] == month])
            percentage = amount / total_expenses * 100
            if percentage > 20 :
                print(f"{Fore.GREEN}{month}:{Fore.WHITE} -{amount:.2f} руб. ({count} операций, {Back.YELLOW + Fore.BLACK}{percentage:.1f}%{Style.RESET_ALL})")
            else:
                print(f"{Fore.GREEN}{month}:{Fore.WHITE} -{amount:.2f} руб. ({count} операций, {percentage:.1f}%)")
    else:
        print("Нет данных о расходах.")

    if not expense_by_category.empty:
        #Генерация цвета
        colors = generate_pastel_colors(len(expense_by_category))

        plt.figure(figsize=(10, 6))
        bars = expense_by_category.plot(kind='bar', color=colors, title='Расходы по категориям')
        plt.ylabel('Сумма (руб.)')
        plt.xlabel('Категория')
        plt.xticks(rotation=45)

        # Подсветка максимального значения
        max_amount = expense_by_category.max()
        max_category = expense_by_category.idxmax()
        for bar in bars.patches:
            if bar.get_height() == max_amount:
                bar.set_color('red')

        plt.tight_layout()
        plt.savefig(os.path.join(os.path.dirname(csv_path), 'expense_by_category.png'))
        print("\nГрафик трат по категориям сохранён как 'expense_by_category.png'")

    if not expense_by_month.empty:
        plt.figure(figsize=(10, 6))
        bars = expense_by_month.plot(kind='bar', color = generate_pastel_colors(len(expense_by_month)), title='Расходы по месяцам')
        plt.ylabel('Сумма (руб.)')
        plt.xlabel('Месяц')
        plt.xticks(rotation=45)
        # Подсветка максимального значения
        max_amount = expense_by_month.max()
        max_month = expense_by_month.idxmax()
        for bar in bars.patches:
          if bar.get_height() == max_amount:
              bar.set_color('red')

        plt.tight_layout()
        plt.savefig(os.path.join(os.path.dirname(csv_path), 'expense_by_month.png'))
        print("График трат по месяцам сохранён как 'expense_by_month.png'")
def generate_pastel_colors(n):
  """
  Генерирует список из n пастельных цветов.

  Параметры:
  - n: количество цветов

  Возвращает:
  - список hex-кодов цветов
  """
  pastel_colors = []
  for i in range(n):
    hue = i / n  # Равномерно распределяем оттенки
    saturation = 0.5 # Уменьшаем насыщенность
    value = 0.9 # Увеличиваем яркость
    rgb_color = mcolors.hsv_to_rgb((hue, saturation, value))
    hex_color = mcolors.to_hex(rgb_color)
    pastel_colors.append(hex_color)
  return pastel_colors

if __name__ == "__main__":
    current_dir = os.getcwd()
    pdf_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print("Ошибка: В текущей папке нет PDF-файлов!")
    elif len(pdf_files) > 1:
        print("Ошибка: В папке найдено несколько PDF-файлов. Укажите один конкретный файл.")
        print("Найденные файлы:", pdf_files)
    else:
        pdf_path = os.path.join(current_dir, pdf_files[0])
        output_dir = os.path.join(current_dir, 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        csv_path = os.path.join(output_dir, 'transactions.csv')
        
        print(f"Конвертация {pdf_path} в {csv_path}...")
        total_info, transactions = pdf_to_csv(pdf_path, csv_path)
        print(f"Конвертация завершена. Создан файл: {csv_path}\n")
        
        print("Анализ данных из CSV...")
        analyze_csv(csv_path)
