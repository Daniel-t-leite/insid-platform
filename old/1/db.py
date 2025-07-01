import sqlite3
from contextlib import closing
import hashlib
import pandas as pd
from typing import Optional
import logging

def conectar_db():
    """Estabelece conexão com o banco de dados"""
    return sqlite3.connect('inSID.db')

def hash_senha(senha):
    """Gera hash SHA-256 para senhas"""
    return hashlib.sha256(senha.encode()).hexdigest()

def inicializar_bd():
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            admin INTEGER DEFAULT 0
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS barragens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            localizacao TEXT,
            altura REAL,
            comprimento REAL,
            rel_cordaaltura REAL,
            em_analise INTEGER DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        """)

        # Inserir valores padrão se as tabelas estiverem vazias
        if not cursor.execute("SELECT 1 FROM tipos_barragem LIMIT 1").fetchone():
            cursor.executemany(
                "INSERT INTO tipos_barragem (nome, descricao) VALUES (?, ?)",
                [
                    ("Homogênea", "Barragem construída com um único tipo de material"),
                    ("Terra e Enrocamento", "Barragem com núcleo de terra e envoltório de enrocamento"),
                    ("Enrocamento com Face de Betão", "Barragem de enrocamento com face de concreto"),
                    ("Enrocamento com Núcleo Betuminoso", "Barragem de enrocamento com núcleo impermeável de betume")
                ]
            )

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS zonas_barragem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barragem_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            material_id INTEGER NOT NULL,
            FOREIGN KEY (barragem_id) REFERENCES barragens(id),
            FOREIGN KEY (material_id) REFERENCES tipos_materiais(id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario_barragem_analise (
            usuario_id INTEGER NOT NULL,
            barragem_id INTEGER NOT NULL,
            data_selecao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (barragem_id) REFERENCES barragens(id),
            PRIMARY KEY (usuario_id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS modos_falha (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT,
            causa TEXT,
            fase_operacao TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS modos_falha_associacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modo_falha_id INTEGER NOT NULL,
            tipo_barragem TEXT,
            zona_nome TEXT,
            material_id INTEGER,
            altura_min REAL,
            altura_max REAL,
            comprimento_min REAL,
            comprimento_max REAL,
            FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
            FOREIGN KEY (material_id) REFERENCES tipos_materiais(id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomalias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT,
            categoria TEXT,
            gravidade_padrao INTEGER
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomalias_observadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zona_id INTEGER NOT NULL,
            anomalia_id INTEGER NOT NULL,
            data_observacao DATE,
            observacoes TEXT,
            FOREIGN KEY (zona_id) REFERENCES zonas_barragem(id),
            FOREIGN KEY (anomalia_id) REFERENCES anomalias(id)
        )
        """)
        conn.commit()




# ---------- Operações de Usuário ----------
def criar_usuario(codigo, nome, email, funcao, organizacao, senha, ativo):
    """Cadastra um novo usuário no sistema"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (codigo, nome, email, funcao, organizacao, senha_hash, ativo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (codigo, nome, email, funcao, organizacao, hash_senha(senha), ativo)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def verificar_credenciais(email, senha):
    """Verifica se as credenciais são válidas"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT codigo, nome, is_admin FROM usuarios 
        WHERE email = ? AND senha_hash = ? AND LOWER(ativo) = 'sim'
        """, (email, hash_senha(senha)))
        return cursor.fetchone()

def email_existe(email):
    """Verifica se um email já está cadastrado"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,))
        return cursor.fetchone() is not None

def obter_proximo_codigo_usuario():
    """Obtém o próximo código disponível para novo usuário"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(CAST(codigo AS INTEGER)) FROM usuarios")
        max_codigo = cursor.fetchone()[0]
        return str(max_codigo + 1) if max_codigo is not None else "1"
    



# ---------- Operações de Administração de Usuários ----------
def listar_usuarios():
    """Lista todos os usuários cadastrados"""
    with closing(conectar_db()) as conn:
        query = """
        SELECT codigo, nome, email, funcao, organizacao, 
               ativo, is_admin, strftime('%d/%m/%Y %H:%M', data_criacao) as data_criacao
        FROM usuarios
        ORDER BY nome
        """
        return pd.read_sql(query, conn)

def atualizar_status_usuario(codigo, ativo):
    """Atualiza o status ativo/inativo de um usuário"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET ativo = ? WHERE codigo = ?",
            (ativo, codigo)
        )
        conn.commit()
        return cursor.rowcount > 0

