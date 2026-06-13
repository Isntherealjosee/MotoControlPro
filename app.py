import os
import uuid
import requests
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = 'llave_super_secreta_motocontrol'

# --- FUNCIÓN TELEGRAM (Única y correcta) ---
def enviar_telegram(mensaje):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        params = {'chat_id': chat_id, 'text': mensaje}
        try:
            requests.get(url, params=params, timeout=5)
        except Exception as e:
            print(f"Error enviando Telegram: {e}")

# --- CONFIGURACIÓN DE SUBIDA DE IMÁGENES ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- RUTA 1: INICIO DE SESIÓN ---
@app.route('/', methods=['GET', 'POST'])
def inicio():
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        conexion = None
        try:
            conexion = mysql.connector.connect(**DB_CONFIG)
            cursor = conexion.cursor(dictionary=True) 
            sql = "SELECT * FROM usuarios WHERE correo = %s"
            cursor.execute(sql, (correo,))
            usuario = cursor.fetchone()
            if usuario and check_password_hash(usuario['password_hash'], password):
                session['id_usuario'] = usuario['id_usuario']
                session['nombre'] = usuario['nombre']
                return redirect(url_for('dashboard'))
            else:
                flash('Correo o contraseña incorrectos.', 'error')
        except mysql.connector.Error as e:
            flash(f'Error de base de datos: {e}', 'error')
        finally:
            if conexion and conexion.is_connected():
                cursor.close()
                conexion.close()
    return render_template('login.html')

# --- RUTA 2: REGISTRO ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']
        password_encriptada = generate_password_hash(password)
        conexion = None
        try:
            conexion = mysql.connector.connect(**DB_CONFIG)
            cursor = conexion.cursor()
            sql = "INSERT INTO usuarios (nombre, correo, password_hash) VALUES (%s, %s, %s)"
            valores = (nombre, correo, password_encriptada)
            cursor.execute(sql, valores)
            conexion.commit()
            flash('¡Cuenta creada con éxito! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('inicio'))
        except mysql.connector.IntegrityError:
            flash('Ese correo ya está registrado.', 'error')
        except mysql.connector.Error as e:
            flash(f'Error de base de datos: {e}', 'error')
        finally:
            if conexion and conexion.is_connected():
                cursor.close()
                conexion.close()
    return render_template('register.html')

# --- RUTA 3: DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'id_usuario' in session:
        conexion = None
        motos = []
        try:
            conexion = mysql.connector.connect(**DB_CONFIG)
            cursor = conexion.cursor(dictionary=True)
            sql = "SELECT * FROM motocicletas WHERE id_usuario = %s"
            cursor.execute(sql, (session['id_usuario'],))
            motos = cursor.fetchall()
            for moto in motos:
                moto['alertas'] = []
                sql_aceite = "SELECT kilometraje_servicio FROM mantenimientos WHERE id_moto = %s AND tipo_servicio = 'Cambio de Aceite' ORDER BY fecha_servicio DESC LIMIT 1"
                cursor.execute(sql_aceite, (moto['id_moto'],))
                ultimo_aceite = cursor.fetchone()
                if ultimo_aceite:
                    km_recorridos = moto['kilometraje_actual'] - ultimo_aceite['kilometraje_servicio']
                    if km_recorridos >= 3000: moto['alertas'].append(f'⚠ Urgente: Cambio de aceite vencido')
                else:
                    moto['alertas'].append('⚠ Atención: No hay registro inicial de aceite')
        except mysql.connector.Error as e:
            flash(f'Error al cargar tus motocicletas: {e}', 'error')
        finally:
            if conexion and conexion.is_connected():
                cursor.close()
                conexion.close()
        return render_template('dashboard.html', motos=motos)
    else:
        return redirect(url_for('inicio'))

# --- RUTA: REGISTRAR NUEVO MANTENIMIENTO (CORREGIDA) ---
@app.route('/moto/<int:id_moto>/mantenimiento/nuevo', methods=['GET', 'POST'])
def nuevo_mantenimiento(id_moto):
    if 'id_usuario' not in session:
        return redirect(url_for('inicio'))

    conexion = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM motocicletas WHERE id_moto = %s AND id_usuario = %s", (id_moto, session['id_usuario']))
        moto = cursor.fetchone()

        if request.method == 'POST':
            tipo_servicio = request.form['tipo_servicio']
            fecha_servicio = request.form['fecha_servicio']
            kilometraje_servicio = int(request.form['kilometraje_servicio'])
            costo = float(request.form['costo'])
            notes = request.form['notas']

            sql_insertar = "INSERT INTO mantenimientos (id_moto, tipo_servicio, costo, fecha_servicio, kilometraje_servicio, notas) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql_insertar, (id_moto, tipo_servicio, costo, fecha_servicio, kilometraje_servicio, notes))
            conexion.commit()
            
            # --- NOTIFICACIÓN TELEGRAM ---
            enviar_telegram(f"✅ Mantenimiento registrado: {tipo_servicio} en {moto['marca']}")
            # -----------------------------
            
            flash('Mantenimiento registrado correctamente.', 'success')
            return redirect(url_for('detalle_moto', id_moto=id_moto))

        return render_template('nuevo_mantenimiento.html', moto=moto)
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)