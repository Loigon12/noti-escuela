from app import app, db, Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()  # Esto crea las tablas si no existen

    # Crear un usuario admin si no existe
    if not Usuario.query.first():
        admin = Usuario(
            nom_usuario='admin',
            ape_usuario='Admin',
            pasword=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        print("Usuario admin creado.")
    else:
        print("Ya existe un usuario.")