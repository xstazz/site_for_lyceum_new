from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

menu_list = [
    {"id": 1, "name": "Пицца", "price": 10},
    {"id": 2, "name": "Паста", "price": 8},
    {"id": 3, "name": "Салат", "price": 5},
]

order = []

admin_username = 'admin'
admin_password = 'qwerty'

chef_username = 'chef'
chef_password = 'qwerty'

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создаем таблицу пользователей (если она не существует)
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')

conn.commit()
conn.close()


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login_post():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == admin_username and password == admin_password:
            session['username'] = username
            flash(f"Добро пожаловать, {username}!", 'success')
            return redirect(url_for('admin_panel'))  # Перенаправляем на админ панель

        elif username == chef_username and password == chef_password:
            session['username'] = username
            flash(f"Добро пожаловать, {username}!", 'success')
            return redirect(url_for('chief'))  # Перенаправляем на страницу меню для повара

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Поиск пользователя в базе данных
        cursor.execute("SELECT username, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        conn.close()

        if user and user[1] == password:
            session['username'] = username
            flash(f"Добро пожаловать, {username}!", 'success')
            return redirect(url_for('menu'))

        flash("Неверное имя пользователя или пароль. Пожалуйста, попробуйте снова.", 'error')

    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Пароли не совпадают. Пожалуйста, попробуйте снова.", 'error')
        else:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            # Вставляем данные пользователя в базу данных
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                           (username, email, password))

            conn.commit()
            conn.close()

            flash(f"Регистрация успешна для пользователя: {username}", 'success')
            return redirect(url_for('menu'))

    return render_template('register.html')


@app.route('/admin', methods=['GET'])
def admin_panel():
    if 'username' in session and session['username'] == admin_username:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()

        # Выполняем SQL-запрос для подсчета записей в таблице
        cursor.execute("SELECT COUNT(*) FROM orders")

        # Извлекаем результат запроса
        count = cursor.fetchone()[0]

        conn.close()

        # Проверяем, есть ли данные в таблице
        if count > 0:
            conn = sqlite3.connect('orders.db')
            cursor = conn.cursor()

            cursor.execute("""SELECT * from orders""")
            data = cursor.fetchall()
            conn.execute('DELETE FROM orders;', );
            conn.commit()
            conn.close()
            return render_template('admin_panel.html', data=data)
        else:
            return render_template('admin_panel.html')
    else:
        flash("Доступ к админ панели запрещен.", 'error')
        return redirect(url_for('index'))


@app.route('/menu')
def menu():
    if 'username' in session:
        return render_template('menu.html', menu=menu_list)
    else:
        flash("Пожалуйста, войдите в систему, чтобы получить доступ к меню.", 'error')
        return redirect(url_for('index'))


@app.route('/add_to_order/<int:menu_id>')
def add_to_order(menu_id):
    selected_dish = next((dish for dish in menu_list if dish["id"] == menu_id), None)
    if selected_dish:
        order.append(selected_dish)
    return redirect(url_for('menu'))


@app.route('/view_order')
def view_order():
    total_price = sum(dish['price'] for dish in order)
    return render_template('order.html', order=order, total_price=total_price)


@app.route('/pay_order')
def pay_order():
    # Сохраняем данные о заказе в базу данных
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    for dish in order:
        cursor.execute('''
                INSERT INTO orders (dish_id, dish_name, dish_price)
                VALUES (?, ?, ?)
            ''', (dish['id'], dish['name'], dish['price']))
    conn.commit()
    conn.close()
    order.clear()
    return redirect(url_for('menu'))


@app.route('/clear_order')
def clear_order():
    order.clear()
    return redirect(url_for('menu'))


@app.route('/chief')
def chief():
    if 'username' in session and session['username'] == chef_username:
        return render_template('chief.html', menu=menu_list)
    else:
        flash("Доступ к этой странице запрещен.", 'error')
        return redirect(url_for('index'))


@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute("SELECT username, email FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            username = user[0]
            email = user[1]
            return render_template('profile.html', username=username, email=email)
        else:
            flash("Не удалось загрузить данные профиля.", 'error')
            return redirect(url_for('index'))
    else:
        flash("Пожалуйста, войдите в систему, чтобы получить доступ к профилю.", 'error')
        return redirect(url_for('index'))


@app.route('/update_dish', methods=['POST'])
def update_dish():
    dish_id = int(request.form['dish_id'])
    new_name = request.form['new_name']
    new_price = float(request.form['new_price'])

    # Find the dish in the menu_list and update its name and price
    for dish in menu_list:
        if dish['id'] == dish_id:
            dish['name'] = new_name
            dish['price'] = new_price
            break

    flash("Товар успешно обновлен.", 'success')
    return redirect(url_for('chief'))
@app.route('/add_new_menu', methods=['GET', 'POST'])
def add_new_menu():
    if 'username' in session and session['username'] == chef_username:
        if request.method == 'POST':
            new_name = request.form['new_name']
            new_price = float(request.form['new_price'])

            # Generate a unique ID for the new dish
            new_id = max(dish['id'] for dish in menu_list) + 1 if menu_list else 1

            # Create a dictionary for the new dish and add it to the menu_list
            new_dish = {"id": new_id, "name": new_name, "price": new_price}
            menu_list.append(new_dish)

            flash("Новое блюдо успешно добавлено.", 'success')
            return redirect(url_for('chief'))
        else:
            return render_template('add_new_menu.html')
    else:
        flash("Доступ запрещен.", 'error')
        return redirect(url_for('index'))


if __name__ == '__main__':
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_id INTEGER,
            dish_name TEXT,
            dish_price INTEGER
        )
    ''')
    conn.commit()
    conn.close()

    app.run(debug=True)
