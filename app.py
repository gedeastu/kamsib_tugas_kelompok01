from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "kunci-rahasia-ku"
db = SQLAlchemy(app)

def login_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if "user" not in session:
            return abort(403)
        return f(*args, **kwargs)
    return decorator

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    grade = db.Column(db.String(10))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Cek apakah username sudah ada
        existing = User.query.filter_by(username=username).first()
        if existing:
            return "Username sudah dipakai."

        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user"] = user.username
            return redirect(url_for("index"))

        return "Username atau password salah."

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route('/')
@login_required
def index():
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)

@app.route('/add', methods=['POST'])
@login_required
def add_student():
    name = request.form['name']
    age = request.form['age']
    grade = request.form['grade']

    db.session.execute(
        text("INSERT INTO student (name, age, grade) VALUES (:name, :age, :grade)"),
        {'name': name, 'age': age, 'grade': grade}
    )
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
@login_required
def delete_student(id):
    db.session.execute(text("DELETE FROM student WHERE id=:id"), {'id': id})
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    if request.method == 'POST':
        db.session.execute(
            text("UPDATE student SET name=:name, age=:age, grade=:grade WHERE id=:id"),
            {
                'name': request.form['name'],
                'age': request.form['age'],
                'grade': request.form['grade'],
                'id': id
            }
        )
        db.session.commit()
        return redirect(url_for('index'))

    student = db.session.execute(
        text("SELECT * FROM student WHERE id=:id"),
        {'id': id}
    ).fetchone()

    return render_template('edit.html', student=student)

@app.errorhandler(403)
def forbidden(e):
    return """
    <div style='text-align:center; margin-top:50px; font-family:Arial;'>
        <h1 style='color:red;'>403 - Akses Tidak Diizinkan</h1>
        <p>Anda tidak memiliki izin untuk mengakses halaman ini.</p>
        <a href='/login'>Login</a>
    </div>
    """, 403

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
