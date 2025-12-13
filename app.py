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

@app.route('/')
def index():
    # RAW Query
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)

@app.route('/add', methods=['POST'])
def add_student():
    try:
        name = request.form.get('name', '').strip()
        age_raw = request.form.get('age', '').strip()
        grade = request.form.get('grade', '').strip()

        if not name or not age_raw or not grade:
            return """
            <script>
                alert("Semua field wajib diisi!");
                window.location.href = "/";
            </script>
            """

        if not age_raw.isdigit():
            return """
            <script>
                alert("Age harus berupa angka!");
                window.location.href = "/";
            </script>
            """

        age = int(age_raw)

        if age < 1 or age > 150:
            return """
            <script>
                alert("Age tidak valid!");
                window.location.href = "/";
            </script>
            """

        connection = sqlite3.connect('instance/students.db')
        cursor = connection.cursor()

        query = "INSERT INTO student (name, age, grade) VALUES (:name,:age,:grade)"
        cursor.execute(query, {
            'name': name,
            'age': age,
            'grade': grade
        })

        connection.commit()
        connection.close()

        return """
        <script>
            alert("Data berhasil ditambahkan!");
            window.location.href = "/";
        </script>
        """

    except ValueError:
        return """
        <script>
            alert("Terjadi kesalahan konversi data!");
            window.location.href = "/";
        </script>
        """

    except sqlite3.Error:
        return """
        <script>
            alert("Terjadi kesalahan pada database!");
            window.location.href = "/";
        </script>
        """

    except Exception:
        return """
        <script>
            alert("Terjadi kesalahan pada server!");
            window.location.href = "/";
        </script>
        """

@app.route('/delete/<int:id>') 
def delete_student(id):
    # Menggunakan :id untuk melakukan placeholder terlebih dahulu sebelum melakukan pengiriman ID untuk validasi Penghapusan data
    db.session.execute(text("DELETE FROM student WHERE id=:id"),({'id':id}))
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']
        
        # RAW Query
        # Menambahkan :name, :age, dan :grade untuk memisahkan antara struktur query dan pengiriman datanya jadi untuk menghindari ketika melakukan input dengan menambahkan karakter string yang dapat merusak struktur query dan berpotensi mengubah semua baris data
        # serta menggunakan :id untuk melakukan placeholder terlebih dahulu sebelum melakukan pengiriman ID untuk validasi Pembaharuan data
        db.session.execute(text(f"UPDATE student SET name=:name, age=:age, grade=:grade WHERE id=:id"),({'name': name, 'age': age, 'grade': grade,'id':id}))
        db.session.commit()
        return redirect(url_for('index'))
    else:
        # RAW Query
        student = db.session.execute(text(f"SELECT * FROM student WHERE id=:id"),({'id':id})).fetchone()
        return render_template('edit.html', student=student)

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=6969, debug=True)

