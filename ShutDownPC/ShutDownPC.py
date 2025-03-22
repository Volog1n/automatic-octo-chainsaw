import tkinter as tk
from tkinter import messagebox
import threading
import time
import schedule
from PIL import Image, ImageTk
import subprocess

shutdown_timer = None
scheduled_job = None
timer_minutes_remaining = 0
scheduled_shutdown_enabled = True
root = None
scheduled_time = ""
scheduler_thread = None
app_running = True


def shutdown_system():
    """Выключает компьютер."""
    try:
        subprocess.Popen("shutdown /s /t 1", creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"Ошибка при выключении: {e}")


def update_indicator():
    """Обновляет индикатор (кружок и текст)."""
    global shutdown_timer, scheduled_job, timer_minutes_remaining, scheduled_shutdown_enabled
    if shutdown_timer and shutdown_timer.is_alive():
        indicator_label.config(image=green_indicator)
        timer_minutes_remaining = int((shutdown_timer_end_time - time.time()) / 60)
        if timer_minutes_remaining > 0:
            indicator_text.set(f"Таймер: {timer_minutes_remaining} мин")
        else:
            indicator_text.set("Выключение...")
    elif scheduled_job and scheduled_shutdown_enabled:
        indicator_label.config(image=green_indicator)
        indicator_text.set(f"Расписание: {scheduled_time}")
    else:
        indicator_label.config(image=red_indicator)
        indicator_text.set("Не активно")
    if root and app_running:
        root.after(60000, update_indicator)


def start_timer_shutdown(minutes):
    """Запускает таймер на выключение."""
    global shutdown_timer, shutdown_timer_end_time
    seconds = minutes * 60
    shutdown_timer_end_time = time.time() + seconds

    def timer_shutdown_task():
        time.sleep(seconds)
        if shutdown_timer and shutdown_timer.is_alive() and app_running:
            shutdown_system()

    # Если таймер запущен, то останавливаем поток
    if shutdown_timer and shutdown_timer.is_alive():
        shutdown_timer.join(timeout=1)
        shutdown_timer = None

    shutdown_timer = threading.Thread(target=timer_shutdown_task)
    shutdown_timer.daemon = True
    shutdown_timer.start()
    messagebox.showinfo("Таймер установлен", f"Компьютер будет выключен через {minutes} минут.")
    update_indicator()


def schedule_shutdown(time_str):
    """Устанавливает расписание выключения."""
    global scheduled_job, scheduled_time, scheduled_shutdown_enabled
    scheduled_time = time_str
    scheduled_shutdown_enabled = True

    def scheduled_shutdown_task():
        if scheduled_shutdown_enabled and app_running:
            shutdown_system()

    # Удаляем старое расписание.
    if scheduled_job:
        schedule.cancel_job(scheduled_job)

    scheduled_job = schedule.every().day.at(time_str).do(scheduled_shutdown_task)

    messagebox.showinfo("Расписание установлено", f"Компьютер будет выключен каждый день в {time_str}.")
    update_indicator()


def cancel_shutdown():
    """Отменяет таймер или расписание."""
    global shutdown_timer, scheduled_job, scheduled_shutdown_enabled
    cancelled = False

    # Отменяем таймер, если он активен
    if shutdown_timer and shutdown_timer.is_alive():
        try:
            subprocess.Popen("shutdown /a", creationflags=subprocess.CREATE_NO_WINDOW)
            print("Команда shutdown /a выполнена успешно.")
        except Exception as e:
            print(f"Ошибка при отмене выключения: {e}")
        shutdown_timer.join(timeout=1)
        shutdown_timer = None
        cancelled = True

    # Отменяем расписание, если оно установлено
    if scheduled_job:
        schedule.cancel_job(scheduled_job)
        scheduled_shutdown_enabled = False
        scheduled_job = None
        cancelled = True

    if cancelled:
        messagebox.showinfo("Выключение отменено", "Выключение компьютера отменено.")
    else:
        messagebox.showinfo("Нет активных таймеров/расписаний", "Нет активных таймеров или расписаний выключения.")
    update_indicator()


