import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import calendar
import os

class WorkScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("График работы")
        self.schedule = {}
        self.hourly_rate = tk.DoubleVar(value=500.0)  # Ставка по умолчанию 500 руб/час
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        self.buttons = {}  # Для хранения кнопок дней

        # Цвета для типов смен
        self.colors = {
            "Дневная смена": "#66BB6A",      # Более мягкий зеленый
            "Ночная смена": "#8D6E63",       # Приглушенный коричневый
            "Выходной": "#B0BEC5",           # Мягкий серый
            "Больничный": "#EF5350",         # Приглушенный красный
            "Отгул за свой счёт": "#EF5350"  # Приглушенный красный
        }

        # Загрузка сохраненного графика
        self.load_schedule()

        # Привязка сохранения при закрытии окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Основной интерфейс
        self.create_widgets()

    def create_widgets(self):
        # Устанавливаем стиль для современного дизайна
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 12), padding=5)
        style.configure("TLabel", font=("Segoe UI", 12))
        style.configure("TEntry", font=("Segoe UI", 12))

        # Панель с доходами и количеством смен
        self.stats_frame = tk.Frame(self.root, bg="#F5F5F5")
        self.stats_frame.pack(pady=10, padx=10, fill=tk.X)

        # Карточка для дохода за месяц
        monthly_card = tk.Frame(self.stats_frame, bg="#F5F5F5")
        monthly_card.pack(side=tk.LEFT, padx=(5, 25))
        monthly_canvas = tk.Canvas(monthly_card, width=250, height=40, bg="#F5F5F5", highlightthickness=0)  # Увеличиваем ширину до 250
        monthly_canvas.pack()
        # Рисуем закругленный прямоугольник с тенью
        monthly_canvas.create_rectangle(5, 5, 245, 35, fill="#E0E0E0", outline="#E0E0E0")  # Тень
        monthly_canvas.create_rectangle(0, 0, 240, 30, fill="#E0F7FA", outline="#E0F7FA", width=2, tags="rounded")  # Основной фон
        # Текст поверх Canvas
        self.monthly_income_label = tk.Label(monthly_card, text="Доход за месяц: 0 руб", 
                                             font=("Segoe UI", 12, "bold"), bg="#E0F7FA", fg="#006064")
        self.monthly_income_label.place(x=10, y=5)

        # Карточка для количества смен
        shifts_card = tk.Frame(self.stats_frame, bg="#F5F5F5")
        shifts_card.pack(side=tk.LEFT, padx=5)
        shifts_canvas = tk.Canvas(shifts_card, width=100, height=40, bg="#F5F5F5", highlightthickness=0)
        shifts_canvas.pack()
        # Рисуем закругленный прямоугольник с тенью
        shifts_canvas.create_rectangle(5, 5, 95, 35, fill="#E0E0E0", outline="#E0E0E0")  # Тень
        shifts_canvas.create_rectangle(0, 0, 90, 30, fill="#FFF3E0", outline="#FFF3E0", width=2, tags="rounded")  # Основной фон
        # Текст поверх Canvas
        self.shifts_label = tk.Label(shifts_card, text="Смены: 0", 
                                     font=("Segoe UI", 12, "bold"), bg="#FFF3E0", fg="#EF6C00")
        self.shifts_label.place(x=10, y=5)

        # Панель с переключением месяцев
        nav_frame = tk.Frame(self.root, bg="#F5F5F5")
        nav_frame.pack(pady=10, fill=tk.X)
        tk.Button(nav_frame, text="←", font=("Segoe UI", 12, "bold"), width=3, command=self.prev_month, 
                  bg="#E0E0E0", relief="flat", activebackground="#B0BEC5").pack(side=tk.LEFT, padx=10)
        self.month_label = tk.Label(nav_frame, text=self.get_month_name(), font=("Segoe UI", 14, "bold"), bg="#F5F5F5")
        self.month_label.pack(side=tk.LEFT)
        tk.Button(nav_frame, text="→", font=("Segoe UI", 12, "bold"), width=3, command=self.next_month, 
                  bg="#E0E0E0", relief="flat", activebackground="#B0BEC5").pack(side=tk.LEFT, padx=10)

        # Календарь
        self.cal_frame = tk.Frame(self.root, bg="#FFFFFF")
        self.cal_frame.pack(pady=10)
        self.update_calendar()

        # Поле для ставки
        rate_frame = tk.Frame(self.root, bg="#F5F5F5")
        rate_frame.pack(pady=5)
        tk.Label(rate_frame, text="Ставка за час (руб):", font=("Segoe UI", 12), bg="#F5F5F5").pack(side=tk.LEFT)
        tk.Entry(rate_frame, textvariable=self.hourly_rate, width=10, font=("Segoe UI", 12)).pack(side=tk.LEFT, padx=5)

        # Фильтры
        filter_frame = tk.Frame(self.root, bg="#F5F5F5")
        filter_frame.pack(pady=5)
        tk.Label(filter_frame, text="Фильтр:", font=("Segoe UI", 12), bg="#F5F5F5").pack(side=tk.LEFT)
        tk.Button(filter_frame, text="День", command=lambda: self.show_schedule("day"), 
                  font=("Segoe UI", 12), bg="#E0E0E0", relief="flat", activebackground="#B0BEC5").pack(side=tk.LEFT, padx=2)
        tk.Button(filter_frame, text="Неделя", command=lambda: self.show_schedule("week"), 
                  font=("Segoe UI", 12), bg="#E0E0E0", relief="flat", activebackground="#B0BEC5").pack(side=tk.LEFT, padx=2)
        tk.Button(filter_frame, text="Месяц", command=lambda: self.show_schedule("month"), 
                  font=("Segoe UI", 12), bg="#E0E0E0", relief="flat", activebackground="#B0BEC5").pack(side=tk.LEFT, padx=2)

        # Поле для вывода графика
        self.output = tk.Text(self.root, height=10, width=50, font=("Segoe UI", 12), bg="#FAFAFA", relief="flat")
        self.output.pack(pady=10, padx=10)

        # Кнопка сохранения
        tk.Button(self.root, text="Сохранить", command=self.save_schedule, 
                  font=("Segoe UI", 12, "bold"), bg="#42A5F5", fg="white", relief="flat", 
                  activebackground="#2196F3").pack(pady=5)

        # Начальный вывод графика и статистики
        self.show_schedule("month")
        self.update_stats()

    def get_month_name(self):
        months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        return f"{months[self.current_month - 1]} {self.current_year}"

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar()
        self.update_stats()

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar()
        self.update_stats()

    def update_calendar(self):
        # Очищаем старый календарь
        for widget in self.cal_frame.winfo_children():
            widget.destroy()
        self.buttons.clear()

        # Названия дней недели
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i, day in enumerate(days):
            tk.Label(self.cal_frame, text=day, width=5, font=("Segoe UI", 12, "bold"), bg="#FFFFFF").grid(row=0, column=i)

        # Дни месяца
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        today = datetime.now()
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day != 0:
                    btn = tk.Button(self.cal_frame, text=str(day), width=5, font=("Segoe UI", 12),
                                   command=lambda d=day: self.select_shift(d), relief="flat", 
                                   activebackground="#B0BEC5")
                    # Выделение текущей даты
                    if (day == today.day and self.current_month == today.month 
                        and self.current_year == today.year):
                        btn.config(relief="solid", borderwidth=2, bg="#42A5F5", fg="white")
                    # Окраска сохраненных смен
                    date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                    if date_str in self.schedule:
                        shift_type = self.schedule[date_str]["type"]
                        btn.config(bg=self.colors[shift_type])
                    else:
                        btn.config(bg="#E0E0E0")
                    btn.grid(row=week_num + 1, column=day_num, padx=2, pady=2)
                    self.buttons[day] = btn
        
        # Обновляем название месяца
        self.month_label.config(text=self.get_month_name())

    def select_shift(self, day):
        # Создаем всплывающее окно как дочернее основного
        popup = tk.Toplevel(self.root)
        popup.title(f"Выбор смены для {day:02d}.{self.current_month:02d}.{self.current_year}")
        popup.transient(self.root)  # Делаем окно "привязанным" к основному
        popup.grab_set()  # Фокус на всплывающем окне

        # Позиционируем окно рядом с основной программой
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        popup.geometry(f"200x200+{root_x + root_width + 10}+{root_y}")  # Справа от основного окна

        tk.Label(popup, text="Выберите тип смены:", font=("Segoe UI", 12)).pack(pady=5)

        # Список кнопок вместо Combobox
        shift_types = ["Дневная смена", "Ночная смена", "Выходной", "Больничный", "Отгул за свой счёт"]
        for shift in shift_types:
            tk.Button(popup, text=shift, width=20, font=("Segoe UI", 12), 
                      command=lambda s=shift: self.add_shift(day, s, popup), 
                      bg="#E0E0E0", relief="flat", activebackground="#B0BEC5").pack(pady=2)

        # Отключаем возможность изменения размера окна
        popup.resizable(False, False)

    def add_shift(self, day, shift_type, popup):
        date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
        hours = 11 if shift_type in ["Дневная смена", "Ночная смена"] else 0
        cost = hours * self.hourly_rate.get() if hours > 0 else 0
        self.schedule[date_str] = {"type": shift_type, "hours": hours, "cost": cost}
        
        # Обновляем цвет кнопки
        self.buttons[day].config(bg=self.colors[shift_type])
        
        # Автосохранение после изменения
        self.save_schedule(auto=True)
        
        popup.destroy()
        self.show_schedule("month")
        self.update_stats()

    def update_stats(self):
        # Рассчитываем доходы и количество смен
        total_cost_month = 0
        total_shifts = 0

        for date_str, info in self.schedule.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date.month == self.current_month and date.year == self.current_year:
                if info["hours"] > 0:
                    total_cost_month += info["cost"]
                    total_shifts += 1

        # Обновляем метки (доход как целое число)
        self.monthly_income_label.config(text=f"Доход за месяц: {int(total_cost_month)} руб")
        self.shifts_label.config(text=f"Смены: {total_shifts}")

    def show_schedule(self, filter_type):
        self.output.delete(1.0, tk.END)
        total_cost = 0
        today = datetime.now()

        # Заголовок таблицы
        self.output.insert(tk.END, "Дата        | Тип смены            | Часы | Сумма\n")
        self.output.insert(tk.END, "-" * 50 + "\n")

        for date_str, info in sorted(self.schedule.items()):
            date = datetime.strptime(date_str, "%Y-%m-%d")
            include = False
            if filter_type == "day" and date.date() == today.date():
                include = True
            elif filter_type == "week" and date.isocalendar()[1] == today.isocalendar()[1]:
                include = True
            elif filter_type == "month" and date.month == self.current_month and date.year == self.current_year:
                include = True

            if include:
                line = f"{date_str}: {info['type']:<20}"
                if info["hours"] > 0:
                    line += f" {info['hours']}ч   {info['cost']} руб"
                self.output.insert(tk.END, line + "\n")
                if info["hours"] > 0:
                    total_cost += info["cost"]

        # Итоговая сумма
        self.output.insert(tk.END, "\n" + "-" * 50 + "\n")
        self.output.insert(tk.END, f"Итого за период: {total_cost} руб\n")

    def save_schedule(self, auto=False):
        file_path = os.path.join(os.path.dirname(__file__), "schedule.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.schedule, f, ensure_ascii=False)
        if not auto:
            messagebox.showinfo("Успех", "График успешно сохранен!")

    def load_schedule(self):
        file_path = os.path.join(os.path.dirname(__file__), "schedule.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.schedule = json.load(f)
        except FileNotFoundError:
            self.schedule = {}

    def on_closing(self):
        # Сохраняем график перед закрытием
        self.save_schedule(auto=True)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WorkScheduleApp(root)
    root.mainloop()