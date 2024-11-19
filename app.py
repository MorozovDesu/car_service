from flask import Flask, jsonify, request, render_template, abort, redirect, url_for, session
from models import connect_db, get_applications_for_client, get_applications_paginated, get_cars_by_client_id, get_client_by_phone, get_clients_paginated,  search_application, search_client
from models import get_client_by_phone, get_worker_by_email


from datetime import timedelta

app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = 'your_secret_key'  # Секретный ключ для работы сессий (измените на ваш)
app.permanent_session_lifetime = timedelta(days=5)


@app.route('/', methods=['GET', 'POST'])
def login():
    """Единая страница входа для клиента и работника."""
    if request.method == 'POST':
        identifier = request.form.get('identifier')  # Номер телефона или Email
        password = request.form.get('password')

        # Сначала пытаемся найти клиента по номеру телефона
        client = get_client_by_phone(identifier)

        if client and client['Пароль'] == password:  # Сравниваем пароли напрямую
            # Если нашли клиента, сохраняем ID в сессию
            session['client_id'] = client['ID клиента']
            session['user_name'] = client['ФИО']
            # Переход на страницу клиента
            return redirect(url_for('dashboard'))

        # Если не нашли клиента, пытаемся найти работника по email
        worker = get_worker_by_email(identifier)

        if worker and worker['Пароль'] == password:  # Сравниваем пароли напрямую
            # Если нашли работника, сохраняем ID в сессию
            session['worker_id'] = worker['ID работника']
            session['worker_position'] = worker['Должность']
            # Переход на страницу работника
            return redirect(url_for('dashboard_worker'))

        # Если ни клиент, ни работник не найдены
        return render_template('login.html', error="Неверные данные для входа")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из системы."""
    session.pop('client_id', None)  # Удаляем client_id из сессии
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    """Страница дашборда для клиента."""
    if 'client_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', client_id=session['client_id'])

@app.route('/clients')
def clients():
    """Страница списка клиентов."""
    # Проверяем авторизацию: клиент или работник
    if 'client_id' not in session and 'worker_id' not in session:
        return redirect(url_for('login'))

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    query = request.args.get('query', '').strip()

    if query:
        clients = search_client(query)
        return render_template('search.html', clients=clients, query=query, user=session.get('user_name', 'Пользователь'))
    else:
        clients = get_clients_paginated(page, per_page)

    return render_template('clients.html', clients=clients, page=page, per_page=per_page, user=session.get('user_name', 'Пользователь'))


@app.route('/api/clients', methods=['GET'])
def api_get_clients():
    """API для списка клиентов с пагинацией."""
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))

    clients = get_clients_paginated(page, per_page)
    return jsonify(clients)

@app.route('/client/search', methods=['GET'])
def search():
    """Поиск клиента."""
    # Проверяем авторизацию
    if 'client_id' not in session and 'worker_id' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '').strip()
    clients = search_client(query) if query else []

    return render_template(
        'search.html',
        clients=clients,
        query=query,
        user=session.get('user_name', 'Пользователь')
    )


@app.route('/cars')
def cars():
    """Страница с информацией об автомобилях клиента."""
    if 'client_id' not in session:
        return redirect(url_for('login'))

    client_id = session['client_id']
    cars = get_cars_by_client_id(client_id)
    return render_template('cars.html', cars=cars, user=session.get('user_name', 'Пользователь'))

@app.route('/cars/delete/<string:car_number>', methods=['POST'])
def delete_car(car_number):
    """Удаление автомобиля клиента."""
    if 'client_id' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    if conn is None:
        return "Ошибка подключения к базе данных", 500

    try:
        with conn.cursor() as cur:
            # Удаляем автомобиль по номеру
            cur.execute(
                '''
                DELETE FROM public."Карточка автомобиля"
                WHERE "Номер автомобиля" = %s AND "ID клиента" = %s;
                ''',
                (car_number, session['client_id'])
            )
            conn.commit()
            return redirect(url_for('cars'))  # Редирект обратно на страницу с автомобилями
    except Exception as e:
        print("Ошибка при удалении автомобиля:", e)
        conn.rollback()
        return "Ошибка при удалении автомобиля", 500
    finally:
        conn.close()

@app.route('/cars/add', methods=['GET', 'POST'])
def add_car():
    """Страница для добавления машины клиента."""
    if 'client_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Получаем данные из формы
        car_number = request.form.get('car_number')
        car_name = request.form.get('car_name')
        car_brand = request.form.get('car_brand')
        model = request.form.get('model')

        # Добавляем машину в базу данных
        conn = connect_db()
        if conn is None:
            return "Ошибка подключения к базе данных", 500

        try:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    INSERT INTO public."Карточка автомобиля" ("Номер автомобиля", "Название", "Марка", "Модель", "ID клиента")
                    VALUES (%s, %s, %s, %s, %s);
                    ''',
                    (car_number, car_name, car_brand, model, session['client_id'])
                )
                conn.commit()
            return redirect(url_for('cars'))
        except Exception as e:
            print("Ошибка при добавлении машины:", e)
            conn.rollback()
            return "Ошибка при добавлении машины", 500
        finally:
            conn.close()

    # Получаем список моделей для выбора
    conn = connect_db()
    if conn is None:
        return "Ошибка подключения к базе данных", 500

    try:
        with conn.cursor() as cur:
            cur.execute('SELECT "Модель" FROM public."Модель автомобиля";')
            models = cur.fetchall()
    except Exception as e:
        print("Ошибка при получении моделей:", e)
        models = []
    finally:
        conn.close()

    # Отображаем форму с выбором модели
    return render_template('add_car.html', models=[row[0] for row in models])


@app.route('/cars/edit/<car_number>', methods=['GET', 'POST'])
def edit_car(car_number):
    """Страница для редактирования информации об автомобиле."""
    
    if not car_number:
        return "Ошибка: Номер автомобиля не указан", 400
    if 'client_id' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    if conn is None:
        return "Ошибка подключения к базе данных", 500

    if request.method == 'POST':
        # Получение данных из формы
        car_name = request.form.get('car_name')
        car_brand = request.form.get('car_brand')
        model = request.form.get('model')

        try:
            with conn.cursor() as cur:
                # Обновляем данные автомобиля
                cur.execute(
                    '''
                    UPDATE public."Карточка автомобиля"
                    SET "Название" = %s, "Марка" = %s, "Модель" = %s
                    WHERE "Номер автомобиля" = %s;
                    ''',
                    (car_name, car_brand, model, car_number)
                )
                conn.commit()
            return redirect(url_for('cars'))
        except Exception as e:
            print("Ошибка при редактировании автомобиля:", e)
            conn.rollback()
            return "Ошибка при редактировании автомобиля", 500
        finally:
            conn.close()

    # Если метод GET, подгружаем текущие данные автомобиля
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "Номер автомобиля", "Название", "Марка", "Модель"
                FROM public."Карточка автомобиля"
                WHERE "Номер автомобиля" = %s;
                ''',
                (car_number,)
            )
            car = cur.fetchone()

            # Получаем список моделей для выбора
            cur.execute('SELECT DISTINCT "Модель" FROM public."Модель автомобиля";')
            models = [row[0] for row in cur.fetchall()]
    except Exception as e:
        print("Ошибка при загрузке данных автомобиля:", e)
        return "Ошибка при загрузке данных", 500
    finally:
        conn.close()

    return render_template(
        'edit_car.html',
        car=car,
        models=models
    )

@app.route('/applications/add', methods=['GET', 'POST'])
def add_application():
    """Страница для добавления заявки."""
    if 'client_id' not in session:
        return redirect(url_for('login'))

    # Подключаемся к базе данных
    conn = connect_db()
    if conn is None:
        return "Ошибка подключения к базе данных", 500

    # Получаем список услуг из базы данных
    services = []
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT "ID услуги", "Тип услуги" FROM public."Услуга";')
            services = cur.fetchall()  # Список услуг
    except Exception as e:
        print("Ошибка при получении услуг:", e)
        return "Ошибка при получении услуг", 500
    finally:
        conn.close()

    # Обработка формы при POST-запросе
    if request.method == 'POST':
        service_id = request.form.get('service_id')
        warranty = request.form.get('warranty')
        warranty = True if warranty == 'true' else False  # Преобразуем строку в bool
        date = request.form.get('date')

        # Добавляем заявку в базу данных
        conn = connect_db()
        if conn is None:
            return "Ошибка подключения к базе данных", 500

        try:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    INSERT INTO public."Заявка" ("ID Клиента", "ID услуги", "Гарантия", "Дата")
                    VALUES (%s, %s, %s, %s);
                    ''',
                    (session['client_id'], service_id, warranty, date)
                )
                conn.commit()
            return redirect(url_for('applications'))  # Перенаправляем на страницу заявок
        except Exception as e:
            print("Ошибка при добавлении заявки:", e)
            conn.rollback()
            return "Ошибка при добавлении заявки", 500
        finally:
            conn.close()

    # Отображаем форму с услугами
    return render_template('add_application.html', services=services)

from datetime import datetime

@app.route('/applications/edit/<int:application_id>', methods=['GET', 'POST'])
def edit_application(application_id):
    """Редактирование заявки."""
    if 'client_id' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    if conn is None:
        return "Ошибка подключения к базе данных", 500

    try:
        if request.method == 'POST':
            # Обновление заявки
            service_id = request.form.get('service_id')
            warranty = request.form.get('warranty') == 'true'
            date = request.form.get('date')

            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE public."Заявка"
                    SET "ID услуги" = %s, "Гарантия" = %s, "Дата" = %s
                    WHERE "Номер заявки" = %s;
                ''', (service_id, warranty, date, application_id))
                conn.commit()
            return redirect(url_for('applications'))

        # Получение данных заявки для отображения в форме
        with conn.cursor() as cur:
            cur.execute('''
                SELECT z."Номер заявки", z."ID услуги", z."Гарантия", z."Дата", u."Тип услуги"
                FROM public."Заявка" z
                JOIN public."Услуга" u ON z."ID услуги" = u."ID услуги"
                WHERE z."Номер заявки" = %s;
            ''', (application_id,))
            application = cur.fetchone()

            if not application:
                return "Заявка не найдена", 404

            cur.execute('SELECT "ID услуги", "Тип услуги" FROM public."Услуга";')
            services = cur.fetchall()

        # Форматируем дату для передачи в шаблон
        formatted_date = application[3].strftime('%Y-%m-%d') if application[3] else ''

        return render_template(
            'edit_application.html',
            application={
                "Номер заявки": application[0],
                "ID услуги": application[1],
                "Гарантия": application[2],
                "Дата": formatted_date,  # Форматированная дата
                "Тип услуги": application[4]
            },
            services=services
        )
    except Exception as e:
        print("Ошибка при редактировании заявки:", e)
        return "Ошибка при редактировании заявки", 500
    finally:
        conn.close()
# 
@app.route('/applications', methods=['GET'])
def applications():
    """Страница заявок."""
    # Проверяем авторизацию
    if 'client_id' not in session:
        return redirect(url_for('login'))

    client_id = session['client_id']
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Получаем заявки с названиями услуг
    applications = get_applications_for_client(client_id, page, per_page)

    return render_template(
        'applications.html',
        applications=applications,
        page=page,
        user=session.get('user_name', 'Пользователь')
    )
# 

@app.route('/applications/delete/<int:application_id>', methods=['POST'])
def delete_application(application_id):
    """Удаление заявки по ее номеру."""
    if 'client_id' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    if conn is None:
        return "Ошибка подключения к базе данных", 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                DELETE FROM public."Заявка"
                WHERE "Номер заявки" = %s AND "ID Клиента" = %s;
                ''',
                (application_id, session['client_id'])
            )
            conn.commit()
    except Exception as e:
        print("Ошибка при удалении заявки:", e)
        conn.rollback()
        return "Ошибка при удалении заявки", 500
    finally:
        conn.close()

    return redirect(url_for('applications'))

@app.route('/applications/delete/<int:application_number>', methods=['POST'])
def delete_application_route(application_number):
    """Обработчик для удаления заявки."""
    if 'client_id' not in session:
        return redirect(url_for('login'))

    if delete_application(application_number):
        return redirect(url_for('applications'))  # Редирект на страницу с заявками
    else:
        return "Ошибка при удалении заявки", 500
#/////////////////////////////////////////////////////////Обработка работника

@app.route('/dashboard/worker/completed', methods=['GET'])
def completed_tasks():
    """Дашборд для выполненных заявок."""
    if 'worker_id' not in session:
        return redirect(url_for('login'))

    worker_id = session['worker_id']
    conn = connect_db()
    if conn is None:
        return "Ошибка подключения к базе данных", 500

    try:
        with conn.cursor() as cur:
            # Получение выполненных заявок
            cur.execute(
                '''
                SELECT z."Номер заявки", z."Дата", u."Тип услуги", c."ФИО", z."Гарантия", z."Дата выполнения"
                FROM public."Заявка" z
                JOIN public."Услуга" u ON z."ID услуги" = u."ID услуги"
                JOIN public."Клиент" c ON z."ID Клиента" = c."ID клиента"
                WHERE z."ID выполняющего работы" = %s AND z."Дата выполнения" IS NOT NULL;
                ''',
                (worker_id,)
            )
            completed_tasks = cur.fetchall()
    except Exception as e:
        print("Ошибка при загрузке выполненных заявок:", e)
        return "Ошибка при загрузке данных", 500
    finally:
        conn.close()

    # Отображение шаблона с выполненными заявками
    return render_template(
        'completed_tasks.html',
        completed_tasks=completed_tasks,
        worker_name=session.get('worker_name', 'Исполнитель')
    )

@app.route('/mark_task_completed/<int:task_id>', methods=['POST'])
def mark_task_completed(task_id):
    """Отметить заявку как выполненную."""
    if 'worker_id' not in session:
        return redirect(url_for('login'))

    worker_id = session['worker_id']
    conn = connect_db()
    if conn is None:
        return "Ошибка подключения к базе данных", 500

    try:
        with conn.cursor() as cur:
            # Обновление заявки, добавление даты выполнения
            cur.execute(
                '''
                UPDATE public."Заявка"
                SET "Дата выполнения" = CURRENT_DATE
                WHERE "Номер заявки" = %s AND "ID выполняющего работы" = %s;
                ''',
                (task_id, worker_id)
            )
            conn.commit()
    except Exception as e:
        print("Ошибка при обновлении заявки:", e)
        return "Ошибка при обновлении данных", 500
    finally:
        conn.close()

    return redirect(url_for('dashboard_worker'))

@app.route('/dashboard/worker', methods=['GET'])
def dashboard_worker():
    """Дашборд для выполняющего работы."""
    if 'worker_id' not in session:
        return redirect(url_for('login'))

    worker_id = session['worker_id']
    conn = connect_db()
    if conn is None:
        return "Ошибка подключения к базе данных", 500

    try:
        with conn.cursor() as cur:
            # Получение заявок, назначенных выполняющему работы
            cur.execute(
                '''
                SELECT z."Номер заявки", z."Дата", u."Тип услуги", c."ФИО", z."Гарантия"
                FROM public."Заявка" z
                JOIN public."Услуга" u ON z."ID услуги" = u."ID услуги"
                JOIN public."Клиент" c ON z."ID Клиента" = c."ID клиента"
                WHERE z."ID выполняющего работы" = %s AND z."Дата выполнения" IS NULL;
                ''',
                (worker_id,)
            )
            tasks_to_complete = cur.fetchall()

            # Статистика: количество выполненных заявок
            cur.execute(
                '''
                SELECT COUNT(*)
                FROM public."Заявка"
                WHERE "ID выполняющего работы" = %s AND "Дата выполнения" IS NOT NULL;
                ''',
                (worker_id,)
            )
            completed_tasks_count = cur.fetchone()[0]
    except Exception as e:
        print("Ошибка при загрузке данных для дашборда выполняющего:", e)
        return "Ошибка при загрузке данных", 500
    finally:
        conn.close()

    # Отображение шаблона дашборда
    return render_template(
        'dashboard_worker.html',
        tasks_to_complete=tasks_to_complete,
        completed_tasks_count=completed_tasks_count,
        worker_name=session.get('worker_name', 'Исполнитель')
    )




















if __name__ == '__main__':
    app.run(debug=True)

