from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
from datetime import datetime
import threading
import time
import base64
import os
import atexit

# Initialize Flask app
app = Flask(__name__)

app.config['ESP32_LAST_READ'] = {'rfid_id': None, 'timestamp': None}
CORS(app)  # Enable CORS for all routes

# Definindo credenciais admin
ADMIN_USERNAME = ""
ADMIN_PASSWORD = ""

# Initialize RFID reader
try:
    reader = SimpleMFRC522()
    print("Leitor RFID iniciado com sucesso!")
except Exception as e:
    print(f"Erro ao iniciar leitor RFID: {str(e)}")

# GPIO setup
RELAY_PIN = 18
try:
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Começa com a porta trancada
    print("GPIO configurado com sucesso!")
except Exception as e:
    print(f"Erro ao configurar GPIO: {str(e)}")

def cleanup_gpio():
    try:
        GPIO.cleanup()
        print("GPIO cleanup realizado com sucesso!")
    except Exception as e:
        print(f"Erro no GPIO cleanup: {str(e)}")

atexit.register(cleanup_gpio)

# Database setup
def init_db():
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lab_access.db')
        print(f"Iniciando banco de dados em: {db_path}")
        
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (rfid_id TEXT PRIMARY KEY, name TEXT, authorized BOOLEAN)''')
        
        # Access logs table
        c.execute('''CREATE TABLE IF NOT EXISTS access_logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      rfid_id TEXT,
                      timestamp DATETIME,
                      action TEXT,
                      FOREIGN KEY (rfid_id) REFERENCES users(rfid_id))''')
        
        conn.commit()
        conn.close()
        print("Banco de dados iniciado com sucesso!")
    except Exception as e:
        print(f"Erro ao iniciar banco de dados: {str(e)}")

def get_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lab_access.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# RFID reading function
def read_rfid():
    while True:
        try:
            print("Aguardando cartão RFID...")
            id, text = reader.read()
            print(f"Cartão lido: {id}")
            handle_access(str(id))
            time.sleep(0.5)  # Pequeno delay para evitar leituras múltiplas
        except Exception as e:
            print(f"Erro na leitura RFID: {str(e)}")
            time.sleep(1)

def handle_access(rfid_id):
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Verifica se o user está autorizado
        c.execute('SELECT * FROM users WHERE rfid_id = ? AND authorized = 1', (rfid_id,))
        user = c.fetchone()
        
        if user:
            print(f"user autorizado: {user['name']}")
            # Verifica se o user já está no laboratório
            c.execute('''SELECT action FROM access_logs 
                        WHERE rfid_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1''', (rfid_id,))
            last_action = c.fetchone()
            
            # Determina se é entrada ou saída
            action = 'exit' if last_action and last_action['action'] == 'entry' else 'entry'
            
            # Registra o acesso
            c.execute('''INSERT INTO access_logs (rfid_id, timestamp, action)
                        VALUES (?, ?, ?)''', (rfid_id, datetime.now(), action))
            
            # Controla a porta
            print("Abrindo fechadura...")
            GPIO.output(RELAY_PIN, GPIO.LOW)  # Destrava
            time.sleep(3)  # Mantém destravado por 3 segundos
            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Trava
            print("Fechadura fechada")
            
            conn.commit()
            print(f"Acesso registrado: {action}")
        else:
            print(f"Acesso negado para RFID: {rfid_id}")
            
        conn.close()
    except Exception as e:
        print(f"Erro no handle_access: {str(e)}")

# Web Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_user')
def add_user():
    try:
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return Response('Login necessário', 401,
                          {'WWW-Authenticate': 'Basic realm="Login Obrigatório"'})
        return render_template('add_user.html')
    except Exception as e:
        print(f"Erro na rota add_user: {str(e)}")
        return Response('Erro interno do servidor', 500)

@app.route('/api/check_name', methods=['POST'])
def check_name():
    auth = request.authorization
    if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('SELECT COUNT(*) FROM users WHERE name = ?', (data['name'],))
        count = c.fetchone()[0]
        name_exists = count > 0
        conn.close()
        return jsonify({
            'exists': name_exists,
            'message': 'Nome já está em uso' if name_exists else 'Nome disponível'
        })
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/add_user', methods=['POST'])
def add_new_user():
    auth = request.authorization
    if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    try:
        # First check if name exists
        c.execute('SELECT COUNT(*) FROM users WHERE name = ?', (data['name'],))
        if c.fetchone()[0] > 0:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Nome já está em uso. Por favor, escolha um nome diferente.'
            })

        # If name doesn't exist, proceed with insert
        c.execute('INSERT INTO users (rfid_id, name, authorized) VALUES (?, ?, ?)',
                 (data['rfid_id'], data['name'], True))
        conn.commit()
        success = True
        message = "user adicionado com sucesso"
    except sqlite3.IntegrityError:
        success = False
        message = "ID RFID já existe"
    except Exception as e:
        success = False
        message = str(e)
    
    conn.close()
    return jsonify({'success': success, 'message': message})

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    auth = request.authorization
    if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('DELETE FROM users WHERE rfid_id = ?', (data['rfid_id'],))
        conn.commit()
        success = True
        message = "user eliminar com sucesso"
    except:
        success = False
        message = "Erro ao eliminar user"
    
    conn.close()
    return jsonify({'success': success, 'message': message})

@app.route('/api/current_status')
def get_current_status():
    conn = get_db()
    c = conn.cursor()
    
    # Get people currently in the lab - only their names if their last action was entry
    c.execute('''
        WITH LatestActions AS (
            SELECT 
                rfid_id,
                action,
                ROW_NUMBER() OVER (PARTITION BY rfid_id ORDER BY timestamp DESC) as rn
            FROM access_logs
        )
        SELECT DISTINCT u.name
        FROM users u
        JOIN access_logs al ON u.rfid_id = al.rfid_id
        WHERE al.rfid_id IN (
            SELECT rfid_id 
            FROM LatestActions 
            WHERE rn = 1 AND action = 'entry'
        )
    ''')
    
    present = [{'name': row['name']} for row in c.fetchall()]
    
    # Get recent access logs
    c.execute('''
        SELECT u.name, al.timestamp, al.action 
        FROM users u
        JOIN access_logs al ON u.rfid_id = al.rfid_id
        ORDER BY al.timestamp DESC
        LIMIT 10
    ''')
    
    all_access = [{'name': row['name'], 'timestamp': row['timestamp'], 'action': row['action']} 
                 for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        'present': present,
        'all_access': all_access,
        'count': len(present)
    })

# New route to handle ESP32 RFID reads
@app.route('/api/esp32_rfid', methods=['GET', 'POST'])
def esp32_rfid():
    if request.method == 'GET':
        return jsonify({'status': 'Server is running'})
        
    data = request.json
    if 'rfid_id' in data:
        app.config['ESP32_LAST_READ'] = {
            'rfid_id': data['rfid_id'],
            'timestamp': datetime.now()
        }
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'No RFID ID provided'}), 400

# Read tags for the add_user page
@app.route('/api/read_rfid')
def read_rfid_once():
    try:
        last_read = app.config['ESP32_LAST_READ']
        current_time = datetime.now()
        
        # Check if we have a recent read (within last 5 seconds)
        if (last_read['rfid_id'] is not None and 
            last_read['timestamp'] is not None and 
            (current_time - last_read['timestamp']).total_seconds() < 5):
            
            # Clear the read after returning it
            rfid_id = last_read['rfid_id']
            app.config['ESP32_LAST_READ'] = {'rfid_id': None, 'timestamp': None}
            return jsonify({'rfid_id': rfid_id})
            
        return jsonify({'rfid_id': None})
    except Exception as e:
        print(f"Error reading RFID: {str(e)}")
        return jsonify({'rfid_id': None})

# Inicialize o banco de dados antes de qualquer outra coisa
init_db()

if __name__ == '__main__':
    # Start RFID reading in a separate thread
    rfid_thread = threading.Thread(target=read_rfid, daemon=True)
    rfid_thread.start()
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)
else:
    # Quando executado pelo gunicorn
    print("Iniciando aplicação via Gunicorn")
    # Inicia a thread de leitura RFID
    rfid_thread = threading.Thread(target=read_rfid, daemon=True)
    rfid_thread.start()
    print("Thread RFID iniciada")