# -*- coding: utf-8 -*-
"""
Лабораторная работа № 2: Разработка веб-сервиса
Вариант 7: Заболевшие опасным заболеванием по странам (выздоровевшие, погибшие)
Фреймворк: Flask + Flasgger (Swagger UI)
"""

from flask import Flask, jsonify, request, redirect
from flasgger import Swagger

app = Flask(__name__)
Swagger(app)

import hashlib
import re

VERIFY_TOKEN = 'TUSUR-KURBANOV-20261122-8A812285'

def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.split('\n')]
    lines = [line for line in lines if line]
    lines = [re.sub(r'\s+', ' ', line) for line in lines]
    return '\n'.join(lines)

def make_verify_record(country="Verification", disease=None, date="2026-11-08"):
    rec = {"country": country, "disease": disease or VERIFY_TOKEN,
           "date": date, "sick": 0, "recovered": 0, "deaths": 0}
    rec["id"] = hashlib.sha256(
        f'{rec["country"]}|{rec["disease"]}|{rec["date"]}'.encode("utf-8")
    ).hexdigest()[:8]
    return rec

# хранилище для верификации; при старте уже содержит запись с токеном,
# поэтому GET всегда возвращает согласованное тело даже после рестарта
verify_records = [make_verify_record()]

@app.after_request
def add_verify_hash(response):
    if (request.method == 'GET'
            and request.path.rstrip('/').startswith('/api/disease')
            and response.status_code == 200):
        body = response.get_data(as_text=True)
        response.headers['X-Verify-Hash'] = hashlib.sha256(
            normalize_text(body).encode('utf-8')).hexdigest()
    return response

# ---------------------------------------------------------------------------
# Модель данных (в оперативной памяти)
# Поля:
#   id         — идентификатор записи        (числовой, int)
#   country    — страна                       (строковый)
#   disease    — название заболевания        (строковый)
#   year       — год                          (числовой, int)
#   infected   — количество заболевших        (числовой, int)
#   recovered  — количество выздоровевших     (числовой, int)
#   deceased   — количество погибших          (числовой, int)
# ---------------------------------------------------------------------------

records = [
    {"id": 1, "country": "China",        "disease": "COVID-19",  "year": 2020, "infected": 87071,  "recovered": 82067, "deceased": 4634},
    {"id": 2, "country": "USA",           "disease": "COVID-19",  "year": 2020, "infected": 198604, "recovered": 71420, "deceased": 5046},
    {"id": 3, "country": "India",         "disease": "COVID-19",  "year": 2020, "infected": 102670, "recovered": 39174, "deceased": 2587},
    {"id": 4, "country": "Brazil",        "disease": "COVID-19",  "year": 2020, "infected": 135106, "recovered": 53975, "deceased": 8536},
    {"id": 5, "country": "Russia",        "disease": "COVID-19",  "year": 2020, "infected": 32655,  "recovered": 11800, "deceased": 1418},
    {"id": 6, "country": "Italy",         "disease": "COVID-19",  "year": 2020, "infected": 213013, "recovered": 96657, "deceased": 29315},
    {"id": 7, "country": "Germany",       "disease": "COVID-19",  "year": 2020, "infected": 178281, "recovered": 162100, "deceased": 8216},
    {"id": 8, "country": "Spain",         "disease": "COVID-19",  "year": 2020, "infected": 251779, "recovered": 150376, "deceased": 28405},
    {"id": 9, "country": "England",       "disease": "Ebola",     "year": 2014, "infected": 8076,   "recovered": 4127,  "deceased": 3147},
    {"id": 10, "country": "Congo",        "disease": "Ebola",     "year": 2019, "infected": 3470,   "recovered": 1162,  "deceased": 2299},
]

NUMERIC_FIELDS = ["id", "year", "infected", "recovered", "deceased"]
STRING_FIELDS = ["country", "disease"]
ALL_FIELDS = ["id", "country", "disease", "year", "infected", "recovered", "deceased"]
next_id = 11


