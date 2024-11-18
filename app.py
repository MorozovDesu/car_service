from flask import Flask, jsonify, request, render_template, abort, redirect, url_for, session
from models import connect_db, get_applications_for_client, get_applications_paginated, get_cars_by_client_id, get_client_by_phone, get_clients_paginated, add_client, search_application, search_client
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

@app.route('/dashboard/worker')
def dashboard_worker():
    """Страница дашборда для работника."""
    if 'worker_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard_worker.html', worker_id=session['worker_id'])

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


@app.route('/api/clients', methods=['POST'])
def api_add_client():
    """API для добавления нового клиента."""
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data or not all(k in data for k in ("ФИО", "Email", "Дата рождения", "Номер телефона")):
        abort(400, description="Некорректные данные. Требуются поля 'ФИО', 'Email', 'Дата рождения', 'Номер телефона'.")

    if add_client(data["ФИО"], data["Email"], data["Дата рождения"], data["Номер телефона"]):
        return jsonify({"message": "Клиент успешно добавлен"}), 201
    else:
        return "Ошибка добавления клиента", 500

@app.route('/applications', methods=['GET'])
def applications():
    """Страница заявок."""
    # Проверяем авторизацию
    if 'client_id' not in session:
        return redirect(url_for('login'))

    client_id = session['client_id']
    page = request.args.get('page', 1, type=int)
    per_page = 10

    applications = get_applications_for_client(client_id, page, per_page)

    return render_template(
        'applications.html',
        applications=applications,
        page=page,
        user=session.get('user_name', 'Пользователь')
    )

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





















if __name__ == '__main__':
    app.run(debug=True)

