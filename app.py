from flask import Flask, jsonify, request, render_template, abort, redirect, url_for, session
from models import get_applications_paginated, get_clients_paginated, add_client, search_application, search_client

app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = 'your_secret_key'  # Секретный ключ для работы сессий (измените на ваш)

# Пример данных пользователей
users = {
    'admin': '1',
    'user': '1'
}

@app.route('/', methods=['GET', 'POST'])
def login():
    """Главная страница с формой входа."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))  # Переход на основную страницу

        return render_template('login.html', error="Неверный логин или пароль")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из системы."""
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Страница дашборда."""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/clients')
def clients():
    """Страница списка клиентов."""
    if 'user' not in session:
        return redirect(url_for('login'))

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    query = request.args.get('query', '').strip()

    if query:
        clients = search_client(query)
        return render_template('search.html', clients=clients, query=query, user=session['user'])
    else:
        clients = get_clients_paginated(page, per_page)

    return render_template('clients.html', clients=clients, page=page, per_page=per_page, user=session['user'])

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
    if 'user' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '').strip()
    if query:
        clients = search_client(query)
    else:
        clients = []

    return render_template('search.html', clients=clients, query=query, user=session['user'])

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

@app.route('/applications', methods=['GET', 'POST'])
def applications():
    """Страница заявок."""
    if 'user' not in session:
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    per_page = 25

    if request.method == 'POST':
        query = request.form.get('query')
        applications = search_application(query)
        return render_template('applications.html', applications=applications, page=1, query=query, user=session['user'])

    applications = get_applications_paginated(page, per_page)
    return render_template('applications.html', applications=applications, page=page, user=session['user'])

if __name__ == '__main__':
    app.run(debug=True)