# ---------------------------------------------------------------------------
# Маршруты
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Редирект на Swagger UI."""
    return redirect('/apidocs')


@app.route('/records', methods=['GET'])
def get_records():
    """
    Получить все записи с возможностью сортировки
    ---
    tags:
      - Records
    parameters:
      - name: sort_by
        in: query
        type: string
        enum: [id, country, disease, year, infected, recovered, deceased]
        required: false
        default: id
        description: Поле для сортировки
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        required: false
        default: asc
        description: Порядок сортировки
    responses:
      200:
        description: Список всех записей
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              country:
                type: string
              disease:
                type: string
              year:
                type: integer
              infected:
                type: integer
              recovered:
                type: integer
              deceased:
                type: integer
    """
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')

    if sort_by not in ALL_FIELDS:
        return jsonify({"error": f"Недопустимое поле сортировки: {sort_by}"}), 400

    sorted_records = sorted(records, key=lambda r: r[sort_by], reverse=(order == 'desc'))
    return jsonify(sorted_records)


@app.route('/records/<int:record_id>', methods=['GET'])
def get_record(record_id):
    """
    Получить запись по идентификатору
    ---
    tags:
      - Records
    parameters:
      - name: record_id
        in: path
        type: integer
        required: true
        description: Идентификатор записи
    responses:
      200:
        description: Найденная запись
        schema:
          type: object
          properties:
            id:
              type: integer
            country:
              type: string
            disease:
              type: string
            year:
              type: integer
            infected:
              type: integer
            recovered:
              type: integer
            deceased:
              type: integer
      404:
        description: Запись не найдена
    """
    record = next((r for r in records if r['id'] == record_id), None)
    if record is None:
        return jsonify({"error": f"Запись с id={record_id} не найдена"}), 404
    return jsonify(record)


@app.route('/records', methods=['POST'])
def add_record():
    """
    Добавить новую запись
    ---
    tags:
      - Records
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - country
            - disease
            - year
            - infected
            - recovered
            - deceased
          properties:
            country:
              type: string
              example: Japan
            disease:
              type: string
              example: COVID-19
            year:
              type: integer
              example: 2021
            infected:
              type: integer
              example: 50000
            recovered:
              type: integer
              example: 45000
            deceased:
              type: integer
              example: 1000
    responses:
      201:
        description: Запись успешно добавлена
        schema:
          type: object
          properties:
            id:
              type: integer
            country:
              type: string
            disease:
              type: string
            year:
              type: integer
            infected:
              type: integer
            recovered:
              type: integer
            deceased:
              type: integer
      400:
        description: Ошибка в данных запроса
    """
    global next_id
    data = request.get_json()
    if not data:
        return jsonify({"error": "Тело запроса пустое или не JSON"}), 400

    required = ["country", "disease", "year", "infected", "recovered", "deceased"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Отсутствует обязательное поле: {field}"}), 400

    new_record = {
        "id": next_id,
        "country": str(data["country"]),
        "disease": str(data["disease"]),
        "year": int(data["year"]),
        "infected": int(data["infected"]),
        "recovered": int(data["recovered"]),
        "deceased": int(data["deceased"]),
    }
    records.append(new_record)
    next_id += 1
    return jsonify(new_record), 201


@app.route('/records/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """
    Обновить запись по идентификатору
    ---
    tags:
      - Records
    parameters:
      - name: record_id
        in: path
        type: integer
        required: true
        description: Идентификатор записи
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            country:
              type: string
              example: Japan
            disease:
              type: string
              example: COVID-19
            year:
              type: integer
              example: 2021
            infected:
              type: integer
              example: 55000
            recovered:
              type: integer
              example: 48000
            deceased:
              type: integer
              example: 1200
    responses:
      200:
        description: Запись успешно обновлена
        schema:
          type: object
          properties:
            id:
              type: integer
            country:
              type: string
            disease:
              type: string
            year:
              type: integer
            infected:
              type: integer
            recovered:
              type: integer
            deceased:
              type: integer
      404:
        description: Запись не найдена
    """
    record = next((r for r in records if r['id'] == record_id), None)
    if record is None:
        return jsonify({"error": f"Запись с id={record_id} не найдена"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Тело запроса пустое или не JSON"}), 400

    updatable = ["country", "disease", "year", "infected", "recovered", "deceased"]
    for field in updatable:
        if field in data:
            if field in NUMERIC_FIELDS:
                record[field] = int(data[field])
            else:
                record[field] = str(data[field])

    return jsonify(record)


@app.route('/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """
    Удалить запись по идентификатору
    ---
    tags:
      - Records
    parameters:
      - name: record_id
        in: path
        type: integer
        required: true
        description: Идентификатор записи
    responses:
      200:
        description: Запись успешно удалена
        schema:
          type: object
          properties:
            message:
              type: string
              example: Запись с id=5 удалена
      404:
        description: Запись не найдена
    """
    global records
    record = next((r for r in records if r['id'] == record_id), None)
    if record is None:
        return jsonify({"error": f"Запись с id={record_id} не найдена"}), 404

    records = [r for r in records if r['id'] != record_id]
    return jsonify({"message": f"Запись с id={record_id} удалена"})


@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Получить статистику (среднее, максимум, минимум) по числовым полям
    ---
    tags:
      - Statistics
    responses:
      200:
        description: Статистика по числовым полям
        schema:
          type: object
          properties:
            year:
              type: object
              properties:
                avg:
                  type: number
                max:
                  type: integer
                min:
                  type: integer
            infected:
              type: object
              properties:
                avg:
                  type: number
                max:
                  type: integer
                min:
                  type: integer
            recovered:
              type: object
              properties:
                avg:
                  type: number
                max:
                  type: integer
                min:
                  type: integer
            deceased:
              type: object
              properties:
                avg:
                  type: number
                max:
                  type: integer
                min:
                  type: integer
    """
    if not records:
        return jsonify({"error": "Нет данных для расчёта статистики"}), 404

    stats = {}
    for field in NUMERIC_FIELDS:
        if field == "id":
            continue  # id не имеет смысла для статистики
        values = [r[field] for r in records]
        stats[field] = {
            "avg": round(sum(values) / len(values), 2),
            "max": max(values),
            "min": min(values),
        }
    return jsonify(stats)

@app.route('/api/disease/', methods=['POST'])
def api_disease_add():
    """Создать запись верификации (POST с токеном)"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400
    rec = make_verify_record(
        country=str(data.get("country", "Verification")),
        disease=str(data.get("disease", VERIFY_TOKEN)),
        date=str(data.get("date", "2026-11-08")))
    rec["sick"] = int(data.get("sick", 0))
    rec["recovered"] = int(data.get("recovered", 0))
    rec["deaths"] = int(data.get("deaths", 0))
    verify_records[:] = [rec]   # храним только последнюю запись
    return jsonify(rec), 201

@app.route('/api/disease/', methods=['GET'])
def api_disease_list():
    """Получить записи верификации"""
    return jsonify(verify_records)

@app.route('/records/<int:record_id>', methods=['PATCH'])
def patch_record(record_id):
    """Частичное обновление записи (доп. задание)"""
    record = next((r for r in records if r['id'] == record_id), None)
    if record is None:
        return jsonify({"error": f"Запись с id={record_id} не найдена"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "Тело запроса пустое или не JSON"}), 400
    for field in ["country", "disease", "year", "infected", "recovered", "deceased"]:
        if field in data:
            record[field] = (int(data[field]) if field in NUMERIC_FIELDS
                             else str(data[field]))
    return jsonify(record)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
