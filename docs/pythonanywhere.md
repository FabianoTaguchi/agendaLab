# Deploy no PythonAnywhere — AgendaLab (Flask + MySQL)

Este guia descreve como publicar o projeto AgendaLab no PythonAnywhere com MySQL.

## Pré-requisitos

- Conta criada no PythonAnywhere.
- Repositório no GitHub (ou upload dos arquivos via painel).
- Banco MySQL criado no PythonAnywhere (menu Databases).

## Estrutura do projeto

- Aplicação Flask em `app.py` exporta `app`.
- Templates em `templates/`, estáticos em `assets/`.
- Dependências em `requirements.txt` (inclui `Flask`, `Flask-SQLAlchemy`, `SQLAlchemy`, `PyMySQL`, `cryptography`, `gunicorn`).
- SQL em `sql/schema.sql` e dump opcional `sql/Dump20251123 agendalab.sql`.

## Passo a passo

### 1) Código no servidor

- Opção Git: no bash do PythonAnywhere, clone o repositório:

  ```bash
  git clone https://github.com/<usuario>/<repo>.git
  cd <repo>
  ```

- Opção upload: use o “Files” para enviar os arquivos e organizar na pasta desejada.

### 2) Virtualenv e dependências

Crie/ative uma virtualenv pelo menu “Consoles” → “Bash” e instale:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Configurar variáveis de ambiente

No PythonAnywhere, vá em “Web” → seção “Environment variables” e adicione:

- `SECRET_KEY`: um valor aleatório e forte.
- `DATABASE_URL`: string de conexão do MySQL, formato:

  ```
  mysql+pymysql://<usuario>:<senha>@<host>/<database>?charset=utf8mb4
  ```

No PythonAnywhere, o `host` costuma ser:

```
<usuario>.mysql.pythonanywhere-services.com
```

Exemplo:

```
mysql+pymysql://meuuser:minhasenha@meuuser.mysql.pythonanywhere-services.com/agendalab?charset=utf8mb4
```

### 4) WSGI

No menu “Web” → arquivo WSGI, ajuste para importar a aplicação:

```python
import sys
import os

# Caminho do projeto (ajuste conforme sua pasta)
path = '/home/<usuario>/<repo>'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

Salve e reinicie o web app.

### 5) Arquivos estáticos

No menu “Web”, mapeie uma URL para a pasta `assets`:

- URL: `/assets/`
- Diretório: `/home/<usuario>/<repo>/assets`

### 6) Banco de dados

Abra um console “MySQL” (menu Databases) e rode o schema:

```sql
source /home/<usuario>/<repo>/sql/schema.sql;
```

Opcionalmente, importe dados do dump:

```sql
source "/home/<usuario>/<repo>/sql/Dump20251123 agendalab.sql";
```

Se preferir evitar espaços no nome, renomeie o arquivo para algo como `dump_2025-11-23_agendalab.sql` e rode:

```sql
source /home/<usuario>/<repo>/sql/dump_2025-11-23_agendalab.sql;
```

Valide:

```sql
SHOW TABLES;
SHOW COLUMNS FROM usuarios;
```

### 7) Reiniciar e validar

- Reinicie o web app no menu “Web”.
- Acesse a URL pública.
- Teste login, `/usuarios`, `/ambientes`, `/dashboard` e `/perfil`.

## Logs e troubleshooting

- Verifique “Error log” no menu “Web” → “Log files”.
- Erros comuns:
  - Conexão MySQL: confirme `DATABASE_URL`, host e credenciais.
  - Módulos ausentes: reabra virtualenv e `pip install -r requirements.txt`.
  - Permissões: confirme caminhos corretos nos `source` e mapeamentos.

## Segurança recomendada

- Hash de senhas com `werkzeug.security` (`generate_password_hash`, `check_password_hash`).
- CSRF com Flask-WTF para formulários `POST`.
- Padronizar `role` do admin como `admin` e ajustar seed/código para consistência.

---

Com isso, o AgendaLab deve ficar online no PythonAnywhere com MySQL. Qualquer dúvida nos passos, me diga seu usuário, caminho do repo e eu ajusto os comandos exatamente para sua conta.

