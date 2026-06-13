import mysql.connector

# Pega aquí tu URL PÚBLICA de Railway entre las comillas
URL_NUBE = "mysql://root:ZbpDWYjImPiDjtBwXcoipGrXkHWkWfOh@thomas.proxy.rlwy.net:35962/railway"

# Extraemos los datos de la URL para conectarnos
from urllib.parse import urlparse
url = urlparse(URL_NUBE)

config = {
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'database': url.path[1:], 
    'port': url.port
}

try:
    conexion = mysql.connector.connect(**config)
    cursor = conexion.cursor()

    # 1. Tabla de Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        correo VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL
    )""")

    # 2. Tabla de Motocicletas (Con el campo de foto incluido)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS motocicletas (
        id_moto INT AUTO_INCREMENT PRIMARY KEY,
        id_usuario INT NOT NULL,
        marca VARCHAR(50) NOT NULL,
        modelo VARCHAR(50) NOT NULL,
        anio INT NOT NULL,
        cilindrada INT NOT NULL,
        kilometraje_actual INT NOT NULL,
        foto_url VARCHAR(255) DEFAULT 'default.png',
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    )""")

    # 3. Tabla de Mantenimientos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mantenimientos (
        id_mantenimiento INT AUTO_INCREMENT PRIMARY KEY,
        id_moto INT NOT NULL,
        tipo_servicio VARCHAR(100) NOT NULL,
        costo DECIMAL(10,2) NOT NULL,
        fecha_servicio DATE NOT NULL,
        kilometraje_servicio INT NOT NULL,
        notas TEXT,
        FOREIGN KEY (id_moto) REFERENCES motocicletas(id_moto)
    )""")

    print("✅ ¡Éxito! Las tablas se construyeron perfectamente en la nube de Railway.")

except mysql.connector.Error as err:
    print(f"Error de base de datos: {err}")
finally:
    if 'conexion' in locals() and conexion.is_connected():
        cursor.close()
        conexion.close()