-- AgendaLab — Esquema de Banco (PostgreSQL)
-- Tabelas: usuarios, ambientes, reservas
-- Observações:
--  - Unicidades em login (usuarios) e nome (ambientes)
--  - CHECK de ordem de horário (inicio < fim)
--  - Índices para suportar consultas e validação de conflitos no backend

-- Usuários
CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  login VARCHAR(50) NOT NULL UNIQUE,
  nome VARCHAR(120) NOT NULL,
  email VARCHAR(120),
  telefone VARCHAR(20),
  role VARCHAR(20) NOT NULL DEFAULT 'usuario',
  criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Ambientes
CREATE TABLE IF NOT EXISTS ambientes (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(120) NOT NULL UNIQUE,
  capacidade INTEGER NOT NULL CHECK (capacidade > 0),
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Reservas
CREATE TABLE IF NOT EXISTS reservas (
  id SERIAL PRIMARY KEY,
  ambiente_id INTEGER NOT NULL REFERENCES ambientes(id) ON DELETE RESTRICT,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  data DATE NOT NULL,
  inicio TIME NOT NULL,
  fim TIME NOT NULL,
  turma VARCHAR(60),
  status VARCHAR(20) NOT NULL DEFAULT 'ativa',
  criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
  CHECK (inicio < fim)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_reservas_amb_data_horario
  ON reservas (ambiente_id, data, inicio, fim);

CREATE INDEX IF NOT EXISTS idx_reservas_usuario_data
  ON reservas (usuario_id, data);

-- Unicidade para evitar duplicatas exatas de reserva no mesmo intervalo
-- (não cobre sobreposição de intervalos; a lógica deve validar no backend)
CREATE UNIQUE INDEX IF NOT EXISTS uq_reserva_intervalo_exato
  ON reservas (ambiente_id, data, inicio, fim);
