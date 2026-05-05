from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash
from db import init_db, get_user, get_products, get_cart_items, register_user, login_user, update_user_profile, add_to_cart, get_user_balance, get_user_orders, process_purchase, change_user_password, transfer_funds, get_user_id_by_username, remove_from_cart

app = Flask(__name__)
app.secret_key = 's3cr3t_k3y_123'  # для шифрования сессий

 
class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class UpdateProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Обновить профиль')

class AddToCartForm(FlaskForm):
    product_id = StringField('ID товара', validators=[DataRequired()])
    quantity = StringField('Количество', validators=[DataRequired()])
    submit = SubmitField('Добавить в корзину')

class PurchaseForm(FlaskForm):
    submit=SubmitField('Подтвердить покупку!')

class ChangePasswordForm(FlaskForm):
    new_password=PasswordField('Новый пароль', validators=[DataRequired()])
    submit=SubmitField('Сменить пароль')

class TransferForm(FlaskForm):
    username = StringField('Имя получателя', validators=[DataRequired()])
    amount = StringField('Сумма', validators=[DataRequired()])
    submit = SubmitField('Перевести')

class RemoveFromCartForm(FlaskForm):
    product_id=HiddenField('ID товара', validators=[DataRequired()])
    submit=SubmitField('Удалить из корзины')


init_db()

# главная страница
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user(session['user_id'])
    if user is None:
        session.pop('user_id', None)
        flash('Пользователь не найден. Войдите снова.', 'error')
        return redirect(url_for('login'))
    
    username = user[0]
    products = get_products()
    cart_items = get_cart_items(session['user_id'])
    balance = get_user_balance(session['user_id'])
    
    form = UpdateProfileForm()
    cart_form = AddToCartForm()
    remove_form=RemoveFromCartForm()
    return render_template('home.html', username=username, form=form, cart_form=cart_form, remove_form=remove_form, products=products, cart_items=cart_items, balance=balance)

# страница регистрации пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():#проверяем, был ли запрос методом POST; валидны ли данные формы; корректен ли csrf-токен
        username = form.username.data
        password = form.password.data
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            register_user(username, hashed_password)#добавление пользователя в бд
            flash('Регистрация успешна! Войдите в матрицу.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Имя пользователя уже занято!', 'error')
    return render_template('register.html', form=form)

# страница входа пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = login_user(username, password)#проверяем данные о пользователе
        if user:
            session['user_id'] = user[0]
            flash('Взлом успешен! Добро пожаловать!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль!', 'error')
    return render_template('login.html', form=form)

# страница профиля
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user(session['user_id'])
    if user is None:
        session.pop('user_id', None)
        flash('Пользователь не найден. Войдите снова.', 'error')
        return redirect(url_for('login'))
    
    username = user[0]
    balance = get_user_balance(session['user_id'])
    cart_items = get_cart_items(session['user_id'])
    orders = get_user_orders(session['user_id'])
    balance = get_user_balance(session['user_id'])
    
    return render_template('profile.html', username=username, balance=balance, cart_items=cart_items, orders=orders)

# страница для выхода
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Выход успешен! До встречи в матрице!', 'success')
    return redirect(url_for('login'))

# добавление товаров в корзину
@app.route('/add_to_cart_vulnerable', methods=['POST'])
def add_to_cart_vulnerable():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    product_id = request.form['product_id']#извлекаем параметры из <form> элемента из POST-запроса
    quantity = int(request.form['quantity'])
    product_id = int(product_id)  
    add_to_cart(session['user_id'], product_id, quantity)
    flash('Товар добавлен в корзину!', 'success')
    return redirect(url_for('home'))

# покупка товаров
@app.route('/purchase',methods=['GET','POST'])
def purchase():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user=get_user(session['user_id'])
    if user is None:
        session.pop('user_id',None)
        flash('Пользователь не найден. Войдите снова.', 'error')
        return redirect(url_for('login'))
    
    username=user[0]
    cart_items=get_cart_items(session['user_id'])
    balance=get_user_balance(session['user_id'])
    total_cost = sum(int(item[2]) * int(item[3]) for item in cart_items)

    form=PurchaseForm()
    if form.validate_on_submit():
        if total_cost>balance:
            flash('Недостаточно кредитов!!!', 'error')
        else:
            process_purchase(session['user_id'],cart_items,total_cost)
            flash('Покупка успешно совершена!!', 'success')
            return redirect(url_for('profile'))
    return render_template('purchase.html', username=username, cart_items=cart_items, balance=balance,total_cost=total_cost, form=form)

# смена пароля
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user(session['user_id'])
    if user is None:
        session.pop('user_id', None)
        flash('Пользователь не найден. Войдите снова.', 'error')
        return redirect(url_for('login'))
    
    username = user[0]
    form = ChangePasswordForm()
    if request.method == 'POST':
        new_password = form.new_password.data
        new_hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        change_user_password(session['user_id'], new_hashed_password) 
        session.pop('user_id', None)  
        flash('Пароль успешно изменён! Пожалуйста, войдите заново', 'success')
        return redirect(url_for('login'))
    
    return render_template('change_password.html', username=username, form=form)

# перевод денег
@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    sender_id = session['user_id']
    target_username = request.form.get('username')
    amount = int(request.form.get('amount', 0))  
    
    target_user_id = get_user_id_by_username(target_username)
    
    if not target_user_id:
        flash('Пользователь с таким именем не найден!', 'error')
        return redirect(url_for('profile'))
    
    balance = get_user_balance(sender_id)
    if balance >= amount:
        transfer_funds(sender_id, target_user_id, amount)
        flash(f'Переведено {amount} кредитов пользователю {target_username}!', 'success')
    else:
        flash('Недостаточно кредитов!', 'error')
    return redirect(url_for('profile'))

# удаление товара из корзины
@app.route('/remove_from_cart', methods=['POST'])
def handle_remove_from_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form = RemoveFromCartForm() 
    if form.validate_on_submit():
        product_id = int(form.product_id.data)  
        remove_from_cart(session['user_id'], product_id)
        flash('Товар удалён из корзины!', 'success')
    else:
        flash('Ошибка при удалении товара.', 'error')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)