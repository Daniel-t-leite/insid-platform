import streamlit as st
import sqlite3
from contextlib import closing


def conectar_db():
    return sqlite3.connect('inSID.db')

# ---------- FUNÇÕES DE ACESSO AOS DADOS ----------
def obter_tipos_barragem():
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM tipos_barragem ORDER BY nome")
        return cursor.fetchall()

def obter_tipos_fundacao():
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM tipos_fundacao ORDER BY nome")
        return cursor.fetchall()

def adicionar_tipo_barragem(nome, descricao):
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

def adicionar_tipo_fundacao(nome, descricao):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO tipos_fundacao (nome, descricao) VALUES (?, ?)",
                (nome, descricao)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remover_tipo_barragem(tipo_id):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tipos_barragem WHERE id = ?", (tipo_id,))
        conn.commit()
        return cursor.rowcount > 0

def remover_tipo_fundacao(tipo_id):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tipos_fundacao WHERE id = ?", (tipo_id,))
        conn.commit()
        return cursor.rowcount > 0



def obter_usuario_id(email):
    conn = sqlite3.connect("inSID.db")
    cursor = conn.cursor()
    cursor.execute("SELECT codigo FROM usuarios WHERE email = ?", (email,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return resultado[0]
    return None

# Cria a conexão com o banco de dados inSID.db
def criar_conexao():
    return sqlite3.connect("inSID.db")

# Cria a tabela barragens com os campos atualizados
def criar_tabela():
    conn = criar_conexao()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS barragens (
            Barragem_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Usuario_ID INTEGER NOT NULL,
            Nome TEXT NOT NULL,
            Tipo TEXT NOT NULL,
            Fundacao TEXT NOT NULL,
            Localizacao TEXT NOT NULL,
            FOREIGN KEY (Usuario_ID) REFERENCES usuarios(id)
        )
    """)
    conn.commit()
    conn.close()

# Insere uma nova barragem
def criar_barragem(usuario_id, nome, tipo, fundacao, localizacao):
    conn = sqlite3.connect("inSID.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO barragens (Usuario_ID, Nome, Tipo, TipoFundacao, Localizacao)
        VALUES (?, ?, ?, ?, ?)
    """, (usuario_id, nome, tipo, fundacao, localizacao))
    conn.commit()
    conn.close()

# Lista todas as barragens registradas
def listar_barragens():
    conn = sqlite3.connect("inSID.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            Barragem_ID, Usuario_ID, Nome, Tipo, TipoFundacao, Localizacao 
        FROM barragens
    """)
    linhas = cursor.fetchall()
    conn.close()
    return [
        {
            "ID": linha[0],
            "Usuário_ID": linha[1],
            "Nome": linha[2],
            "Tipo": linha[3],
            "Fundação": linha[4],
            "Localização": linha[5],
        }
        for linha in linhas
    ]
# Cria a tabela ao importar o módulo
criar_tabela()
