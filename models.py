# models.py

import psycopg2
from config import Config

# models.py

import psycopg2
from config import Config

def connect_db():
    """Создаем соединение с базой данных PostgreSQL."""
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

def get_clients_paginated(page, per_page):
    """Получает клиентов с учетом пагинации."""
    conn = connect_db()
    if conn is None:
        return []

    offset = (page - 1) * per_page  # Расчет смещения для SQL-запроса

    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT "ID клиента", "ФИО", "Email", "Дата рождения", "Номер телефона" '
            'FROM public."Клиент" '
            'ORDER BY "ID клиента" '
            'LIMIT %s OFFSET %s;',
            (per_page, offset)
        )
        rows = cur.fetchall()
        cur.close()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        rows = []
    finally:
        conn.close()

    clients = [
        {
            "ID клиента": row[0],
            "ФИО": row[1],
            "Email": row[2],
            "Дата рождения": row[3].isoformat() if row[3] else None,
            "Номер телефона": row[4]
        }
        for row in rows
    ]
    
    return clients

def search_client(query):
    """Ищет клиента по ID или ФИО."""
    conn = connect_db()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        # Проверяем, является ли query числом (ID клиента)
        if query.isdigit():  # Если это число
            cur.execute(
                'SELECT "ID клиента", "ФИО", "Email", "Дата рождения", "Номер телефона" '
                'FROM public."Клиент" '
                'WHERE "ID клиента" = %s;',
                (int(query),)  # Преобразуем в число, если это ID
            )
        else:
            # Если это не число, ищем по ФИО
            cur.execute(
                'SELECT "ID клиента", "ФИО", "Email", "Дата рождения", "Номер телефона" '
                'FROM public."Клиент" '
                'WHERE "ФИО" ILIKE %s;',
                (f'%{query}%',)  # Поиск по ФИО с учетом регистра
            )

        rows = cur.fetchall()
        cur.close()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        rows = []
    finally:
        conn.close()

    clients = [
        {
            "ID клиента": row[0],
            "ФИО": row[1],
            "Email": row[2],
            "Дата рождения": row[3].isoformat() if row[3] else None,
            "Номер телефона": row[4]
        }
        for row in rows
    ]
    return clients


def add_client(fio, email, dob, phone):
    """Добавляет нового клиента в таблицу 'Клиент'."""
    conn = connect_db()
    if conn is None:
        return False

    try:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO public."Клиент" ("ФИО", "Email", "Дата рождения", "Номер телефона") VALUES (%s, %s, %s, %s)',
            (fio, email, dob, phone)
        )
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print("Ошибка при добавлении клиента:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

#....................................................................

def get_applications_paginated(page, per_page):
    """Получает заявки с учетом пагинации."""
    conn = connect_db()
    if conn is None:
        return []

    offset = (page - 1) * per_page  # Расчет смещения для SQL-запроса

    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT "Номер заявки", "ID Клиента", "ID услуги", "ID выполняющего работы", "ID проверяющего", "Гарантия", "Дата" '
            'FROM public."Заявка" '
            'ORDER BY "Номер заявки" '
            'LIMIT %s OFFSET %s;',
            (per_page, offset)
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

def search_application(query):
    """Ищет заявку по номеру заявки или ID клиента."""
    conn = connect_db()
    if conn is None:
        return []

    try:
        cur = conn.cursor()
        # Поиск по номеру заявки или ID клиента
        cur.execute(
            'SELECT "Номер заявки", "ID Клиента", "ID услуги", "ID выполняющего работы", "ID проверяющего", "Гарантия", "Дата" '
            'FROM public."Заявка" '
            'WHERE "Номер заявки" = %s OR "ID Клиента" = %s;',
            (query, query)
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