def atualizar_admin_usuario(codigo, is_admin):
    """Atualiza o status de administrador de um usuário"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET is_admin = ? WHERE codigo = ?",
            (is_admin, codigo)
        )
        conn.commit()
        return cursor.rowcount > 0

def excluir_usuario(codigo):
    """Remove um usuário do sistema"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE codigo = ?", (codigo,))
        conn.commit()
        return cursor.rowcount > 0

# ---------- Operações de Tipos ----------
def obter_tipos_barragem():
    """Retorna todos os tipos de barragem cadastrados"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT *, nome FROM tipos_barragem ORDER BY nome")
        return cursor.fetchall()

def cadastrar_barragem(usuario_id, nome, tipo, localizacao, altura, comprimento, rel_cordaaltura):
    """Insere uma nova barragem no banco de dados"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO barragens 
        (usuario_id, nome, tipo, localizacao, altura, comprimento, rel_cordaaltura) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (usuario_id, nome, tipo, localizacao, altura, comprimento, rel_cordaaltura)
    )
    conn.commit()
    conn.close()


def adicionar_tipo_barragem(nome, descricao):
    """Adiciona um novo tipo de barragem"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO tipos_barragem (nome, descricao) VALUES (?, ?)",
                (nome, descricao)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def remover_tipo_barragem(tipo_id):
    """Remove um tipo de barragem pelo ID"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tipos_barragem WHERE id = ?", (tipo_id,))
        conn.commit()
        return cursor.rowcount > 0



def inserir_barragem(usuario_id, nome, tipo, localizacao, altura, comprimento):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO barragens (usuario_id, nome, tipo, localizacao, altura, comprimento)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (usuario_id, nome, tipo, localizacao, altura, comprimento))
            conn.commit()
            return True
        except Exception as e:
            print("Erro ao inserir barragem:", e)
            return False

def listar_barragens(usuario_id=None):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        if usuario_id:
            cursor.execute("""
            SELECT * FROM barragens WHERE usuario_id = ?
            """, (usuario_id,))
        else:
            cursor.execute("""
            SELECT * FROM barragens
            """)
        return cursor.fetchall()

def obter_usuario_id(email):
    """Obtém o ID do usuário a partir do email"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT codigo FROM usuarios WHERE email = ?", (email,))
        result = cursor.fetchone()
        return result[0] if result else None

def obter_barragens_usuario(usuario_id):
    """Retorna todas as barragens cadastradas por um usuário"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, tipo, localizacao, altura, comprimento, rel_cordaaltura FROM barragens WHERE usuario_id = ?", (usuario_id,))
    barragens = cursor.fetchall()
    conn.close()
    return barragens

def obter_barragem_analise(usuario_id):
    """Retorna a barragem atualmente em análise pelo usuário, com todos os dados"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.usuario_id, b.nome, b.tipo, b.localizacao, 
               b.altura, b.comprimento, b.rel_cordaaltura, 
               b.em_analise, b.data_criacao
        FROM barragens b
        JOIN usuario_barragem_analise uba ON b.id = uba.barragem_id
        WHERE uba.usuario_id = ?
    """, (usuario_id,))
    barragem = cursor.fetchone()
    conn.close()
    return barragem

def definir_barragem_analise(usuario_id, barragem_id):
    """Define qual barragem está em análise para o usuário"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Remove qualquer análise existente
    cursor.execute("DELETE FROM usuario_barragem_analise WHERE usuario_id = ?", (usuario_id,))
    
    # Insere a nova análise
    cursor.execute("INSERT INTO usuario_barragem_analise (usuario_id, barragem_id) VALUES (?, ?)", 
                  (usuario_id, barragem_id))
    
    conn.commit()
    conn.close()

def atualizar_barragem(barragem_id, nome, tipo, localizacao, altura, comprimento, rel_cordaaltura):
    """Atualiza os dados de uma barragem existente"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE barragens 
        SET nome = ?, tipo = ?, localizacao = ?, altura = ?, comprimento = ?, rel_cordaaltura = ?
        WHERE id = ?
    """, (nome, tipo, localizacao, altura, comprimento, rel_cordaaltura, barragem_id))
    conn.commit()
    conn.close()

def excluir_barragem(barragem_id):
    """Remove uma barragem do sistema"""
    print(barragem_id)
    print("P00")
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Remove da tabela de análise primeiro (se existir)
    cursor.execute("DELETE FROM usuario_barragem_analise WHERE barragem_id = ?", (barragem_id,))
    
        # Remove a barragem
    cursor.execute("DELETE FROM barragens WHERE id = ?", (barragem_id,))
    
    conn.commit()
    conn.close()






# Inicializa o banco de dados
inicializar_bd()