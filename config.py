import os
from urllib.parse import urlparse

# Buscamos la URL en Render. Si no existe, usamos la local.
URL_BD = os.environ.get('DATABASE_URL', 'mysql://root:Joseesoto11-@127.0.0.1:3306/motocontrol_db')

# Usamos la herramienta nativa de Python (la misma que funcionó en construir_nube.py)
url = urlparse(URL_BD)

DB_CONFIG = {
    'host': url.hostname,
    'user': url.username,
    'password': url.password,
    'database': url.path[1:],  # El [1:] quita la diagonal '/' del nombre de la base
    'port': url.port
}