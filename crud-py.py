
from flask import Flask, flash, render_template, request, redirect, url_for, session
import mysql.connector
import bcrypt
import datetime

app = Flask(__name__)
app.secret_key = 'vocacao-key'

# Configurações do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': ' resgistro'
}

# Rotas relacionadas ao Login
@app.route('/')
def login():
    return render_template('login.html', registros=[])

@app.route('/registro_de_login.html', methods=['GET', 'POST'])
def registro_de_login():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        senha_encoded = senha.encode('utf-8')
        
        salt = bcrypt.gensalt(8)
        hashed_password = bcrypt.hashpw(senha_encoded, salt)

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO user (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, hashed_password))
        conn.commit()

        cursor.close()
        conn.close()
    return render_template('registro_de_login.html')

def verificar_credenciais(nome, email, senha):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT senha FROM user WHERE nome = %s AND email = %s", (nome, email))
        user = cursor.fetchone()

        if user:
            hashed_password_from_db = user.get('senha').encode('utf-8')

            if bcrypt.checkpw(senha.encode('utf-8'), hashed_password_from_db):
                return True

    finally:
        for _ in cursor:
            pass  
        cursor.close()
        conn.close()

    return False

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def fazer_login():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        if verificar_credenciais(nome, email, senha):
            session['logged_in'] = True
            session['username'] = nome
            session['last_active'] = datetime.datetime.now(datetime.timezone.utc)

            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('pagina_inicial'))
        else:
            flash('Credenciais inválidas. Tente novamente.', 'error')

    return render_template('login.html')



@app.route('/pagina_inicial')
def pagina_inicial():
    if 'logged_in' in session:
        current_time = datetime.datetime.now(datetime.timezone.utc)

        if (current_time - session['last_active']).seconds > 180:
            session.clear()  
            flash('Sessão expirada. Faça login novamente.', 'info')
            return redirect(url_for('login'))

        return render_template('pagina_inicial.html', username=session['username'])
    else:
        flash('Faça login para acessar esta página.', 'info')
        return redirect(url_for('login'))

# Funções de Registro

# Rota para adicionar um novo registro
@app.route('/adicionar_registro', methods=['GET', 'POST'])
def adicionar_registro():
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO registros (nome, idade) VALUES (%s, %s)", (nome, idade))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('exibir_registros'))

    return render_template('adicionar_registro.html')

# Rota para exibir registros
@app.route('/exibir_registros')
def exibir_registros():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM registros")
    registros = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('exibir_registros.html', registros=registros)

# Rota para deletar registro
@app.route('/deletar_registro/<int:id>', methods=['POST'])
def deletar_registro(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM registros WHERE id = %s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash('Registro deletado com sucesso!', 'success')
    return redirect(url_for('exibir_registros'))

# Rota para editar registro
@app.route('/editar_registro/<int:id>', methods=['GET', 'POST'])
def editar_registro(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']

        cursor.execute("UPDATE registros SET nome = %s, idade = %s WHERE id = %s", (nome, idade, id))
        conn.commit()

        flash('Registro editado com sucesso!', 'success')
        return redirect(url_for('exibir_registros'))

    cursor.execute("SELECT * FROM registros WHERE id = %s", (id,))
    registro = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('editar_registro.html', registro=registro)

if __name__ == '__main__':
    app.run(debug=True)

