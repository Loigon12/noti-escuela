from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import check_password_hash, generate_password_hash
import os

# Crear la app Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'PODIUM2025')
database_url = os.getenv('DATABASE_URL')
if not database_url:
    # Fallback local
    database_url = 'postgresql://postgres:PODIUM2025@localhost/Tienda1'

# Configura SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Fuerza SSL/TLS (opcional)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'sslmode': 'disable'}
}

db = SQLAlchemy(app)

# Modelos
class Categoria(db.Model):
    __tablename__ = 'categorias'
    id_categoria = db.Column(db.Integer, primary_key=True)
    nom_categoria = db.Column(db.String(100), nullable=False)

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    imagen = db.Column(db.String(200))
    precio = db.Column(db.Float, nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categoria'), nullable=False)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_ud_usuario = db.Column(db.Integer, primary_key=True)
    nom_usuario = db.Column(db.String(50), nullable=False)
    ape_usuario = db.Column(db.String(50), nullable=False)
    pasword = db.Column(db.String(128))  # Asegúrate de usar hashing

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id_ud_usuario)

# Vistas personalizadas del admin protegidas
class MyModelView(ModelView):
    column_list = ("id_ud_usuario", "nom_usuario", "ape_usuario")

    def is_accessible(self):
        return 'user_id' in session  # Solo si está logueado

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

# Inicializar Flask-Admin
admin = Admin(app, name='Panel Admin', template_mode='bootstrap3')
admin.add_view(MyModelView(Usuario, db.session))
admin.add_view(MyModelView(Categoria, db.session))
admin.add_view(MyModelView(Producto, db.session))

# Rutas públicas
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/noticias")
def noticias():
    return render_template("reuniones.html")

@app.route("/ingreso")
def ingreso():
    return render_template("ingreso.html")

@app.route("/eventos")
def eventos():
    return render_template("eventos.html")

# LOGIN / LOGOUT
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(nom_usuario=username).first()
        if user and check_password_hash(user.pasword, password):
            session['user_id'] = user.id_ud_usuario
            return redirect('/admin')
        else:
            flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Ejecutar app
if __name__ == '__main__':
    app.run(debug=True)