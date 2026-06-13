import mysql.connector
from config import DB_CONFIG

try:
    # Nos conectamos a tu base de datos
    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()
    
    # Agregamos la columna 'foto_url'. Si no suben foto, se asignará 'default.png'
    cursor.execute("ALTER TABLE motocicletas ADD COLUMN foto_url VARCHAR(255) DEFAULT 'default.png'")
    print("✅ ¡Éxito! Columna 'foto_url' agregada a la base de datos.")
    
except mysql.connector.Error as err:
    # Si la columna ya existía o hay otro error, nos avisará sin romper nada
    print(f"Nota de la Base de Datos: {err}")
finally:
    if 'conexion' in locals() and conexion.is_connected():
        cursor.close()
        conexion.close()