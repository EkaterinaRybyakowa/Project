from nicegui import ui
import psycopg2

import json

# Параметры подключения к базе данных
DB_HOST = "localhost"
DB_NAME = "project"
DB_USER = "postgres"
DB_PASS = "1234"

# Функция для подключения к базе данных
def connect_to_db():
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        return conn
    except psycopg2.Error as e:
        ui.notify(f"Ошибка подключения к базе данных: {e}", type="negative")
        return None

# 1. Страница добавления горшка
@ui.page('/add_plant')
def add_plant_page():
    ui.label("Добавить горшок").classes('text-h4') # Добавим заголовок
    with ui.card().classes('q-pa-md'): # Обернем форму в карточку
        client_id = ui.number(label="ID клиента", value=1, format='%.0f').props('min=1').classes('w-full') # Растянем поле на всю ширину
        experiment_id = ui.number(label="ID эксперимента", value=1, format='%.0f').props('min=1').classes('w-full')
        pos = ui.number(label="Позиция", value=0.0).classes('w-full')

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
                    if cur:
                        cur.close()
                    conn.close()

        ui.button("Добавить горшок", on_click=add_plant, icon='add').classes('w-full bg-green-500 text-white') # Добавим иконку и цвет
        ui.link('Вернуться на главную', target='/').classes('text-grey-700')

# 2. Страница добавления эксперимента
@ui.page('/add_experiment')
def add_experiment_page():
    ui.label("Добавить эксперимент").classes('text-h4')
    with ui.card().classes('q-pa-md'):
        name = ui.input(label="Название эксперимента").classes('w-full')
        description = ui.textarea(label="Описание эксперимента").classes('w-full')
        parameter = ui.textarea(label="Параметры (JSON)", placeholder="Введите данные JSON здесь").classes('w-full')

        def add_experiment():
            conn = connect_to_db()
            if conn:
                try:
                    # Проверка JSON перед вставкой
                    try:
                        json.loads(parameter.value)  # Попытка разобрать JSON
                    except json.JSONDecodeError as e:
                        ui.notify(f"Неверный формат JSON: {e}", type="negative")
                        return

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
                    if cur:
                        cur.close()
                    conn.close()

        ui.button("Добавить эксперимент", on_click=add_experiment, icon='science').classes('w-full bg-blue-500 text-white')
        ui.link('Вернуться на главную', target='/').classes('text-grey-700')

# 3. Страница назначения эксперимента
@ui.page('/assign_experiment')
def assign_experiment_page():
    ui.label("Назначить эксперимент").classes('text-h4')
    with ui.card().classes('q-pa-md'):
        experiment_id = ui.number(label="ID эксперимента", value=1, format='%.0f').props('min=1').classes('w-full')
        plant_id = ui.number(label="ID горшка", value=1, format='%.0f').props('min=1').classes('w-full')

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
                    if cur:
                        cur.close()
                    conn.close()

        ui.button("Назначить эксперимент", on_click=assign, icon='assignment').classes('w-full bg-orange-500 text-white')
        ui.link('Вернуться на главную', target='/').classes('text-grey-700')

# 4. Страница просмотра данных
@ui.page('/view_data')
def view_data_page():
    ui.label("Просмотр данных").classes('text-h4')
    with ui.card().classes('q-pa-md'):
        plant_id = ui.number(label="ID горшка", value=1, format='%.0f').props('min=1').classes('w-full')

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
                            {'name': 'date', 'label': 'Дата', 'field': 'date', 'sortable': True, 'format': '%Y-%m-%d %H:%M:%S'},
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
                    if cur:
                        cur.close()
                    conn.close()

        ui.button("Показать данные", on_click=show_data, icon='table_chart').classes('w-full bg-purple-500 text-white')
        ui.link('Вернуться на главную', target='/').classes('text-grey-700')

# Главная страница
@ui.page('/')
def index():
    ui.label("Управление экспериментами с растениями").classes('text-h3')
    with ui.row().classes('q-gutter-md'): # Добавим отступы между ссылками
        ui.link("Добавить горшок", target="/add_plant").classes('text-blue-500')
        ui.link("Добавить эксперимент", target="/add_experiment").classes('text-blue-500')
        ui.link("Назначить эксперимент", target="/assign_experiment").classes('text-blue-500')
        ui.link("Просмотреть данные", target="/view_data").classes('text-blue-500')

ui.run(title="Управление экспериментами с растениями")