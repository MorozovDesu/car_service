from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from config import Config

def connect_db():
    """Создает соединение с базой данных PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
        return conn
    except Exception as e:
        print("Ошибка подключения к базе данных:", e)
        return None

# Функции для работы с клиентами
def get_client_by_phone(phone_number):
    """Получает данные клиента по номеру телефона."""
    conn = connect_db()
    if conn is None:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "ID клиента", "ФИО", "Email", "Дата рождения", "Номер телефона", "Пароль"
                FROM public."Клиент"
                WHERE "Номер телефона" = %s;
                ''',
                (phone_number,)
            )
            row = cur.fetchone()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        row = None
    finally:
        conn.close()

    if row:
        return {
            "ID клиента": row[0],
            "ФИО": row[1],
            "Email": row[2],
            "Дата рождения": row[3].isoformat() if row[3] else None,
            "Номер телефона": row[4],
            "Пароль": row[5]
        }
    return None

def get_worker_by_email(email):
    """Получает данные работника по email."""
    conn = connect_db()
    if conn is None:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "ID работника", "ФИО", "Должность", "Пароль", "Email"
                FROM public."Работник"
                WHERE "Email" = %s;
                ''',
                (email,)
            )
            row = cur.fetchone()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        row = None
    finally:
        conn.close()

    if row:
        return {
            "ID работника": row[0],
            "ФИО": row[1],
            "Должность": row[2],
            "Пароль": row[3],
            "Email": row[4]
        }
    return None

def get_clients_paginated(page, per_page):
    """Получает список клиентов с пагинацией."""
    conn = connect_db()
    if conn is None:
        return []

    offset = (page - 1) * per_page
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "ID клиента", "ФИО", "Email", "Дата рождения", "Номер телефона"
                FROM public."Клиент"
                ORDER BY "ID клиента"
                LIMIT %s OFFSET %s;
                ''',
                (per_page, offset)
            )
            rows = cur.fetchall()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        rows = []
    finally:
        conn.close()

    return [
        {
            "ID клиента": row[0],
            "ФИО": row[1],
            "Email": row[2],
            "Дата рождения": row[3].isoformat() if row[3] else None,
            "Номер телефона": row[4]
        }
        for row in rows
    ]

def search_client(query):
    """Ищет клиента по ID или ФИО."""
    conn = connect_db()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            if query.isdigit():
                cur.execute(
                    '''
                    SELECT "ID клиента", "ФИО", "Email", "Дата рождения", "Номер телефона"
                    FROM public."Клиент"
                    WHERE "ID клиента" = %s;
                    ''',
                    (int(query),)
                )
            else:
                cur.execute(
                    '''
                    SELECT "ID клиента", "ФИО", "Email", "Дата рождения", "Номер телефона"
                    FROM public."Клиент"
                    WHERE "ФИО" ILIKE %s;
                    ''',
                    (f'%{query}%',)
                )
            rows = cur.fetchall()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        rows = []
    finally:
        conn.close()

    return [
        {
            "ID клиента": row[0],
            "ФИО": row[1],
            "Email": row[2],
            "Дата рождения": row[3].isoformat() if row[3] else None,
            "Номер телефона": row[4]
        }
        for row in rows
    ]

# Функции для работы с заявками
def get_applications_paginated(page, per_page):
    """Получает список заявок с пагинацией."""
    conn = connect_db()
    if conn is None:
        return []

    offset = (page - 1) * per_page
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "Номер заявки", "ID Клиента", "ID услуги", "ID выполняющего работы", "ID проверяющего", "Гарантия", "Дата"
                FROM public."Заявка"
                ORDER BY "Номер заявки"
                LIMIT %s OFFSET %s;
                ''',
                (per_page, offset)
            )
            rows = cur.fetchall()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        rows = []
    finally:
        conn.close()

    return [
        {
            "Номер заявки": row[0],
            "ID Клиента": row[1],
            "ID услуги": row[2],
            "ID выполняющего работы": row[3],
            "ID проверяющего": row[4],
            "Гарантия": row[5],
            "Дата": row[6].isoformat() if row[6] else None
        }
        for row in rows
    ]

def search_application(query):
    """Ищет заявку по номеру заявки или ID клиента."""
    conn = connect_db()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "Номер заявки", "ID Клиента", "ID услуги", "ID выполняющего работы", "ID проверяющего", "Гарантия", "Дата"
                FROM public."Заявка"
                WHERE "Номер заявки" = %s OR "ID Клиента" = %s;
                ''',
                (query, query)
            )
            rows = cur.fetchall()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        rows = []
    finally:
        conn.close()

    return [
        {
            "Номер заявки": row[0],
            "ID Клиента": row[1],
            "ID услуги": row[2],
            "ID выполняющего работы": row[3],
            "ID проверяющего": row[4],
            "Гарантия": row[5],
            "Дата": row[6].isoformat() if row[6] else None
        }
        for row in rows
    ]

def get_applications_for_client(client_id, page, per_page):
    """Получает список заявок клиента с названиями услуг."""
    conn = connect_db()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            offset = (page - 1) * per_page
            cur.execute('''
                SELECT z."Номер заявки", u."Тип услуги", z."Гарантия", z."Дата"
                FROM public."Заявка" z
                JOIN public."Услуга" u ON z."ID услуги" = u."ID услуги"
                WHERE z."ID Клиента" = %s
                ORDER BY z."Дата" DESC
                LIMIT %s OFFSET %s;
            ''', (client_id, per_page, offset))
            applications = cur.fetchall()

            # Преобразуем список к формату словаря для удобства работы в шаблоне
            return [
                {
                    "Номер заявки": app[0],
                    "Тип услуги": app[1],
                    "Гарантия": app[2],
                    "Дата": app[3]
                }
                for app in applications
            ]
    except Exception as e:
        print("Ошибка при получении заявок:", e)
        return []
    finally:
        conn.close()

    
def delete_application(application_number):
    """Удаляет заявку и все связанные записи в таблице 'Заказ'."""
    conn = connect_db()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            # Удаляем все связанные записи в таблице "Заказ"
            cur.execute(
                '''
                DELETE FROM public."Заказ"
                WHERE "Номер заявки" = %s;
                ''',
                (application_number,)
            )

            # Теперь удаляем саму заявку
            cur.execute(
                '''
                DELETE FROM public."Заявка"
                WHERE "Номер заявки" = %s;
                ''',
                (application_number,)
            )
            conn.commit()
            return True
    except Exception as e:
        print("Ошибка при удалении заявки:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

def get_cars_by_client_id(client_id):
    """Получает список автомобилей клиента по его ID."""
    conn = connect_db()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "Номер автомобиля", "Название", "Марка", "Модель"
                FROM public."Карточка автомобиля"
                WHERE "ID клиента" = %s;
                ''',
                (client_id,)
            )
            rows = cur.fetchall()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        rows = []
    finally:
        conn.close()

    return [
        {
            "Номер автомобиля": row[0],
            "Название": row[1],
            "Марка": row[2],
            "Модель": row[3]
        }
        for row in rows
    ]

def get_cars_by_client_id(client_id):
    """Получает список автомобилей клиента по его ID."""
    conn = connect_db()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "Номер автомобиля", "Название", "Марка", "Модель"
                FROM public."Карточка автомобиля"
                WHERE "ID клиента" = %s;
                ''',
                (client_id,)
            )
            rows = cur.fetchall()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        rows = []
    finally:
        conn.close()

    return [
        {
            "Номер автомобиля": row[0],
            "Название": row[1],
            "Марка": row[2],
            "Модель": row[3]
        }
        for row in rows
    ]


