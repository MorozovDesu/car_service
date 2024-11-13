# app.py

from flask import Flask, jsonify, request, render_template, abort
from models import get_applications_paginated, get_clients_paginated, add_client, search_application, search_client

app = Flask(__name__)
app.config.from_object('config.Config')

@app.route('/')
def index():
    """Главная страница с HTML-шаблоном и поддержкой пагинации."""
    # Получаем параметры page и per_page из URL (с значениями по умолчанию)
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    query = request.args.get('query', '').strip()
    
    if query:
        clients = search_client(query)
        return render_template('search.html', clients=clients, query=query)
    else:
        clients = get_clients_paginated(page, per_page)
    
    return render_template('index.html', clients=clients, page=page, per_page=per_page)

@app.route('/api/clients', methods=['GET'])
def api_get_clients():
    """API-маршрут для получения списка клиентов с поддержкой пагинации."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))

    clients = get_clients_paginated(page, per_page)
    return jsonify(clients)

@app.route('/client/search', methods=['GET'])
def search():
    """Поиск клиента по ID или ФИО."""
    query = request.args.get('query', '').strip()
    if query:
        clients = search_client(query)
    else:
        clients = []

    return render_template('search.html', clients=clients, query=query)

@app.route('/api/clients', methods=['POST'])
def api_add_client():
    """API-маршрут для добавления нового клиента."""
    data = request.json
    if not data or not all(k in data for k in ("ФИО", "Email", "Дата рождения", "Номер телефона")):
        abort(400, description="Некорректные данные. Требуются поля 'ФИО', 'Email', 'Дата рождения', 'Номер телефона'.")

    if add_client(data["ФИО"], data["Email"], data["Дата рождения"], data["Номер телефона"]):
        return jsonify({"message": "Клиент успешно добавлен"}), 201
    else:
        return "Ошибка добавления клиента", 500

@app.route('/applications', methods=['GET', 'POST'])
def applications():
    page = request.args.get('page', 1, type=int)
    per_page = 25  # Количество записей на странице

    if request.method == 'POST':
        query = request.form.get('query')
        applications = search_application(query)
        return render_template('applications.html', applications=applications, page=1, query=query)

    applications = get_applications_paginated(page, per_page)
    return render_template('applications.html', applications=applications, page=page)


if __name__ == '__main__':
    app.run()
