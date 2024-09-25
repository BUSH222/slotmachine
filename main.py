from flask import Blueprint, Flask, redirect, render_template, request, url_for
from flask_login import login_user, LoginManager, current_user, login_required, UserMixin
from random import sample
import psycopg2


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

conn = psycopg2.connect(database='slotmachine',
                        user='postgres',
                        host='localhost',
                        password='12345678',
                        port=5432)
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



@app.route("/")
def index():
    return render_template('main.html')


@app.route('/spin')
def spin():
    symbols = {'🚅': 1, '🔐': 2, '🕌': 3, '🔥': 5, '🤗': 7, '🚆': 10, '🐞': 15, '🐘': 20, '💧': 50}
    result = sample(list(symbols.keys()), 3)
    max_symbol = max(set(result), key=result.count)
    max_cnt = list(symbols.keys()).count(max_symbol)
    return max_symbol + str(max_cnt)



class User(UserMixin):
    def __init__(self, id, username, password, balance):
        self.id = id
        self.username = username
        self.password = password
        self.balance = balance

@login_manager.user_loader
def load_user(user_id):
    cur.execute("SELECT id, username, password, balance FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    if user_data:
        return User(*user_data)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        balance = request.form['balance']
        cur.execute("SELECT id, username, password, balance FROM users WHERE username = %s", (username,))
        user_data = cur.fetchone()
        if user_data and user_data[2] == password:
            user = User(*user_data)
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return f'Hello, {current_user.username}! Your balance is {current_user.balance}.'

    
if __name__ == '__main__':
    preload_db()
    app.run(host='0.0.0.0', port=8000, debug=True)
