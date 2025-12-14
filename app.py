from flask import Flask, render_template, request, redirect, url_for, session, abort # pyright: ignore[reportMissingImports]
from flask_sqlalchemy import SQLAlchemy # type: ignore
from sqlalchemy import text # pyright: ignore[reportMissingImports]
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash # pyright: ignore[reportMissingImports]
import sqlite3
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("SECRET_KEY")
db = SQLAlchemy(app)

def login_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))   
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
    username_error = None
    password_error = None
    username_value = ""
    password_value = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        username_value = username      
        password_value = password      

        user = User.query.filter_by(username=username).first()

        if not user:
            username_error = "Username tidak ditemukan."
        else:
            if not check_password_hash(user.password, password):
                password_error = "Password salah."

        if username_error or password_error:
            return render_template(
                "login.html",
                username_error=username_error,
                password_error=password_error,
                username_value=username_value,
                password_value=password_value
            )

        session["user"] = user.username
        return redirect(url_for("index"))

    return render_template(
        "login.html",
        username_error=username_error,
        password_error=password_error,
        username_value=username_value,
        password_value=password_value
    )

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

def alert(message):
    return f"""
    <script>
        alert("{message}");
        window.location.href = "/";
    </script>
    """

@app.route('/')
@login_required
def index():
    try:
        students = db.session.execute(
            text("SELECT * FROM student")
        ).fetchall()
        return render_template('index.html', students=students)

    except Exception:
        return alert("Gagal memuat data!")

@app.route('/add', methods=['POST'])
@login_required
def add_student():
    connection = None
    try:
        name = request.form.get('name', '').strip()
        age_raw = request.form.get('age', '').strip()
        grade = request.form.get('grade', '').strip()

        if not name or not age_raw or not grade:
            return alert("Semua field wajib diisi!")

        if not age_raw.isdigit():
            return alert("Age harus berupa angka!")

        age = int(age_raw)

        if age < 1 or age > 150:
            return alert("Age tidak valid!")

        connection = sqlite3.connect('instance/students.db')
        cursor = connection.cursor()

        query = """
            INSERT INTO student (name, age, grade)
            VALUES (:name, :age, :grade)
        """
        cursor.execute(query, {
            'name': name,
            'age': age,
            'grade': grade
        })

        connection.commit()
        return alert("Data berhasil ditambahkan!")

    except ValueError:
        return alert("Kesalahan konversi data!")

    except sqlite3.Error:
        return alert("Kesalahan pada database!")

    except Exception:
        return alert("Kesalahan pada server!")

    finally:
        if connection:
            connection.close()

@app.route('/delete/<int:id>')
@login_required
def delete_student(id):
    try:
        db.session.execute(
            text("DELETE FROM student WHERE id = :id"),
            {'id': id}
        )
        db.session.commit()
        return redirect(url_for('index'))

    except Exception:
        db.session.rollback()
        return alert("Gagal menghapus data!")

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    try:
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            age_raw = request.form.get('age', '').strip()
            grade = request.form.get('grade', '').strip()

            if not name or not age_raw or not grade:
                return alert("Semua field wajib diisi!")

            if not age_raw.isdigit():
                return alert("Age harus berupa angka!")

            age = int(age_raw)

            if age < 1 or age > 150:
                return alert("Age tidak valid!")

            db.session.execute(
                text("""
                    UPDATE student
                    SET name = :name, age = :age, grade = :grade
                    WHERE id = :id
                """),
                {
                    'name': name,
                    'age': age,
                    'grade': grade,
                    'id': id
                }
            )
            db.session.commit()
            return redirect(url_for('index'))

        else:
            student = db.session.execute(
                text("SELECT * FROM student WHERE id = :id"),
                {'id': id}
            ).fetchone()

            if not student:
                return alert("Data tidak ditemukan!")

            return render_template('edit.html', student=student)

    except Exception:
        db.session.rollback()
        return alert("Terjadi kesalahan saat edit data!")

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
    app.run(host='0.0.0.0', port=5040, debug=True)

