from app import app, db, Usuario

with app.app_context():
    # Verificar si el usuario ya existe
    existe = Usuario.query.filter_by(username="admin").first()
    if existe:
        print("⚠️  Ya existe un usuario admin.")
    else:
        nuevo_usuario = Usuario(
            nom_usuario="Admin",
            ape_usuario="General",
            username="admin",
            password="admin123"
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        print("✅ Usuario admin creado con éxito.")