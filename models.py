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

def add_client(fio, email, dob, phone, password):
    """Добавляет клиента с хешированным паролем."""
    conn = connect_db()
    if conn is None:
        return False

    hashed_password = generate_password_hash(password)

    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO public."Клиент" ("ФИО", "Email", "Дата рождения", "Номер телефона", "Пароль")
                VALUES (%s, %s, %s, %s, %s);
                ''',
                (fio, email, dob, phone, hashed_password)
            )
            conn.commit()
            return True
    except Exception as e:
        print("Ошибка при добавлении клиента:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

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
    """Получает заявки клиента с учетом пагинации."""
    conn = connect_db()
    if conn is None:
        return []

    offset = (page - 1) * per_page

    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT "Номер заявки", "ID Клиента", "ID услуги", "ID выполняющего работы", "ID проверяющего", "Гарантия", "Дата" '
            'FROM public."Заявка" '
            'WHERE "ID Клиента" = %s '
            'ORDER BY "Номер заявки" '
            'LIMIT %s OFFSET %s;',
            (client_id, per_page, offset)
        )
        rows = cur.fetchall()
        cur.close()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        rows = []
    finally:
        conn.close()

    applications = [
        {
            "Номер заявки": row[0],
            "ID Клиента": row[1],
            "ID услуги": row[2],
            "ID выполняющего работы": row[3],
            "ID проверяющего": row[4],
            "Гарантия": row[5],
            "Дата": row[6].isoformat() if row[6] else None,
        }
        for row in rows
    ]
    return applications