def show_timer_dialog():
    """Показывает диалоговое окно для установки таймера."""

    def set_timer():
        try:
            minutes = int(timer_entry.get())
            start_timer_shutdown(minutes)
            timer_dialog.destroy()
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите целое число минут.")

    timer_dialog = tk.Toplevel(root)
    timer_dialog.title("Укажите время до выключения (в минутах)")

    timer_label = tk.Label(timer_dialog, text="Минут:")
    timer_label.pack(padx=10, pady=5)

    timer_entry = tk.Entry(timer_dialog)
    timer_entry.pack(padx=10, pady=5)

    set_timer_button = tk.Button(timer_dialog, text="Установить таймер", command=set_timer)
    set_timer_button.pack(padx=10, pady=5)


def show_schedule_dialog():
    """Показывает диалоговое окно для установки расписания."""

    def set_schedule():
        time_str = schedule_entry.get()
        try:
            time.strptime(time_str, '%H:%M')
            schedule_shutdown(time_str)
            schedule_dialog.destroy()
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите время в формате HH:MM (например, 22:30).")

    schedule_dialog = tk.Toplevel(root)
    schedule_dialog.title("Укажите время выключения (HH:MM)")

    schedule_label = tk.Label(schedule_dialog, text="Время (HH:MM):")
    schedule_label.pack(padx=10, pady=5)

    schedule_entry = tk.Entry(schedule_dialog)
    schedule_entry.pack(padx=10, pady=5)

    set_schedule_button = tk.Button(schedule_dialog, text="Установить расписание", command=set_schedule)
    set_schedule_button.pack(padx=10, pady=5)
    schedule_dialog.protocol("WM_DELETE_WINDOW", schedule_dialog.destroy)


def run_scheduler():
    """Запускает планировщик."""
    global app_running
    while app_running:
        schedule.run_pending()
        time.sleep(1)


def on_closing():
    """Обработчик закрытия главного окна."""
    global shutdown_timer, scheduled_job, scheduler_thread, app_running
    app_running = False

    # Сначала очищаем планировщик
    schedule.clear()

    # Отменяем и завершаем таймер, если он активен
    if shutdown_timer and shutdown_timer.is_alive():
        try:
            subprocess.Popen("shutdown /a", creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print(f"Ошибка при отмене выключения: {e}")
        shutdown_timer.join(timeout=1)

    # Завершаем поток планировщика, если он запущен
    if scheduler_thread and scheduler_thread.is_alive():
        scheduler_thread.join(timeout=1)

    # Закрываем окно
    root.destroy()
    root.quit()


# Main
root = tk.Tk()
root.title("Управление выключением")

# Load images
try:
    red_image = Image.open("red_circle.png").resize((20, 20))
    green_image = Image.open("green_circle.png").resize((20, 20))
    red_indicator = ImageTk.PhotoImage(red_image)
    green_indicator = ImageTk.PhotoImage(green_image)
except FileNotFoundError:
    messagebox.showerror(
        "Ошибка",
        "Не найдены изображения индикаторов (red_circle.png, green_circle.png). Пожалуйста, поместите их в ту же папку, что и скрипт.",
    )
    exit()

# Indicator label
indicator_label = tk.Label(root, image=red_indicator)
indicator_label.pack(pady=5)

# Indicator text
indicator_text = tk.StringVar()
indicator_text.set("Не активно")
indicator_text_label = tk.Label(root, textvariable=indicator_text)
indicator_text_label.pack(pady=5)

# Buttons
set_timer_button = tk.Button(root, text="Установить таймер выключения", command=show_timer_dialog)
set_timer_button.pack(pady=10)

set_schedule_button = tk.Button(root, text="Установить расписание выключения", command=show_schedule_dialog)
set_schedule_button.pack(pady=10)

cancel_button = tk.Button(root, text="Отменить выключение", command=cancel_shutdown)
cancel_button.pack(pady=10)

# Запуск планировщика в отдельном потоке
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

# Initial indicator update
update_indicator()

# Обработчик закрытия окна
root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()