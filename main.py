from flask import Flask, redirect, render_template, request, url_for
from flask_login import login_user, LoginManager, current_user, login_required, UserMixin
from random import choices
import os
import psycopg2


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

DATABASE_URL = os.getenv('DATABASE_URL')
# conn = psycopg2.connect(database='slotmachine',
#                         user='postgres',
#                         host='postgres',
#                         password='12345678',
#                         port=5432)
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

schema_obj = open('schema.sql', 'r')
schema = schema_obj.read()
schema_obj.close()


def preload_db():
    cur.execute(schema)
    conn.commit()
    cur.execute('SELECT * FROM users')
    print(cur.fetchall())
    print('done')


def update_balance(suser, updated):
    suser.balance += updated
    cur.execute('UPDATE users SET balance = %s WHERE id = %s', (suser.balance, suser.id))
    conn.commit()


@app.route('/')
@login_required
def spin():
    bet = 0
    symbols = {'🚅': 1, '🔐': 2, '🕌': 3, '🔥': 5, '🤗': 7, '🚆': 10, '🐞': 15, '🐘': 20, '💧': 50}
    result = choices(list(symbols.keys()), k=3)
    max_symbol = max(set(result), key=result.count)
    max_cnt = list(result).count(max_symbol)
    if max_cnt == 1:
        bet = 0
    elif max_cnt == 2:
        bet = symbols[max_symbol]
    elif max_cnt == 3:
        bet = symbols[max_symbol]*3
    update_balance(current_user, bet-10)
    data = {'emoji1': result[0], 'emoji2': result[1], 'emoji3': result[2], 'balance': current_user.balance}
    return render_template("main.html", data=data)


class User(UserMixin):
    def __init__(self, id, username, password, balance):
        self.id = id
        self.username = username
        self.password = password
        self.balance = balance


@login_manager.user_loader
def load_user(user_id):
    cur.execute("SELECT id, name, password, balance FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    if user_data:
        return User(*user_data)
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur.execute("SELECT id, name, password, balance FROM users WHERE name = %s", (username,))
        user_data = cur.fetchone()
        if user_data:
            if user_data[2] == password and len(password) < 32:
                user = User(*user_data)
                login_user(user)
                return redirect('/')
            else:
                print("bruh")
        else:
            cur.execute("SELECT MAX(id) FROM users")
            maxid = int(cur.fetchone()[0])
            cur.execute("INSERT INTO users (id, name, password) VALUES (%s, %s, %s) RETURNING id",
                        (maxid+1, username, password))
            new_user_id = cur.fetchone()[0]
            conn.commit()
            cur.execute("SELECT id, name, password, balance FROM users WHERE id = %s", (new_user_id,))
            new_user_data = cur.fetchone()
            new_user = User(*new_user_data)
            login_user(new_user)
            return redirect('/')
    else:
        return render_template('login.html')


# @app.route('/dashboard')
# @login_required
# def dashboard():
#     return f'Hello, {current_user.username}! Your balance is {current_user.balance}.'


if __name__ == '__main__':
    preload_db()
    app.run(host='0.0.0.0', port=8000, debug=True)
