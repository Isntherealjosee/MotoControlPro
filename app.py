respaldo app.py:                                                                                                                                            import requests
import os

# Función para enviar notificaciones
def enviar_telegram(mensaje):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        params = {'chat_id': chat_id, 'text': mensaje}
        try:
            requests.get(url, params=params)
        except Exception as e:
            print(f"Error enviando Telegram: {e}")

import requests # Asegúrate de tener este import arriba

def enviar_telegram(mensaje):
    TOKEN = "TU_TOKEN_DE_BOT_AQUI"
    CHAT_ID = "TU_ID_DE_CHAT_AQUI"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensaje}"
    requests.get(url)

import os
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = 'llave_super_secreta_motocontrol'

# --- CONFIGURACIÓN DE SUBIDA DE IMÁGENES ---
# Le decimos a Flask exactamente dónde guardar las fotos
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Límite de seguridad: Solo permitimos estas extensiones de imagen
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# -------------------------------------------

# --- RUTA 1: INICIO DE SESIÓN (AHORA ES LA RAÍZ DIRECTA) ---
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
            flash('Ese correo ya está registrado. Intenta con otro o inicia sesión.', 'error')
        except mysql.connector.Error as e:
            flash(f'Error de base de datos: {e}', 'error')
        finally:
            if conexion and conexion.is_connected():
                cursor.close()
                conexion.close()

    return render_template('register.html')

# --- RUTA 3: DASHBOARD (PANEL DE CONTROL) ---
@app.route('/dashboard')
def dashboard():
    if 'id_usuario' in session:
        conexion = None
        motos = []
        try:
            conexion = mysql.connector.connect(**DB_CONFIG)
            cursor = conexion.cursor(dictionary=True)
            
            # 1. Traer todas las motos del usuario
            sql = "SELECT * FROM motocicletas WHERE id_usuario = %s"
            cursor.execute(sql, (session['id_usuario'],))
            motos = cursor.fetchall()
            
            # 2. MOTOR DE ALERTAS INTELIGENTE
            for moto in motos:
                moto['alertas'] = []
                
                # Regla A: Cambio de Aceite
                sql_aceite = "SELECT kilometraje_servicio FROM mantenimientos WHERE id_moto = %s AND tipo_servicio = 'Cambio de Aceite' ORDER BY fecha_servicio DESC LIMIT 1"
                cursor.execute(sql_aceite, (moto['id_moto'],))
                ultimo_aceite = cursor.fetchone()
                
                if ultimo_aceite:
                    km_recorridos = moto['kilometraje_actual'] - ultimo_aceite['kilometraje_servicio']
                    if km_recorridos >= 3000:
                        moto['alertas'].append(f'⚠ Urgente: Cambio de aceite vencido (se pasó por {km_recorridos - 3000} km)')
                    elif km_recorridos >= 2500:
                        moto['alertas'].append(f'⚠ Pronto: Cambio de aceite en {3000 - km_recorridos} km')
                else:
                    moto['alertas'].append('⚠ Atención: No hay registro inicial de aceite')

                # Regla B: Cadena
                sql_cadena = "SELECT kilometraje_servicio FROM mantenimientos WHERE id_moto = %s AND tipo_servicio = 'Ajuste y Lubricación de Cadena' ORDER BY fecha_servicio DESC LIMIT 1"
                cursor.execute(sql_cadena, (moto['id_moto'],))
                ultima_cadena = cursor.fetchone()
                
                if ultima_cadena:
                    km_recorridos = moto['kilometraje_actual'] - ultima_cadena['kilometraje_servicio']
                    if km_recorridos >= 1000:
                        moto['alertas'].append('⚠ Recomendado: Toca lubricar cadena')

        except mysql.connector.Error as e:
            flash(f'Error al cargar tus motocicletas: {e}', 'error')
        finally:
            if conexion and conexion.is_connected():
                cursor.close()
                conexion.close()
                
        return render_template('dashboard.html', motos=motos)
    else:
        flash('Por favor, inicia sesión primero.', 'error')
        return redirect(url_for('inicio'))

