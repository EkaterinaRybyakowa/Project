import psycopg2
from db import *

# Проверка наличия переменных окружения
if not all([DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT, DB_ADMIN]):
    print("Не все переменные окружения для базы данных заданы!")
    exit()


# Функция для создания базы данных
def create_database():
    conn = None
    cur = None
    try:
        # Подключение к базе данных postgres (системной базе данных)
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database='postgres', user=DB_ADMIN, password=DB_PASS)
        conn.autocommit = True

        cur = conn.cursor()

        # Проверка, существует ли база данных
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'")
        exists = cur.fetchone()

        if not exists:
            # Создание базы данных
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"База данных '{DB_NAME}' успешно создана.")
        else:
            print(f"База данных '{DB_NAME}' уже существует.")

    except psycopg2.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# Функция для подключения к базе данных (теперь возвращает соединение)
def connect_to_db():
    try:
        # Подключение к созданной базе данных
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)
        return conn
    except psycopg2.Error as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None


# Функция для создания таблиц, если они не существуют
def create_tables():
    conn = None
    cur = None
    try:
        conn = connect_to_db()
        if conn is None:
            print("Не удалось подключиться к базе данных.")
            return

        cur = conn.cursor()

        # SQL-запросы для создания таблиц
        create_table_queries = [
            """
            CREATE TABLE IF NOT EXISTS public.client (
                client_id smallint NOT NULL,
                rack_num smallint NOT NULL,
                row_num smallint NOT NULL, 

                CONSTRAINT client_pk PRIMARY KEY (client_id),
                CONSTRAINT client_unique UNIQUE (rack_num, row_num)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS public.experiment(
                id integer NOT NULL,
                parameter json NOT NULL,
                name character varying NOT NULL,
                description text,

                CONSTRAINT experiment_pk PRIMARY KEY (id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS public.packages (
                client_id smallint NOT NULL,
                package integer NOT NULL,
                temperature_air numeric NOT NULL,
                humidity_air numeric NOT NULL,
                "time" timestamp without time zone NOT NULL,

                CONSTRAINT packages_pk PRIMARY KEY (client_id, package)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS public.plant (
                id bigint NOT NULL,
                experiment_id integer NOT NULL,
                pos numeric NOT NULL,
                client_id smallint NOT NULL,

                CONSTRAINT plant_pk PRIMARY KEY (id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS public.plant_data (
                plant_id bigint NOT NULL,
                date timestamp without time zone NOT NULL,
                path_to_photo character varying,
                temperature_ground numeric,
                package_id integer NOT NULL,
                humidity_ground numeric,
                illuminance integer,
                client_id smallint NOT NULL,

                CONSTRAINT plant_data_pk PRIMARY KEY (client_id, package_id, plant_id)
            );
            """,

            """
            CREATE SEQUENCE IF NOT EXISTS public.experiment_id_seq
                AS integer
                START WITH 1
                INCREMENT BY 1
                NO MINVALUE
                NO MAXVALUE
                CACHE 1;
            """,
            """
            CREATE SEQUENCE IF NOT EXISTS  public.plant_id_seq
                START WITH 1
                INCREMENT BY 1
                NO MINVALUE
                NO MAXVALUE
                CACHE 1;
            """,

            """
            ALTER SEQUENCE IF EXISTS public.experiment_id_seq OWNED BY public.experiment.id;
            """,
            """
            ALTER TABLE ONLY public.experiment ALTER COLUMN id SET DEFAULT nextval('public.experiment_id_seq'::regclass);
            """,
            """
            ALTER SEQUENCE IF EXISTS public.plant_id_seq OWNED BY public.plant.id;
            """,
            """
            ALTER TABLE ONLY public.plant ALTER COLUMN id SET DEFAULT nextval('public.plant_id_seq'::regclass);
            """,

            """
            ALTER TABLE public.client OWNER TO postgres;
            """,
            """
            ALTER TABLE public.experiment OWNER TO postgres;
            """,
            """
            ALTER TABLE public.packages OWNER TO postgres;
            """,
            """
            ALTER TABLE public.plant OWNER TO postgres;
            """,
            """
            ALTER TABLE public.plant_data OWNER TO postgres;
            """
        ]

        # Выполнение запросов для создания таблиц
        for query in create_table_queries:
            cur.execute(query)

        # Добавление внешних ключей (с проверкой существования)
        add_constraint_queries = [
            (
                "packages_client_fk",
                """
                ALTER TABLE ONLY public.packages
                ADD CONSTRAINT packages_client_fk FOREIGN KEY (client_id) REFERENCES public.client(client_id);
                """,
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'packages_client_fk'
                AND conrelid = 'packages'::regclass;
                """
            ),
            (
                "plant_client_fk",
                """
                ALTER TABLE ONLY public.plant
                ADD CONSTRAINT plant_client_fk FOREIGN KEY (client_id) REFERENCES public.client(client_id);
                """,
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'plant_client_fk'
                AND conrelid = 'plant'::regclass;
                """
            ),
            (
                "plant_data_packages_fk",
                """
                ALTER TABLE ONLY public.plant_data
                ADD CONSTRAINT plant_data_packages_fk FOREIGN KEY (client_id, package_id) REFERENCES public.packages(client_id, package);
                """,
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'plant_data_packages_fk'
                AND conrelid = 'plant_data'::regclass;
                """
            ),
            (
                "plant_data_plant_fk",
                """
                ALTER TABLE ONLY public.plant_data
                ADD CONSTRAINT plant_data_plant_fk FOREIGN KEY (plant_id) REFERENCES public.plant(id);
                """,
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'plant_data_plant_fk'
                AND conrelid = 'plant_data'::regclass;
                """
            ),
            (
                "plant_experiment_fk",
                """
                ALTER TABLE ONLY public.plant
                ADD CONSTRAINT plant_experiment_fk FOREIGN KEY (experiment_id) REFERENCES public.experiment(id);
                """,
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'plant_experiment_fk'
                AND conrelid = 'plant'::regclass;
                """
            )

        ]

        # Добавление внешних ключей с проверкой существования
        for constraint_name, add_constraint_query, check_constraint_query in add_constraint_queries:
            cur.execute(check_constraint_query)
            exists = cur.fetchone()
            if not exists:
                cur.execute(add_constraint_query)
                print(f"Ограничение '{constraint_name}' успешно добавлено.")
            else:
                print(f"Ограничение '{constraint_name}' уже существует.")

        conn.commit()
        print("Таблицы базы данных созданы (если они еще не существовали).")

    except psycopg2.Error as e:
        print(f"Ошибка при создании таблиц: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()