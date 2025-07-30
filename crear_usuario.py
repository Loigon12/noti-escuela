# crear_admin.py

from app import app, db, Usuario

with app.app_context():
    # Verificar si ya existe un usuario con username = 'admin'
    existe = Usuario.query.filter_by(username="admin").first()
    
    if existe:
        print("⚠️  Ya existe un usuario con username 'admin'.")
    else:
        # Crear nuevo usuario sin encriptar la contraseña
        nuevo_usuario = Usuario(
            nom_usuario="Admin",
            ape_usuario="General",
            username="admin",
            password="admin123"  # Contraseña en texto plano
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        print("✅ Usuario 'admin' creado con éxito.")
        print(f"🔑 Credenciales: usuario='admin', contraseña='admin123'")