from flask import Flask, render_template, request
from flask import redirect, url_for, flash, session
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError


app = Flask(
    __name__,
    static_folder='assets',
    static_url_path='/assets',
    template_folder='templates'
)

app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:root@localhost:3306/agendalab?charset=utf8mb4'
)
db = SQLAlchemy(app)


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
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


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    current_user = None
    if session.get('usuario_id'):
        current_user = Usuario.query.get(session['usuario_id'])
    ambientes = Ambiente.query.order_by(Ambiente.nome.asc()).all()
    return render_template('dashboard.html', current_user=current_user, ambientes=ambientes)

@app.route('/painel')
def painel():
    return render_template('painel.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')



# Página somente leitura: lista de usuários
@app.route('/usuarios')
def usuarios_page():
    users = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return render_template('usuarios.html', users=users)



@app.route('/usuarios/cadastrar', methods=['POST'])
def form_create_usuario():
    nome = (request.form.get('nome') or '').strip()
    email = (request.form.get('email') or '').strip()
    telefone = (request.form.get('telefone') or '').strip()
    login = (request.form.get('login') or '').strip()
    role = 'usuario'

    if not login or not nome:
        flash('Campos obrigatórios: login e nome', 'warning')
        return redirect(url_for('index'))

    try:
        u = Usuario(login=login, nome=nome, email=email or None, telefone=telefone or None, role=role)
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


@app.route('/login', methods=['POST'])
def login():
    login = (request.form.get('login') or '').strip()
    if not login:
        flash('Informe o login para entrar', 'warning')
        return redirect(url_for('index'))
    user = Usuario.query.filter_by(login=login).first()
    if not user:
        flash('Login não encontrado', 'danger')
        return redirect(url_for('index'))
    session['usuario_id'] = user.id
    flash(f'Bem-vindo(a), {user.nome}!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5002'))
    try:
        with app.app_context():
            db.create_all()
            if Ambiente.query.count() == 0:
                for nome in ['Laboratório I', 'Laboratório II', 'Laboratório Robótica']:
                    db.session.add(Ambiente(nome=nome, capacidade=30, ativo=True))
                db.session.commit()
    except Exception:
        pass
    app.run(host=host, port=port, debug=True)

