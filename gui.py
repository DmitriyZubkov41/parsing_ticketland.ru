from tkinter import *
from crontab import CronTab
import time
from pathlib import Path

"""
Данный модуль служит для запуска графического интерфейса программы. Позволяет выбрать 
время запуска программы, интервал для повторного запуска. Работает только в ubuntu. Для 
   windows не работает.
"""


def check_cron(h, m):
    if h >= 0 and h <= 23 and m >= 0 and m <= 59:
        return True
    else:
        return False


def write_crontab(date_launch, interval_launch):
    """
    Записываем в файл crontab расписание и команду с комментарием "ticketland.ru"
    """
    h = int(date_launch.split(":")[0])
    m = int(date_launch.split(":")[1])

    if not check_cron(h, m):
        lbl1_date.configure(text="Неправильное значение времени")
        lbl1_interval.configure(text="")
        return

    my_cron = CronTab(user=True)
    for job in my_cron:
        if job.comment == "ticketland.ru":
            my_cron.remove(job)

    parent_dir = Path(__file__).parent
    path_main = parent_dir / "main.py"
    path_main = path_main.resolve()

    # job = my_cron.new(command=f'DISPLAY=:0 python3 {path_main} > /dev/pts/0', comment='ticketland.ru')
    job = my_cron.new(
        command=f"DISPLAY=:0 python3 {path_main} > /dev/null 2>&1",
        comment="ticketland.ru",
    )
    job.setall(f"{m} {h} * * *")

    # job1 = my_cron.new(command=f'DISPLAY=:0 python3 {path_main} > /dev/pts/0', comment='ticketland.ru')
    job1 = my_cron.new(
        command=f"DISPLAY=:0 python3 {path_main} > /dev/null 2>&1",
        comment="ticketland.ru",
    )
    if int(interval_launch) == 1:
        job1.minute.every(59)
    else:
        job1.hour.every(int(interval_launch))

    my_cron.write()

    lbl1_date.configure(text=date_launch)
    lbl1_interval.configure(text=interval_launch)


def read_crontab():
    """
    Прочитаем из crontab время
    """
    my_cron = CronTab(user=True)
    count_job = 1
    h = ""
    m = ""
    interval = ""
    for job in my_cron:
        if job.comment == "ticketland.ru" and count_job == 1:
            count_job = count_job + 1
            l = str(job).split()
            h = int(l[1])
            m = int(l[0])
        elif job.comment == "ticketland.ru" and count_job == 2:
            l = str(job).split()
            if l[0] == "*":
                interval = l[1][2:]
            else:
                interval = "через 59 минут"

    return (h, m, interval)


def launch():
    import main

    window.destroy()
    main.main()


tuple_date = read_crontab()
hour_minutes = f"{tuple_date[0]}:{tuple_date[1]}"
interval = tuple_date[2]

window = Tk()
window.title("Поиск билетов с ticketland.ru")
window.geometry("500x250")

# Время запуска программы:
lbl_date = Label(window, text="Время запуска времени")
lbl_date.grid(column=0, row=0)
# Поле для ввода времени запуска программы
field_date = Entry(window, width=10)
field_date.insert(END, hour_minutes)
field_date.focus()
field_date.grid(column=1, row=0)
# Значение времени запуска программы
lbl1_date = Label(window, text=hour_minutes)
lbl1_date.grid(column=2, row=0)

# Интервал между первым и повторным запусками программы
lbl_interval = Label(window, text="Интервал между запусками")
lbl_interval.grid(column=0, row=1)
# Поле для ввода
field_interval = Entry(window, width=10)
field_interval.insert(END, interval)
field_interval.grid(column=1, row=1)
# Значение интервала
lbl1_interval = Label(window, text=interval)
lbl1_interval.grid(column=2, row=1)

# Кнопка для сохранения параметров запуска
btn = Button(
    window,
    text="Изменить",
    command=lambda: write_crontab(field_date.get(), field_interval.get()),
)
btn.grid(column=2, row=2)

# Кнопка для немедленного запуска программы
btn1 = Button(window, text="Старт", command=launch)
btn1.grid(column=3, row=0)

window.mainloop()
