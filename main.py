from flask import Flask, redirect, render_template, request
from flask_login import login_user, LoginManager, current_user, login_required, UserMixin
from random import choices
from os import environ
from dotenv import load_dotenv

import psycopg2
from psycopg2 import sql


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

schema_obj = open('schema.sql', 'r')
schema = schema_obj.read()
print(schema)
schema_obj.close()


def preload_db():
    conn = psycopg2.connect(database='postgres',
                            user='postgres',
                            host='localhost',
                            password='12345678',
                            port='5432')
    cursor = conn.cursor()
    conn.autocommit = True
    cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', ('slotmachine',))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute(sql.SQL(
            'CREATE DATABASE {} WITH OWNER = %s ENCODING = %s LOCALE_PROVIDER = %s CONNECTION LIMIT = %s'
        ).format(sql.Identifier('slotmachine')),
            ('postgres', 'UTF8', 'libc', -1)
        )
    conn.commit()


load_dotenv()
preload_db()

DATABASE_UR = environ.get('DATABASE_URL')
POSTGRES_USE = environ.get('POSTGRES_USER')
POSTGRES_PASSWOR = environ.get('POSTGRES_PASSWORD')
POSTGRES_D = environ.get('POSTGRES_DB')
POSTGRES_POR = environ.get('POSTGRES_PORT')
POSTGRES_HOS = environ.get('POSTGRES_HOST')
print(POSTGRES_PASSWOR)
conn = psycopg2.connect(database=POSTGRES_D,
                        user=POSTGRES_USE,
                        host=POSTGRES_HOS,
                        password=POSTGRES_PASSWOR
                        )
# conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute(schema)


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
            cur.execute("INSERT INTO users (name, password) VALUES (%s, %s) RETURNING id",
                        (username, password))
            new_user_id = cur.fetchone()[0]
            conn.commit()
            cur.execute("SELECT id, name, password, balance FROM users WHERE id = %s", (new_user_id,))
            new_user_data = cur.fetchone()
            new_user = User(*new_user_data)
            login_user(new_user)
            return redirect('/')
    else:
        return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return f'Hello, {current_user.username}! Your balance is {current_user.balance}.'


if __name__ == '__main__':
    app.run(port=5000)
