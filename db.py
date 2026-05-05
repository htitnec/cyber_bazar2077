import sqlite3
import os
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'database5.db')

def init_db():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()#создаем объект курсора (интерфейс для взаимодействия с бд)
    # таблица с пользователями
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')#выполняем sql-запрос для создания таблицы users, если она еще не существует
    # таблица с товарами
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        description TEXT,
        image_url TEXT
    )''')
    # таблица с товарами в корзине 
    c.execute('''CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    # таблица с балансом пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS balance (
        user_id INTEGER PRIMARY KEY,
        credits INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    # таблица с заказами
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    # хранение товаров
    c.execute('SELECT COUNT(*) FROM products')#выполняем sql-запрос для подсчета количества строк
    if c.fetchone()[0] == 0:#извлекаем результат запроса; если таблица пуста, то заполняем
        c.executemany('INSERT INTO products (name, price, description, image_url) VALUES (?, ?, ?, ?)', [
            ('Неоновый катана', 999, 'Светящийся клинок из Нео-Токио.', 'images/neon-katana.png'),
            ('Хакерский имплант', 4999, 'Мгновенные навыки кодинга (бета).', 'images/hack-implant.png'),
            ('Глитч-питомец', 199, 'Виртуальный компаньон с собственным разумом.', 'images/glitch-pet.png'),
            ('Кибер-плащ', 2999, 'Невидимость в матрице!', 'images/cyber-plash.png'),
            ('Датавизор', 1499, 'Увидеть матрицу в 8-битной славе.', 'images/datavisor.png'),
            ('Квантовый чип', 7999, 'Разгон мозга до 300%.', 'images/qvant-chip.png'),
            ('Пиксельный дрон', 599, 'Слежка в стиле ретро.', 'images/pixel-dron.png'),
            ('Синтетический кофе', 99, 'Кофеин для кибер-движка.', 'images/syntetic-coffee.png'),
            ('Голограммный проектор', 2499, 'Проецируй свои мечты.', 'images/gologram-proektor.png'),
            ('Нейро-шлем', 3999, 'Подключись к матрице напрямую.', 'images/neyro-shlem.png')
        ])#вставляем строки (? для безопасной вставки)
    conn.commit()#сохраняем изменения
    conn.close()

# получение юзернейма по id пользователя
def get_user(user_id):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

# получение списка товаров 
def get_products():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT id, name, price, description, image_url FROM products')
    products = c.fetchall()
    conn.close()
    return products

# получение корзины пользователя
def get_cart_items(user_id):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT p.id, p.name, p.price, c.quantity FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?', (user_id,))
    cart_items = c.fetchall()
    conn.close()
    return cart_items

# получение баланса пользователя
def get_user_balance(user_id):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT credits FROM balance WHERE user_id = ?', (user_id,))
    balance_result = c.fetchone()
    balance = balance_result[0] if balance_result else 10000
    if not balance_result:
        c.execute('INSERT INTO balance (user_id, credits) VALUES (?, ?)', (user_id, 10000))
        conn.commit()
    conn.close()
    return balance

# история заказов пользователя
def get_user_orders(user_id):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT p.name, p.price, o.quantity, o.order_date FROM orders o JOIN products p ON o.product_id = p.id WHERE o.user_id = ?', (user_id,))
    orders = c.fetchall()
    conn.close()
    return orders

# регистрирует нового пользователя
def register_user(username, hashed_password):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    user_id = c.lastrowid #извлекаем id последней вставленной записи
    c.execute('INSERT INTO balance (user_id, credits) VALUES (?, ?)', (user_id, 10000))
    conn.commit()
    conn.close()

# проверка данных о пользователе
def login_user(username, password):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[1], password):
        return user
    return None

# обновление имени пользователя
def update_user_profile(user_id, new_username):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
    conn.commit()
    conn.close()

# добавление товара в корзину
def add_to_cart(user_id, product_id, quantity):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    
    # проверка, есть ли такой товар в корзине
    c.execute('SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?', 
             (user_id, product_id))
    existing = c.fetchone()
    
    if existing:
        # если есть, то обновляем количество
        new_quantity = existing[1] + quantity
        c.execute('UPDATE cart SET quantity = ? WHERE id = ?', 
                 (new_quantity, existing[0]))
    else:
        # если нет, то создаем новую запись
        c.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)', 
                 (user_id, product_id, quantity))
    
    conn.commit()
    conn.close()

# покупка товаров
def process_purchase(user_id, cart_items, total_cost):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    for item in cart_items:
        product_id, product_name, price, quantity = item
        c.execute('SELECT id FROM products WHERE name = ?', (product_name,))
        product_id = c.fetchone()[0]
        c.execute('INSERT INTO orders (user_id, product_id, quantity) VALUES (?, ?, ?)',
                 (user_id, product_id, quantity))
        c.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', 
                 (user_id, product_id))
    c.execute('UPDATE balance SET credits = credits - ? WHERE user_id = ?', (total_cost, user_id))
    conn.commit()
    conn.close()

# изменение пароля пользователя
def change_user_password(user_id, new_hashed_password):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE id = ?', (new_hashed_password, user_id))
    conn.commit()
    conn.close()

# перевод средств между пользователями
def transfer_funds(sender_id, target_user_id, amount):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('UPDATE balance SET credits = credits - ? WHERE user_id = ?', (amount, sender_id))
    c.execute('UPDATE balance SET credits = credits + ? WHERE user_id = ?', (amount, target_user_id))
    conn.commit()
    conn.close()

# получение id пользователя по юзернейму
def get_user_id_by_username(username):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    target_user = c.fetchone()
    conn.close()
    return target_user[0] if target_user else None

# удаление товара из корзины
def remove_from_cart(user_id, product_id):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    
    # получаем текущее количество
    c.execute('SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?', 
             (user_id, product_id))
    item = c.fetchone()
    
    if item:
        if item[1] > 1:
            # если количество > 1, то уменьшаем на 1
            c.execute('UPDATE cart SET quantity = quantity - 1 WHERE id = ?', 
                     (item[0],))
        else:
            # если количество = 1, то удаляем запись
            c.execute('DELETE FROM cart WHERE id = ?', 
                     (item[0],))
    
    conn.commit()
    conn.close()