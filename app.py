from flask import Flask, render_template, request, jsonify
from flask import redirect, url_for, flash
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


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/painel')
def painel():
    return render_template('painel.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/api/usuarios', methods=['GET'])
def api_list_usuarios():
    users = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return jsonify([
        {
            'id': u.id,
            'login': u.login,
            'nome': u.nome,
            'email': u.email or '',
            'telefone': u.telefone or '',
            'role': u.role,
            'criado_em': u.criado_em.isoformat() if isinstance(u.criado_em, datetime) else str(u.criado_em),
        }
        for u in users
    ])

# Página somente leitura: lista de usuários
@app.route('/usuarios')
def usuarios_page():
    users = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return render_template('usuarios.html', users=users)

@app.route('/api/usuarios', methods=['POST'])
def api_create_usuario():
    payload = request.get_json(silent=True) or {}
    login = (payload.get('login') or '').strip()
    nome = (payload.get('nome') or '').strip()
    email = (payload.get('email') or '').strip()
    telefone = (payload.get('telefone') or '').strip()
    role = (payload.get('role') or 'usuario').strip() or 'usuario'

    if not login or not nome:
        return jsonify({'error': 'Campos obrigatórios: login e nome'}), 400

    try:
        u = Usuario(login=login, nome=nome, email=email or None, telefone=telefone or None, role=role)
        db.session.add(u)
        db.session.commit()
        return jsonify({
            'id': u.id,
            'login': u.login,
            'nome': u.nome,
            'email': u.email or '',
            'telefone': u.telefone or '',
            'role': u.role,
            'criado_em': u.criado_em.isoformat() if isinstance(u.criado_em, datetime) else str(u.criado_em),
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Login já cadastrado'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# --------- Cadastro via formulário (server-side) ---------
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

if __name__ == '__main__':
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5002'))
    try:
        with app.app_context():
            db.create_all()
    except Exception:
        pass
    app.run(host=host, port=port, debug=True)