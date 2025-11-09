# Bibliotecas que devem ser importadas para o funcionamento da aplicação
from flask import Flask, render_template, request
from flask import redirect, url_for, flash, session
from functools import wraps
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError


# Configuração da estrutura do Flask para renderizar páginas
app = Flask(
    __name__,
    # Caso o arquivo .css não consiga ser lido, apague as três linhas abaixo
    static_folder='assets',
    static_url_path='/assets',
    template_folder='templates')


# Configuração para acesso do banco de dados
# Deve ser alterado login, senha e nome do schema (banco de dados)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:root@localhost:3306/agendalab?charset=utf8mb4')
db = SQLAlchemy(app)


# Função que veridica se o usuário logado é adm
# Função será usada para acessar as rotas /ambientes e /usuarios no projeto
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        uid = session.get('usuario_id')
        if not uid:
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('index'))
        user = Usuario.query.get(uid)
        # Exige que o usuário seja 'adm' e que a senha cadastrada também seja 'adm'
        if not user or user.login != 'adm' or user.senha != 'adm':
            flash('Acesso restrito ao administrador.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return wrapper


# Criação dos modelos de dados para conexão com o banco de dados
# Deve ser observado os campos no MySQL Workbench
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
class Ambiente(db.Model):
    __tablename__ = 'ambientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, server_default='1')
    criado_em = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    reservas = db.relationship('Reserva', backref='ambiente', lazy=True)
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


# Definição das rotas do projeto
# Rota principal que abrea página index.html (Formulário de login e cadastro)
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

# Rota que abre o painel principal após o login ser realizado
@app.route('/home')
def home():
    return render_template('home.html')

# Rota que exibe a rota do dashboard a partir do login do usuário
@app.route('/dashboard')
def dashboard():
    current_user = None
    user_reservas = []
    if session.get('usuario_id'):
        current_user = Usuario.query.get(session['usuario_id'])
        # Select que exibe as reservas já realizadas pelo usuário na página dashboard.html
        if current_user:
            user_reservas = (
                Reserva.query
                .filter(Reserva.usuario_id == current_user.id)
                .order_by(Reserva.data.desc(), Reserva.inicio.desc())
                .all())
    # Select feito na tabela ambientes para ser exibido no formulário que existe na página dashboard.html
    ambientes = Ambiente.query.order_by(Ambiente.nome.asc()).all()
    return render_template('dashboard.html', current_user=current_user, ambientes=ambientes, reservas=user_reservas)

# Rota que exibe o painel de reservas
@app.route('/painel')
def painel():
    # Select dos ambientes cadastrados para ser exibidos no filto
    ambientes = Ambiente.query.order_by(Ambiente.nome.asc()).all()
    selected_lab = (request.args.get('lab') or '').strip()
    query = Reserva.query
    # Select a dos dados para serem exibidos a partir do que foi selecionado no campo Select
    if selected_lab:
        query = query.filter(Reserva.ambiente.has(Ambiente.nome == selected_lab))
    reservas = query.order_by(Reserva.data.desc(), Reserva.inicio.desc()).all()
    return render_template('painel.html', ambientes=ambientes, reservas=reservas, selected_lab=selected_lab)

# Rota para listagem de usuários a partir da função admin_required
@app.route('/usuarios')
@admin_required
def usuarios_page():
    # Select para selecionar os usuários cadastrados para serem exibidos na página usuarios.html
    users = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return render_template('usuarios.html', users=users)

# Rota que lista os ambientes cadastrados a partir da função admim_required
@app.route('/ambientes')
@admin_required
def ambientes_page():
    ambientes = Ambiente.query.order_by(Ambiente.nome.asc()).all()
    return render_template('ambientes.html', ambientes=ambientes)

# Rota que recebe os dados do ambiente (Formulário de cadastro de ambiente)
@app.route('/ambientes/cadastrar', methods=['POST'])
def cadastrar_ambiente():
    nome = (request.form.get('nome') or '').strip()
    capacidade = (request.form.get('capacidade') or '').strip()
    ativo = request.form.get('ativo')

    # Validação se o nome ou a capacidade foram informados
    if not nome or not capacidade:
        flash('Informe nome e capacidade', 'warning')
        return redirect(url_for('ambientes_page'))

    try:
        capacidade = int(capacidade)
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
            ativo=bool(ativo))
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

