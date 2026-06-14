import os
from urllib.parse import urlparse

# 1. Buscamos la URL segura en las variables de entorno de Render
URL_BD = os.environ.get('DATABASE_URL')

# 2. Si no la encuentra (ej. si pruebas en tu computadora), usa credenciales falsas/genéricas
# de esta forma el código no truena, pero tampoco expones claves reales en GitHub.
if not URL_BD:
    URL_BD = 'mysql://usuario_local:clave_falsa123@127.0.0.1:3306/motocontrol_db'

# Usamos la herramienta nativa de Python para separar los datos
url = urlparse(URL_BD)

DB_CONFIG = {
    'host': url.hostname,
    'user': url.username,
    'password': url.password,
    'database': url.path[1:],  # Quita la diagonal inicial
    'port': url.port
}