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

# --- FUNCIÓN TELEGRAM ---
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

# --- CONFIGURACIÓN IMÁGENES ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- RUTAS ---
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
            flash('Correo o contraseña incorrectos.', 'error')
        finally:
            if conexion and conexion.is_connected():
                cursor.close(); conexion.close()
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre, correo, password = request.form['nombre'], request.form['correo'], request.form['password']
        password_encriptada = generate_password_hash(password)
        conexion = None
        try:
            conexion = mysql.connector.connect(**DB_CONFIG)
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO usuarios (nombre, correo, password_hash) VALUES (%s, %s, %s)", (nombre, correo, password_encriptada))
            conexion.commit()
            return redirect(url_for('inicio'))
        finally:
            if conexion and conexion.is_connected():
                cursor.close(); conexion.close()
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'id_usuario' not in session: return redirect(url_for('inicio'))
    conexion = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM motocicletas WHERE id_usuario = %s", (session['id_usuario'],))
        motos = cursor.fetchall()
        return render_template('dashboard.html', motos=motos)
    finally:
        if conexion and conexion.is_connected():
            cursor.close(); conexion.close()

# RUTA FALTANTE QUE CAUSABA EL ERROR
@app.route('/moto/<int:id_moto>')
def detalle_moto(id_moto):
    if 'id_usuario' not in session: return redirect(url_for('inicio'))
    conexion = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM motocicletas WHERE id_moto = %s AND id_usuario = %s", (id_moto, session['id_usuario']))
        moto = cursor.fetchone()
        cursor.execute("SELECT * FROM mantenimientos WHERE id_moto = %s ORDER BY fecha_servicio DESC", (id_moto,))
        mantenimientos = cursor.fetchall()
        return render_template('moto_detalle.html', moto=moto, mantenimientos=mantenimientos)
    finally:
        if conexion and conexion.is_connected():
            cursor.close(); conexion.close()

@app.route('/moto/<int:id_moto>/mantenimiento/nuevo', methods=['GET', 'POST'])
def nuevo_mantenimiento(id_moto):
    if 'id_usuario' not in session: return redirect(url_for('inicio'))
    conexion = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM motocicletas WHERE id_moto = %s AND id_usuario = %s", (id_moto, session['id_usuario']))
        moto = cursor.fetchone()
        if request.method == 'POST':
            tipo_servicio = request.form['tipo_servicio']
            sql = "INSERT INTO mantenimientos (id_moto, tipo_servicio, costo, fecha_servicio, kilometraje_servicio, notas) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (id_moto, tipo_servicio, request.form['costo'], request.form['fecha_servicio'], request.form['kilometraje_servicio'], request.form['notas']))
            conexion.commit()
            enviar_telegram(f"✅ Mantenimiento registrado: {tipo_servicio}")
            return redirect(url_for('detalle_moto', id_moto=id_moto))
        return render_template('nuevo_mantenimiento.html', moto=moto)
    finally:
        if conexion and conexion.is_connected():
            cursor.close(); conexion.close()

@app.route('/finanzas')
def finanzas():
    if 'id_usuario' not in session: return redirect(url_for('inicio'))
    return render_template('finanzas.html') # Simplificado para evitar errores, agrega tu lógica aquí

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)