# --- RUTA: REGISTRAR NUEVA MOTO ---
@app.route('/nueva_moto', methods=['GET', 'POST'])
def nueva_moto():
    if 'id_usuario' not in session:
        flash('Por favor, inicia sesión para registrar motos.', 'error')
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        marca = request.form['marca']
        modelo = request.form['modelo']
        anio = request.form['anio']
        cilindrada = request.form['cilindrada']
        kilometraje = request.form['kilometraje_actual']
        id_usuario = session['id_usuario']

        foto = request.files.get('foto')
        nombre_archivo = 'default.png'

        if foto and foto.filename != '':
            if allowed_file(foto.filename):
                extension = foto.filename.rsplit('.', 1)[1].lower()
                nombre_archivo = f"{uuid.uuid4().hex}.{extension}"
                ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
                foto.save(ruta_guardado)
            else:
                flash('Formato de imagen no permitido. Usa JPG, PNG o WEBP.', 'error')
                return redirect(request.url)

        conexion = None
        try:
            conexion = mysql.connector.connect(**DB_CONFIG)
            cursor = conexion.cursor()

            sql = """
            INSERT INTO motocicletas (id_usuario, marca, modelo, anio, cilindrada, kilometraje_actual, foto_url) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            valores = (id_usuario, marca, modelo, anio, cilindrada, kilometraje, nombre_archivo)
            
            cursor.execute(sql, valores)
            conexion.commit()

            flash('¡Motocicleta registrada exitosamente en tu garaje!', 'success')
            return redirect(url_for('dashboard'))

        except mysql.connector.Error as e:
            flash(f'Error al registrar la motocicleta: {e}', 'error')
        finally:
            if conexion and conexion.is_connected():
                cursor.close()
                conexion.close()

    return render_template('nueva_moto.html')

# --- RUTA: DETALLE DE UNA MOTOCICLETA ---
@app.route('/moto/<int:id_moto>')
def detalle_moto(id_moto):
    if 'id_usuario' not in session:
        flash('Por favor, inicia sesión.', 'error')
        return redirect(url_for('inicio'))

    conexion = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        
        sql_moto = "SELECT * FROM motocicletas WHERE id_moto = %s AND id_usuario = %s"
        cursor.execute(sql_moto, (id_moto, session['id_usuario']))
        moto = cursor.fetchone()
        
        if not moto:
            flash('Motocicleta no encontrada o no tienes permiso para verla.', 'error')
            return redirect(url_for('dashboard'))

        sql_mantenimientos = "SELECT * FROM mantenimientos WHERE id_moto = %s ORDER BY fecha_servicio DESC"
        cursor.execute(sql_mantenimientos, (id_moto,))
        mantenimientos = cursor.fetchall()

        return render_template('moto_detalle.html', moto=moto, mantenimientos=mantenimientos)

    except mysql.connector.Error as e:
        flash(f'Error de base de datos: {e}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()

# --- RUTA: REGISTRAR NUEVO MANTENIMIENTO ---
@app.route('/moto/<int:id_moto>/mantenimiento/nuevo', methods=['GET', 'POST'])
def nuevo_mantenimiento(id_moto):
    if 'id_usuario' not in session:
        flash('Por favor, inicia sesión.', 'error')
        return redirect(url_for('inicio'))

    conexion = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)

        sql_verificar = "SELECT * FROM motocicletas WHERE id_moto = %s AND id_usuario = %s"
        cursor.execute(sql_verificar, (id_moto, session['id_usuario']))
        moto = cursor.fetchone()

        if not moto:
            flash('No tienes permiso para modificar esta moto.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            tipo_servicio = request.form['tipo_servicio']
            fecha_servicio = request.form['fecha_servicio']
            kilometraje_servicio = int(request.form['kilometraje_servicio'])
            costo = float(request.form['costo'])
            notes = request.form['notas']

            sql_insertar = """
            INSERT INTO mantenimientos (id_moto, tipo_servicio, costo, fecha_servicio, kilometraje_servicio, notas) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insertar, (id_moto, tipo_servicio, costo, fecha_servicio, kilometraje_servicio, notes))

            if kilometraje_servicio > moto['kilometraje_actual']:
                sql_actualizar_km = "UPDATE motocicletas SET kilometraje_actual = %s WHERE id_moto = %s"
                cursor.execute(sql_actualizar_km, (kilometraje_servicio, id_moto))

            conexion.commit()
            
            flash('Mantenimiento registrado correctamente.', 'success')
            return redirect(url_for('detalle_moto', id_moto=id_moto))

        return render_template('nuevo_mantenimiento.html', moto=moto)

    except mysql.connector.Error as e:
        flash(f'Error de base de datos: {e}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()

# --- RUTA: ANÁLISIS FINANCIERO ---
@app.route('/finanzas')
def finanzas():
    if 'id_usuario' not in session:
        flash('Por favor, inicia sesión.', 'error')
        return redirect(url_for('inicio'))

    conexion = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT id_moto, marca, modelo, kilometraje_actual FROM motocicletas WHERE id_usuario = %s", (session['id_usuario'],))
        motos = cursor.fetchall()

        estadisticas = None
        datos_grafica = []
        moto_actual = None

        if motos:
            moto_id = request.args.get('moto_id')
            if not moto_id:
                moto_id = motos[0]['id_moto']
            
            moto_actual = next((m for m in motos if str(m['id_moto']) == str(moto_id)), motos[0])

            cursor.execute("SELECT SUM(costo) as total FROM mantenimientos WHERE id_moto = %s", (moto_id,))
            resultado_total = cursor.fetchone()
            total_gastado = resultado_total['total'] if resultado_total['total'] else 0

            costo_por_km = 0
            if moto_actual['kilometraje_actual'] > 0:
                costo_por_km = float(total_gastado) / float(moto_actual['kilometraje_actual'])

            cursor.execute("SELECT tipo_servicio, SUM(costo) as total FROM mantenimientos WHERE id_moto = %s GROUP BY tipo_servicio", (moto_id,))
            datos_crudos = cursor.fetchall()

            datos_grafica = []
            for item in datos_crudos:
                datos_grafica.append({
                    'tipo_servicio': item['tipo_servicio'],
                    'total': float(item['total'])
                })

            estadisticas = {
                'total_gastado': float(total_gastado),
                'costo_por_km': costo_por_km
            }

        return render_template('finanzas.html', motos=motos, moto_actual=moto_actual, estadisticas=estadisticas, datos_grafica=datos_grafica)

    except mysql.connector.Error as e:
        flash(f'Error de base de datos: {e}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()

# --- RUTA 4: CERRAR SESIÓN ---
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)