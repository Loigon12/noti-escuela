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

# Conexión con PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:PODIUM2025@db/Tienda1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
# Inicializar SQLAlchemy directamente
db = SQLAlchemy(app)

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('admin_logged_in')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))

# Vista protegida para cada modelo
class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get('admin_logged_in')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))
    def render(self, template, **kwargs):
        # Agrega el botón de logout en la esquina superior derecha
        kwargs['logout_button'] = Markup('<a class="btn btn-danger" href="/admin/logout">Cerrar sesión</a>')
        return super().render(template, **kwargs)

# Modelos
class UsuarioAdmin(ModelView):
    form_columns = ['nom_usuario', 'ape_usuario', 'username', 'password']
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
    categoria = db.relationship('Categoria', backref='productos')

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_ud_usuario = db.Column(db.Integer, primary_key=True)
    nom_usuario = db.Column(db.String(50), nullable=False)
    ape_usuario = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)  # usuario de login
    password = db.Column(db.String(128), nullable=False)
    
class ProductoAdmin(ModelView):
    # Personaliza el campo imagen para que permita subir archivos
    form_extra_fields = {
        'imagen': ImageUploadField('Imagen del producto',
            base_path=os.path.join(os.getcwd(), 'static', 'uploads'),
            relative_path='uploads/',
            url_relative_path='static/uploads/')
    }
    form_overrides = {
        'id_categoria': SelectField
    }

    form_columns = ['nombre', 'descripcion', 'imagen', 'precio', 'id_categoria']

    # Sobrescribimos el tipo de campo
    form_overrides = {
        'id_categoria': SelectField
    }

    # Configuramos el comportamiento del SelectField
    form_args = {
        'id_categoria': {
            'coerce': int,
            'label': 'Categoría'
        }
    }

    # Llenamos las opciones para el campo select (crear)
    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.id_categoria.choices = [(c.id_categoria, c.nom_categoria) for c in Categoria.query.all()]
        return form

    # Llenamos las opciones para el campo select (editar)
    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.id_categoria.choices = [(c.id_categoria, c.nom_categoria) for c in Categoria.query.all()]
        return form

# Flask-Admin
admin = Admin(app, name='Panel Admin', template_mode='bootstrap3', index_view=MyAdminIndexView())
admin.add_view(UsuarioAdmin(Usuario, db.session))
admin.add_view(SecureModelView(Categoria, db.session))
admin.add_view(ProductoAdmin(Producto, db.session))
admin.add_link(MenuLink(name='Cerrar sesión', category='', url='/admin/logout'))

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
            "precio": p.precio
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

@app.route("/eventos")
def eventos():
    return render_template("eventos.html")

@app.route('/ventas')
def ventas():
    productos = Producto.query.all()
    return render_template('ventas.html', productos=productos)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error= None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Usuario.query.filter_by(username=username, password=password).first()

        if user:
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            error= 'Usuario o contraseña incorrectos'
    
    return render_template('admin_login.html')
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


    
if __name__ == '__main__':
    wait_for_postgres()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')