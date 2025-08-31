import logging
from time import time, sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import csv
from pathlib import Path


def open_page(browser, url, locator):
    # print(f"Открываем страницу по адресу {url}")
    count = 1
    while True:
        try:
            browser.set_page_load_timeout(40)
            browser.get(url)
            # Страница может не успеть загрузиться и browser посчитает что мест нет
            # чтобы этого не произошло будем проверять что загрузился locator
            try:
                WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located(locator)
                )
            except:
                # Если присутствует этот элемент div class="row error-page__error-text"
                # то 404 и переходим к следующему пункту
                if browser.find_elements(
                    By.CSS_SELECTOR, 'div[class="row error-page__error-text"]'
                ):
                    # print("Получена ошибка 404")
                    logging.info(f"Получена ошибка 404 на {url}")
                    break
                else:
                    # print("Страница не успела загрузиться, снова загрузим ее")
                    continue

            # print("Получили страницу")
            break
        except Exception as e:
            count += 1
            # print(e)
            # print(f"Не удалось загрузить страницу по адресу: {url}\nпопытка №{count} открыть страницу через 5 секунд")
            logging.info("Не загрузили страницу, новая попытка")
            logging.info(e)
            sleep(5)
            continue
    return browser


def write_csv(parent_dir, tickets):
    path_table = parent_dir / "tickets.csv"
    path_table = path_table.resolve()
    with open(path_table, "w", newline="") as file_csv:
        writer = csv.writer(file_csv, delimiter=";")
        writer.writerow(["Мероприятие", "Дата", "Сектор", "Ряд", "Место", "Цена"])
        for element in tickets:
            writer.writerow(
                [
                    element["name"],
                    element["date"],
                    element["sector"],
                    f"ряд {element['row']}",
                    f"место {element['seat']}",
                    f"цена {element['price']} рублей",
                ]
            )


def parsing_selenium():
    """ "
    Парсинг сайта ticketland.ru с помощью библиотеки Selenium
    Возвращает список tickets с нужными данными
    """
    options = Options()
    # options.add_argument("--headless") # без запуска браузера
    # чтобы не обнаружили что браузер управляется webdriver
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("log-level=3")  # в Windows отключает сообщения о ошибках ssl
    options.add_argument("--start-maximized")

    browser = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=options
    )

    locator = (By.CSS_SELECTOR, 'a[class="card__title pb-1 pt-1"]')

    open_page(
        browser, "https://www.ticketland.ru/cirki/bolshoy-moskovskiy-cirk/", locator
    )

    # Теперь получим список ссылок на страницы мероприятий
    # a class="card__title pb-1 pt-1"
    list_a = browser.find_elements(By.CSS_SELECTOR, 'a[class="card__title pb-1 pt-1"]')
    event_urls = [teg_a.get_attribute("href") for teg_a in list_a]
    # Переходим по ссылке из списка событий event_urls:
    tickets = []
    for url in event_urls[:1]:
        locator = (By.CSS_SELECTOR, 'div[class="show-card__col show-card__col--end"]')
        open_page(browser, url, locator)
        # Перешли на страницу мероприятия, теперь получим список ссылок на даты, когда это мероприятие проходит
        # div class="show-card__col show-card__col--end"
        date_list = browser.find_elements(
            By.CSS_SELECTOR, 'div[class="show-card__col show-card__col--end"]'
        )
        url_list = []
        for teg_div in date_list:
            teg_a = teg_div.find_elements(By.TAG_NAME, "a")
            if not teg_a:
                continue
            else:
                teg_a_href = teg_a[0].get_attribute("href")
                url_list.append(teg_a_href)

        # print("Количество дат, когда пройдет это событие=", len(url_list))
        # Получили список ссылок на даты мероприятий, теперь будем последовательно эти ссылки открывать
        for url in url_list[:1]:
            locator = (By.CSS_SELECTOR, 'g[class="places"]')
            open_page(browser, url, locator)

            # Открыли мероприятие на конкретную дату, теперь будем считывать места
            # Название мероприятия h1 class="mts-compact text-medium lh-28"
            name = browser.find_element(
                By.CSS_SELECTOR, 'h1[class="mts-compact text-medium lh-28"]'
            ).text[:-2]
            # Дата div class="text-medium mr-2"
            event_date = browser.find_element(
                By.CSS_SELECTOR, 'div[class="text-medium mr-2"]'
            ).text
            # Места в теге rect
            # Наличие билета и его стоимость определяется атрибутом тега rect data-price
            places = browser.find_elements(By.TAG_NAME, "rect")
            count = 0
            for place in places:
                if place.get_attribute("data-price"):
                    count += 1
                    # Запишем данные этого места в список tickets
                    sector = place.get_attribute("data-section-name")
                    row = place.get_attribute("row")
                    seat = place.get_attribute("seat")
                    price = place.get_attribute("data-price")
                    tickets.append(
                        {
                            "name": name,
                            "date": event_date,
                            "sector": sector,
                            "row": row,
                            "seat": seat,
                            "price": price,
                        }
                    )
                    # print(f"Номер билета={count}, sector = {sector}, ряд = {row}, место = {seat}, цена = {price}")
    browser.quit()
    return tickets


def main():
    start_time = time()

    parent_dir = Path(__file__).parent
    path_log = parent_dir / "log.log"
    path_log = path_log.resolve()
    logging.basicConfig(
        filename=path_log,
        format="%(asctime)s -- %(levelname)s -- %(message)s",
        level=logging.INFO,
    )
    logging.info(
        f"___________________________Запуск программы_________________________________________"
    )

    tickets = parsing_selenium()

    write_csv(parent_dir, tickets)
    # print("Всего строк с местами =", len(tickets))

    end_time = time()
    hours = int(round(end_time - start_time, 0)) // 3600
    minutes = (int(round(end_time - start_time, 0)) % 3600) // 60

    # print(f"Время, потраченное на выполнение программы: {hours} часов и {minutes} минут")
    logging.info(
        f"Время, потраченное на выполнение программы: {hours} часов и {minutes} минут"
    )


main()
