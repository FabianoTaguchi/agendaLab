-- AgendaLab — Esquema de Banco (MySQL 8)
-- Tabelas: usuarios, ambientes, reservas
-- Observações:
--  - Unicidade em login (usuarios) e nome (ambientes)
--  - Índices para suportar consultas e validação de conflitos no backend

-- Criação do banco e uso
CREATE DATABASE IF NOT EXISTS agendalab CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE agendalab;

-- Usuários
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  login VARCHAR(50) NOT NULL UNIQUE,
  nome VARCHAR(120) NOT NULL,
  email VARCHAR(120),
  telefone VARCHAR(20),
  senha VARCHAR(255),
  ativo TINYINT(1) NOT NULL DEFAULT 1,
  role VARCHAR(20) NOT NULL DEFAULT 'usuario',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Ambientes
CREATE TABLE IF NOT EXISTS ambientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL UNIQUE,
  capacidade INT NOT NULL,
  ativo TINYINT(1) NOT NULL DEFAULT 1,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Reservas
CREATE TABLE IF NOT EXISTS reservas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ambiente_id INT NOT NULL,
  usuario_id INT NOT NULL,
  data DATE NOT NULL,
  inicio TIME NOT NULL,
  fim TIME NOT NULL,
  turma VARCHAR(60),
  status VARCHAR(20) NOT NULL DEFAULT 'ativa',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_reserva_ambiente FOREIGN KEY (ambiente_id) REFERENCES ambientes(id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_reserva_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT ON UPDATE CASCADE,
  KEY idx_reservas_amb_data_horario (ambiente_id, data, inicio, fim),
  KEY idx_reservas_usuario_data (usuario_id, data),
  UNIQUE KEY uq_reserva_intervalo_exato (ambiente_id, data, inicio, fim)
) ENGINE=InnoDB;

-- Dados iniciais (idempotentes via ON DUPLICATE KEY)
INSERT INTO usuarios (login, nome, email, telefone, senha, role)
VALUES ('adm', 'Administrador', NULL, NULL, 'adm', 'administrador')
ON DUPLICATE KEY UPDATE login = login;
