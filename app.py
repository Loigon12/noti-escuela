from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_admin.menu import MenuLink
from flask_admin.form import ImageUploadField
import os
from wtforms.fields import SelectField
import time
import psycopg2

# Esperar a que PostgreSQL esté listo
def wait_for_postgres():
    while True:
        try:
            conn = psycopg2.connect(
                host="db",
                database="Tienda1",
                user="postgres",
                password="PODIUM2025"
            )
            conn.close()
            print("✅ PostgreSQL está listo")
            break
        except psycopg2.OperationalError:
            print("⏳ Esperando a PostgreSQL...")
            time.sleep(2)

# Crear la app Flask
app = Flask(__name__)
app.secret_key = 'PODIUM2025'

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:PODIUM2025@db/Tienda1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Inicializar SQLAlchemy
db = SQLAlchemy(app)


# ===== DEFINICIÓN DE MODELOS (ÚNICA VEZ, DESPUÉS DE db) =====

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id_categoria = db.Column(db.Integer, primary_key=True)
    nom_categoria = db.Column(db.String(100), nullable=False)
    # Relación: una categoría tiene muchos productos
    productos = db.relationship('Producto', backref='categoria', lazy=True)


class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    imagen = db.Column(db.String(200))
    precio = db.Column(db.Float, nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categoria'), nullable=False)
    # No es necesario definir 'categoria' aquí: lo maneja backref


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_ud_usuario = db.Column(db.Integer, primary_key=True)
    nom_usuario = db.Column(db.String(50), nullable=False)
    ape_usuario = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)


# ===== CONFIGURACIÓN DE ADMIN (Flask-Admin) =====

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('admin_logged_in')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))


class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get('admin_logged_in')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))

    def render(self, template, **kwargs):
        kwargs['logout_button'] = Markup('<a class="btn btn-danger" href="/admin/logout">Cerrar sesión</a>')
        return super().render(template, **kwargs)


class UsuarioAdmin(ModelView):
    form_columns = ['nom_usuario', 'ape_usuario', 'username', 'password']


class ProductoAdmin(ModelView):
    form_extra_fields = {
        'imagen': ImageUploadField('Imagen del producto',
            base_path=os.path.join(os.getcwd(), 'static', 'uploads'),
            relative_path='uploads/',
            url_relative_path='static/uploads/')
    }

    form_overrides = {
        'id_categoria': SelectField
    }

    form_args = {
        'id_categoria': {
            'coerce': int,
            'label': 'Categoría'
        }
    }

    form_columns = ['nombre', 'descripcion', 'imagen', 'precio', 'id_categoria']

    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.id_categoria.choices = [(c.id_categoria, c.nom_categoria) for c in Categoria.query.all()]
        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.id_categoria.choices = [(c.id_categoria, c.nom_categoria) for c in Categoria.query.all()]
        return form


# Inicializar Flask-Admin
admin = Admin(app, name='Panel Admin', template_mode='bootstrap3', index_view=MyAdminIndexView())
admin.add_view(UsuarioAdmin(Usuario, db.session))
admin.add_view(SecureModelView(Categoria, db.session))
admin.add_view(ProductoAdmin(Producto, db.session))
admin.add_link(MenuLink(name='Cerrar sesión', category='', url='/admin/logout'))


# ===== RUTAS =====

@app.route('/status', methods=['GET'])
def service_status():
    return jsonify(message="El servicio funciona correctamente.")

@app.route("/productos", methods=["GET"])
def listar_productos():
    productos = Producto.query.all()
    return jsonify([
        {
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "id_categoria": p.id_categoria,
            "imagen": p.imagen,
            "categoria": p.categoria.nom_categoria if p.categoria else None
        }
        for p in productos
    ])

@app.route("/agregar", methods=["POST"])
def agregar_producto():
    data = request.get_json()
    nuevo = Producto(
        nombre=data["nombre"],
        descripcion=data["descripcion"],
        precio=data["precio"],
        id_categoria=data["id_categoria"]
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"message": "Producto agregado correctamente."}), 201

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/noticias")
def noticias():
    return render_template("reuniones.html")

@app.route("/ingreso")
def ingreso():
    return render_template("ingreso.html")

@app.route("/comunicados")
def comunicados():
    return render_template("comunicados.html")

@app.route("/eventos")
def eventos():
    return render_template("eventos.html")

@app.route('/ventas')
def ventas():
    productos = Producto.query.all()
    return render_template('ventas.html', productos=productos)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username, password=password).first()
        if user:
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            error = 'Usuario o contraseña incorrectos'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


# ===== INICIO DE LA APLICACIÓN =====

if __name__ == '__main__':
    wait_for_postgres()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')