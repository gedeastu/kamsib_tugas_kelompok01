from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

def alert(message):
    return f"""
    <script>
        alert("{message}");
        window.location.href = "/";
    </script>
    """

@app.route('/')
def index():
    try:
        students = db.session.execute(
            text("SELECT * FROM student")
        ).fetchall()
        return render_template('index.html', students=students)

    except Exception:
        return alert("Gagal memuat data!")

@app.route('/add', methods=['POST'])
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=6969, debug=True)

