from flask import Flask, render_template, request
from flask import redirect, url_for, flash, session
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError


# Configuração da estrutura do Flask para renderizar páginas
app = Flask(
    __name__,
    static_folder='assets',
    static_url_path='/assets',
    template_folder='templates'
)


# Configuração com o banco de dados
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:root@localhost:3306/agendalab?charset=utf8mb4'
)
db = SQLAlchemy(app)


# 0 - Criação do modelo de dados para conexão com o banco de dados
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    senha = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False, server_default='usuario')
    criado_em = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    reservas = db.relationship('Reserva', backref='usuario', lazy=True)


# Modelo para a tabela Ambiente
class Ambiente(db.Model):
    __tablename__ = 'ambientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, server_default='1')
    criado_em = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    reservas = db.relationship('Reserva', backref='ambiente', lazy=True)


# Modelo para a tabela Reserva
class Reserva(db.Model):
    __tablename__ = 'reservas'
    id = db.Column(db.Integer, primary_key=True)
    ambiente_id = db.Column(db.Integer, db.ForeignKey('ambientes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    inicio = db.Column(db.Time, nullable=False)
    fim = db.Column(db.Time, nullable=False)
    turma = db.Column(db.String(60))
    status = db.Column(db.String(20), nullable=False, server_default='ativa')
    criado_em = db.Column(db.DateTime, server_default=func.now(), nullable=False)


# 1 - Rota principal que abrea página index.html (Formulário de login e cadastro)
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


# 3 - Rota que abre o painel principal após o login ser realizado
@app.route('/home')
def home():
    return render_template('home.html')

# 7 - Rota que exibe a rota do dashboard a partir do login do usuário
@app.route('/dashboard')
def dashboard():
    current_user = None
    if session.get('usuario_id'):
        current_user = Usuario.query.get(session['usuario_id'])
    ambientes = Ambiente.query.order_by(Ambiente.nome.asc()).all()
    return render_template('dashboard.html', current_user=current_user, ambientes=ambientes)


# 8 - Rota que exibe o painel de reservas
@app.route('/painel')
def painel():
    return render_template('painel.html')


# 9 - Rota que exibe o painel de admin
@app.route('/admin')
def admin():
    return render_template('admin.html')


# 6 - Rota para listagem de usuários
@app.route('/usuarios')
def usuarios_page():
    users = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return render_template('usuarios.html', users=users)


# 10 - Rota que lista os ambientes cadastrados
@app.route('/ambientes')
def ambientes_page():
    ambientes = Ambiente.query.order_by(Ambiente.nome.asc()).all()
    return render_template('ambientes.html', ambientes=ambientes)


# 11 - Rota que recebe os dados do ambiente (Formulário de cadastro de ambiente)
@app.route('/ambientes/cadastrar', methods=['POST'])
def cadastrar_ambiente():
    nome = (request.form.get('nome') or '').strip()
    capacidade_raw = (request.form.get('capacidade') or '').strip()
    ativo_flag = request.form.get('ativo')

    # Validação se o nome ou a capacidade foram informados
    if not nome or not capacidade_raw:
        flash('Informe nome e capacidade', 'warning')
        return redirect(url_for('ambientes_page'))

    try:
        capacidade = int(capacidade_raw)
    except ValueError:
        flash('Capacidade deve ser um número inteiro', 'warning')
        return redirect(url_for('ambientes_page'))

    # Valida se a capacidade do laboratório é menor que 0
    if capacidade <= 0:
        flash('Capacidade deve ser maior que zero', 'warning')
        return redirect(url_for('ambientes_page'))

    try:
        a = Ambiente(
            nome=nome,
            capacidade=capacidade,
            ativo=bool(ativo_flag)
        )
        db.session.add(a)
        db.session.commit()
        flash('Ambiente cadastrado com sucesso!', 'success')
        return redirect(url_for('ambientes_page'))
    except IntegrityError:
        db.session.rollback()
        flash('Nome de ambiente já cadastrado', 'danger')
        return redirect(url_for('ambientes_page'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cadastrar ambiente: {str(e)}', 'danger')
        return redirect(url_for('ambientes_page'))

# 5 - Rota que recebe os dados do cadastro e armazena no banco de dados
@app.route('/usuarios/cadastrar', methods=['POST'])
def form_create_usuario():
    nome = (request.form.get('nome') or '').strip()
    email = (request.form.get('email') or '').strip()
    telefone = (request.form.get('telefone') or '').strip()
    login = (request.form.get('login') or '').strip()
    senha = (request.form.get('senha') or '').strip()
    role = 'usuario'

    # Verifica se o login ou o nome estão em branco
    if not login or not nome:
        flash('Campos obrigatórios: login e nome', 'warning')
        return redirect(url_for('index'))

    # Verifica se a senha foi informada para o cadastro
    if not senha:
        flash('Informe uma senha para cadastrar', 'warning')
        return redirect(url_for('index'))

    # Pega as variáveis e adiciona um novo usuário na tabela
    try:
        u = Usuario(
            login=login,
            nome=nome,
            email=email or None,
            telefone=telefone or None,
            role=role,
            senha=senha
        )
        db.session.add(u)
        db.session.commit()
        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('index'))
    
    except IntegrityError:
        db.session.rollback()
        flash('Login já cadastrado', 'danger')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cadastrar: {str(e)}', 'danger')
        return redirect(url_for('index'))

# 2 - Rota que autentica o login usuário (Recebe os dados de um fomrulário HTML)
@app.route('/login', methods=['POST'])
def login():
    login = (request.form.get('login') or '').strip()
    senha = (request.form.get('senha') or '')

    # Validação para verificar seo login foi digitado
    if not login or not senha:
        flash('Informe login e senha', 'warning')
        return redirect(url_for('index'))
    
    # Analise no banco para ver se login e senha estão na mesma linha
    user = Usuario.query.filter_by(login=login).first()
    # Cria a sessão para o usuário informado
    session['usuario_id'] = user.id
    flash(f'Bem-vindo(a), {user.nome}!', 'success')
    return redirect(url_for('home'))


# 4 - Rota que realiza o logout do usuário
@app.route('/logout', methods=['GET'])
def logout():
    # Destruição da sessão
    session.pop('usuario_id', None)
    flash('Você saiu da sessão.', 'info')
    return redirect(url_for('index'))

# 12 - Verifica se o arquivo é o principal do projeto
if __name__ == '__main__':
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5002'))
    app.run(host=host, port=port, debug=True)

