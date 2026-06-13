import mysql.connector
from config import DB_CONFIG

def crear_tablas():
    conexion = None # Inicializamos la variable vacía por seguridad
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor()

        tabla_usuarios = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            correo VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(tabla_usuarios)

        tabla_motos = """
        CREATE TABLE IF NOT EXISTS motocicletas (
            id_moto INT AUTO_INCREMENT PRIMARY KEY,
            id_usuario INT NOT NULL,
            marca VARCHAR(50) NOT NULL,
            modelo VARCHAR(50) NOT NULL,
            anio INT NOT NULL,
            cilindrada INT NOT NULL,
            kilometraje_actual INT NOT NULL,
            foto_url VARCHAR(255),
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
        )
        """
        cursor.execute(tabla_motos)

        tabla_mantenimientos = """
        CREATE TABLE IF NOT EXISTS mantenimientos (
            id_servicio INT AUTO_INCREMENT PRIMARY KEY,
            id_moto INT NOT NULL,
            tipo_servicio VARCHAR(100) NOT NULL,
            costo DECIMAL(10,2) NOT NULL,
            fecha_servicio DATE NOT NULL,
            kilometraje_servicio INT NOT NULL,
            notas TEXT,
            FOREIGN KEY (id_moto) REFERENCES motocicletas(id_moto) ON DELETE CASCADE
        )
        """
        cursor.execute(tabla_mantenimientos)

        conexion.commit()
        print("¡Éxito! Las tablas de MotoControl Pro se crearon correctamente en la base de datos.")

    except mysql.connector.Error as e:
        print(f"Error detectado en la base de datos: {e}")
    finally:
        # Ahora verificamos de forma segura si la conexión existe antes de cerrarla
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()

if __name__ == '__main__':
    crear_tablas()