# Rota que recebe os dados do cadastro e armazena no banco de dados
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
            senha=senha)
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

# Rota que recebe os dados da reserva
@app.route('/reservas/cadastrar', methods=['POST'])
def cadastrar_reserva():

    # Exige usuário logado
    uid = session.get('usuario_id')
    if not uid:
        flash('Faça login para reservar.', 'warning')
        return redirect(url_for('index'))

    laboratorio_nome = (request.form.get('laboratorio') or '').strip()
    data_str = (request.form.get('data') or '').strip()
    inicio_str = (request.form.get('inicio') or '').strip()
    fim_str = (request.form.get('fim') or '').strip()
    turma = (request.form.get('turma') or '').strip() or None

    # Valida campos obrigatórios
    if not laboratorio_nome or not data_str or not inicio_str or not fim_str:
        flash('Informe laboratório, data e horários.', 'warning')
        return redirect(url_for('dashboard'))

    # Busca ambiente pelo nome
    ambiente = Ambiente.query.filter_by(nome=laboratorio_nome).first()
    if not ambiente:
        flash('Laboratório inválido.', 'danger')
        return redirect(url_for('dashboard'))

    # Converte data e horários
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
        inicio = datetime.strptime(inicio_str, '%H:%M').time()
        fim = datetime.strptime(fim_str, '%H:%M').time()
    except ValueError:
        flash('Formato de data/horário inválido.', 'danger')
        return redirect(url_for('dashboard'))

    # Valida ordem de horários
    if fim <= inicio:
        flash('Horário de término deve ser após o início.', 'warning')
        return redirect(url_for('dashboard'))

    # Verifica conflito de reserva no mesmo ambiente e data
    conflito = (
        Reserva.query
        .filter(Reserva.ambiente_id == ambiente.id, Reserva.data == data)
        .filter(Reserva.inicio < fim, Reserva.fim > inicio)
        .first())
    
    if conflito:
        flash('Conflito: já existe reserva nesse intervalo.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        r = Reserva(
            ambiente_id=ambiente.id,
            usuario_id=uid,
            data=data,
            inicio=inicio,
            fim=fim,
            turma=turma,
            status='ativa')
        db.session.add(r)
        db.session.commit()
        flash('Reserva criada com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar reserva: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

# Rota que autentica o login usuário (Recebe os dados de um fomrulário HTML)
@app.route('/login', methods=['POST'])
def login():
    login = (request.form.get('login') or '').strip()
    senha = (request.form.get('senha') or '')

    # Validação para verificar seo login foi digitado
    if not login or not senha:
        flash('Informe login e senha', 'warning')
        return redirect(url_for('index'))
    
    # Busca usuário e valida senha informada contra a cadastrada
    user = Usuario.query.filter_by(login=login).first()
    if not user or user.senha != senha:
        flash('Login ou senha inválidos', 'danger')
        return redirect(url_for('index'))
    # Cria a sessão para o usuário informado após validação
    session['usuario_id'] = user.id
    flash(f'Bem-vindo(a), {user.nome}!', 'success')
    return redirect(url_for('home'))

# Rota que realiza o logout do usuário
@app.route('/logout', methods=['GET'])
def logout():
    # Destruição da sessão
    session.pop('usuario_id', None)
    flash('Você saiu da sessão.', 'info')
    return redirect(url_for('index'))


# Verifica se o arquivo é o principal do projeto
if __name__ == '__main__':
    # Runner da aplicação (configurável via env HOST/PORT)
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5002'))
    app.run(host=host, port=port, debug=True)

