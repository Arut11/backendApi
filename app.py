from unittest import result
from flask import Flask, request, jsonify
import psycopg2
import json
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# Функция для создания соединения с базой данных и возвращения соединения и курсора
def get_db_connection():
    conn = psycopg2.connect(
        database="habrdb",
        user="habrpguser",
        password="123456",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    return conn, cursor




                                    # удаление заказа по номеру заказа
@app.route('/orders', methods=['DELETE'])
def delete_orders_with_status_3():
    try:
        conn, cur = get_db_connection()
        
        cur.execute('DELETE FROM order_item WHERE order_id IN (SELECT order_id FROM orders WHERE order_status = %s)', ('3',))
        conn.commit()
        
        cur.execute('DELETE FROM orders WHERE order_status = %s RETURNING order_id', ('3',))
        deleted_order_ids = cur.fetchall()
        if not deleted_order_ids:
            conn.close()
            response = jsonify({"message": "Заказы со статусом 3 не найдены"})
            response.status_code = 400
            return response
        
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Заказы со статусом 3 успешно удалены"})
    
    except psycopg2.Error as e:
        return jsonify({"message": "Ошибка при удалении заказов со статусом 3"})





                                                # Официант
@app.route('/waiter', methods=['POST'])
def create_waiter():
    try:
        conn, cur = get_db_connection()

        table_number = request.json['table_number']

        if 'call_waiter' in request.json:
            cur.execute('INSERT INTO waiter (table_number, call_waiter, score) VALUES(%s, %s, %s)',
                        (table_number, 1, 0))  # передача call_waiter означает вызов официанта

        if 'score' in request.json:
            cur.execute('INSERT INTO waiter (table_number, call_waiter, score) VALUES(%s, %s, %s)',
                        (table_number, 0, 1))  # передача score означает запрос счета

        conn.commit()
        conn.close()
        return jsonify({"message": "Официант скоро будет"})
    except psycopg2.Error as e:
        return jsonify({"message": "Ошибка при вызове"})


                                        #Получить данные из таблицы вызова официанта
    
@app.route('/waiter', methods=['GET'])
def get_waiter():
    try:
        con = psycopg2.connect(
            database="habrdb",
            user="habrpguser",
            password="123456",
            host="localhost",
            port="5432"
        )
        cur = con.cursor()

        cur.execute('SELECT * FROM waiter WHERE completed IS NULL')

        rows = cur.fetchall()
        waiters = {}

        for row in rows:
            waiter_id, table_number, call_waiter, score, completed = row
            waiters[waiter_id] = {
                    "waiter_id": waiter_id,
                    "table_number": table_number,
                    "call_waiter": call_waiter,
                    "score": score,
                    "completed": completed
                }

        cur.close()
        con.close()
        
        return jsonify(waiters)

    except psycopg2.Error as e:
        return jsonify({"message": "Ошибка при получении данных официанта"})


                                       #Обновляю таблицу вызова официанта с меткой "Обслужен" true
@app.route('/waiter/<int:waiter_id>', methods=['PUT'])
def update_waiter(waiter_id):
    try:
        conn, cur = get_db_connection()

        cur.execute('UPDATE waiter SET completed = 1 WHERE waiter_id = %s', (waiter_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Информация о заказе с ID {waiter_id} успешно обновлена"})
    except psycopg2.Error as e:
        return jsonify({"message": "Ошибка при обновлении информации о заказе"})
    




                                             # Создание нового заказа
@app.route('/orders', methods=['POST'])
def create_order():
    try:
        conn, cur = get_db_connection()

        # Проверяем, есть ли уже заказы в таблице orders
        cur.execute('SELECT MAX(order_id) FROM orders')
        max_order_id = cur.fetchone()[0]

        if max_order_id is None:
            order_id = 1
        else:
            order_id = max_order_id + 1

        # Создаем новый заказ
        table_number = request.json['table_number']
        order_price = request.json['order_price']
        order_comment = request.json['order_comment']
        cur.execute('INSERT INTO orders (order_id, table_number, order_status, order_price, order_comment) VALUES (%s, %s, %s, %s, %s)',
                    (order_id, table_number, 1, order_price, order_comment))

        # Добавляем позиции в заказ
        items = request.json['items']
        for item in items:
            dish_id = item['dish_id']
            quantity = item['quantity']
            cur.execute('INSERT INTO order_item (order_id, dish_id, quantity) VALUES (%s, %s, %s)',
                        (order_id, dish_id, quantity))

        conn.commit()
        conn.close()

        response_data = {
            'order_id': order_id
        }
        return json.dumps(response_data)
    except psycopg2.Error as e:
        response_data = {
            'error': str(e),
            'message': 'Произошла ошибка при создании заказа: {}'.format(str(e))
        }
        return json.dumps(response_data)

    #Изменить статус заказа по его order_id
@app.route('/orders/<int:order_id>/update_status', methods=['PUT'])
def update_order_status(order_id):
    try:
        conn, cur = get_db_connection()

        new_status = request.json['new_status']

        # Проверяем существование заказа
        cur.execute('SELECT * FROM orders WHERE order_id = %s', (order_id,))
        order = cur.fetchone()

        if order is None:
            response_data = {
                'message': 'Заказ с указанным order_id не найден.'
            }
            return json.dumps(response_data), 404

        # Обновляем статус заказа
        cur.execute('UPDATE orders SET order_status = %s WHERE order_id = %s', (new_status, order_id))
        conn.commit()
        conn.close()

        response_data = {
            'message': 'Статус заказа успешно обновлен.'
        }
        return json.dumps(response_data)
    except psycopg2.Error as e:
        response_data = {
            'error': str(e),
            'message': 'Произошла ошибка при обновлении статуса заказа: {}'.format(str(e))
        }
        return json.dumps(response_data), 400

    
    #Получить заказы в конкретном статусе
@app.route('/orders/<order_status>', methods=['GET'])
def get_order_info(order_status):
    try:
        con = psycopg2.connect(
        database="habrdb",
        user="habrpguser",
        password="123456",
        host="localhost",
        port="5432"
        )
        cur = con.cursor()

        cur.execute('SELECT orders.order_id, orders.table_number, dish.dish_name, orders.order_status, dish.price, order_item.quantity, orders.order_comment, orders.order_price FROM orders JOIN order_item ON orders.order_id = order_item.order_id JOIN dish ON order_item.dish_id = dish.dish_id WHERE orders.order_status = %s', (order_status,))
        result = cur.fetchall()
        if not result:
            return jsonify({"error": "Заказы с указанным статусом не найдены"}), 400

        orders = {}
        for row in result:
            order_id, table_number, dish_name, order_status, price, quantity, order_comment, order_price = row
            if order_id not in orders:
                orders[order_id] = {
                    "order_price": order_price,
                    "order_comment": order_comment,
                    "order_id": order_id,
                    "table_number": table_number,
                    "order_status": order_status,
                    "items": []
                }
            order = orders[order_id]
            order["items"].append({
                "dish_name": dish_name,
                "price": price,
                "quantity": quantity
            })

        return jsonify(orders)
    except psycopg2.Error as e:
        response_data = {
            'error': str(e),
            'message': 'Произошла ошибка при получении информации о заказе: {}'.format(str(e))
        }
        return json.dumps(response_data)


if __name__ == '__main__':
    app.config['DEBUG'] = True
    app.run()

