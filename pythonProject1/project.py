from nicegui import ui
import psycopg2  # Для работы с PostgreSQL
import json

from nicegui.html import data

with open("plant_list.json", "w") as write_file:
    json.dump(data, write_file)

# Параметры подключения к базе данных
DB_HOST = "5432"
DB_NAME = "project"  # Замените на имя вашей базы данных
DB_USER = "postgres"
DB_PASS = "1234"  # Замените на ваш пароль

# Функция для подключения к базе данных
def connect_to_db():
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        return conn
    except psycopg2.Error as e:
        ui.notify(f"Ошибка подключения к базе данных: {e}", type="negative")
        return None

# 1. Добавление горшков
@ui.page('/add_plant')
def add_plant_page():
    ui.label("Добавление горшка")

    client_id = ui.number(label="ID клиента", value=1, format='%.0f').props('min=1')
    experiment_id = ui.number(label="ID эксперимента", value=1, format='%.0f').props('min=1')
    pos = ui.number(label="Позиция", value=0.0)

    def add_plant():
        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO public.plant (experiment_id, pos, client_id) VALUES (%s, %s, %s)",
                    (experiment_id.value, pos.value, client_id.value),
                )
                conn.commit()
                ui.notify("Горшок успешно добавлен!", type="positive")
            except psycopg2.Error as e:
                ui.notify(f"Ошибка добавления горшка: {e}", type="negative")
            finally:
                cur.close()
                conn.close()

    ui.button("Добавить горшок", on_click=add_plant)
    ui.link('Вернуться на главную', target='/')


# 2. Добавление экспериментов
@ui.page('/add_experiment')
def add_experiment_page():
    ui.label("Добавление эксперимента")

    name = ui.input(label="Название эксперимента")
    description = ui.textarea(label="Описание эксперимента")
    parameter = ui.textarea(label="Параметры (JSON)")  # Пока просто текстовое поле

    def add_experiment():
        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO public.experiment (name, description, parameter) VALUES (%s, %s, %s)",
                    (name.value, description.value, parameter.value),
                )
                conn.commit()
                ui.notify("Эксперимент успешно добавлен!", type="positive")
            except psycopg2.Error as e:
                ui.notify(f"Ошибка добавления эксперимента: {e}", type="negative")
            finally:
                cur.close()
                conn.close()

    ui.button("Добавить эксперимент", on_click=add_experiment)
    ui.link('Вернуться на главную', target='/')


# 3. Распределение экспериментов
@ui.page('/assign_experiment')
def assign_experiment_page():
    ui.label("Распределение экспериментов")

    experiment_id = ui.number(label="ID эксперимента", value=1, format='%.0f').props('min=1')
    plant_id = ui.number(label="ID горшка", value=1, format='%.0f').props('min=1')

    def assign():
        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE public.plant SET experiment_id = %s WHERE id = %s",
                    (experiment_id.value, plant_id.value),
                )
                conn.commit()
                ui.notify("Эксперимент успешно назначен!", type="positive")
            except psycopg2.Error as e:
                ui.notify(f"Ошибка назначения эксперимента: {e}", type="negative")
            finally:
                cur.close()
                conn.close()

    ui.button("Назначить эксперимент", on_click=assign)
    ui.link('Вернуться на главную', target='/')


# 4. Просмотр данных
@ui.page('/view_data')
def view_data_page():
    ui.label("Просмотр данных")

    plant_id = ui.number(label="ID горшка", value=1, format='%.0f').props('min=1')

    def show_data():
        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT date, temperature_ground, humidity_ground, illuminance FROM public.plant_data WHERE plant_id = %s",
                    (plant_id.value,),
                )
                data = cur.fetchall()

                if data:
                    columns = [
                        {'name': 'date', 'label': 'Дата', 'field': 'date', 'sortable': True},
                        {'name': 'temperature_ground', 'label': 'Температура почвы', 'field': 'temperature_ground', 'sortable': True},
                        {'name': 'humidity_ground', 'label': 'Влажность почвы', 'field': 'humidity_ground', 'sortable': True},
                        {'name': 'illuminance', 'label': 'Освещенность', 'field': 'illuminance', 'sortable': True},
                    ]
                    rows = [{'date': row[0], 'temperature_ground': row[1], 'humidity_ground': row[2], 'illuminance': row[3]} for row in data]
                    ui.table(columns=columns, rows=rows)
                else:
                    ui.notify("Нет данных для этого горшка.", type="warning")

            except psycopg2.Error as e:
                ui.notify(f"Ошибка получения данных: {e}", type="negative")
            finally:
                cur.close()
                conn.close()

    ui.button("Показать данные", on_click=show_data)
    ui.link('Вернуться на главную', target='/')


# Главная страница
@ui.page('/')
def index():
    ui.label("Главная страница")
    ui.link("Добавить горшок", target="/add_plant")
    ui.link("Добавить эксперимент", target="/add_experiment")
    ui.link("Распределить эксперимент", target="/assign_experiment")
    ui.link("Просмотреть данные", target="/view_data")


ui.run(title="Управление экспериментами с растениями")
