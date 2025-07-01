import sqlite3
from contextlib import closing
import hashlib
import pandas as pd
from typing import Optional


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
            tipo_id INTEGER NOT NULL,
            localizacao TEXT,
            altura REAL,
            comprimento REAL,
            rel_cordaaltura REAL,
            em_analise INTEGER DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
        """)
        # Criação da tabela
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_barragem (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                descricao TEXT,
                referencia_tecnica TEXT,
                image_path TEXT  -- Caminho local ou URL da imagem associada
            );
        """)

        # Inserir valores padrão se a tabela estiver vazia
        if not cursor.execute("SELECT 1 FROM tipos_barragem LIMIT 1").fetchone():
            cursor.executemany(
                """
                INSERT INTO tipos_barragem (usuario_id, nome, descricao)
                VALUES (?, ?, ?)
                """,
                [
                    (1, "Homogênea", "Barragem construída com um único tipo de material"),
                    (1, "Terra e Enrocamento", "Barragem com núcleo de terra e envoltório de enrocamento"),
                    (1, "Enrocamento com Face de Betão", "Barragem de enrocamento com face de concreto"),
                    (1, "Enrocamento com Núcleo Betuminoso", "Barragem de enrocamento com núcleo impermeável de betume")
                ]
            )

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS zonas_barragem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            barragem_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT,
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
        CREATE TABLE IF NOT EXISTS tipo_modo_falha (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT,
            referencia_tecnica TEXT
         );
        """)

        # Inserir valores padrão se a tabela estiver vazia
        if not cursor.execute("SELECT 1 FROM tipo_modo_falha LIMIT 1").fetchone():
            cursor.executemany(
                """
                INSERT INTO tipo_modo_falha (usuario_id, nome, descricao, referencia_tecnica)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        1,
                        'Erosão Interna',
                        'Erosão interna dos solos ou dos preenchimentos de descontinuidades nos encontros, fundação ou corpo do aterro, incluindo zonas próximas a condutas/galerias.',
                        'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC, p. 10'
                    ),
                    (
                        1,
                        'Movimento de Grandes Massas',
                        'Instabilidades estáticas ou sísmicas (incluindo liquefação, assentamentos e perda de folga), galgamento por instabilidade de encostas ou ruptura por corte na fundação.',
                        'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC, p. 10'
                    ),
                    (
                        1,
                        'Roturas Hidráulicas',
                        'Falhas devido a níveis de água excepcionais: galgamento (por capacidade insuficiente ou erro operacional), erosão no dissipador de energia ou galgamento do canal do descarregador.',
                        'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC, p. 10'
                    )
                ]
            )

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS modos_falha (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            id_tipo_modo_falha INTEGER NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT,
            referencia_tecnica TEXT,
            image_path TEXT 
         );
        """)

        # Inserir valores padrão na tabela modos_falha se estiver vazia
        if not cursor.execute("SELECT 1 FROM modos_falha LIMIT 1").fetchone():
            cursor.executemany(
                """
                INSERT INTO modos_falha (
                    usuario_id,
                    id_tipo_modo_falha,
                    nome,
                    descricao,
                    referencia_tecnica,
                    image_path
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    # Erosão Interna (id_tipo_modo_falha = 1)
                    (1, 1, 'Erosão no corpo do aterro',
                    'Erosão interna dos solos ou preenchimentos de descontinuidades no corpo do aterro, encontros ou fundação',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None),
                    (1, 1, 'Erosão ao longo de condutas',
                    'Erosão interna próxima a condutas (descarga de fundo, tomada de água) ou estruturas rígidas',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None),

                    # Movimento de Grandes Massas (id_tipo_modo_falha = 2)
                    (1, 2, 'Instabilidade estática/sísmica',
                    'Instabilidade por ações estáticas (esvaziamento rápido) ou sísmicas nos maciços, fundação ou encontros',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None),
                    (1, 2, 'Assentamentos com perda de folga',
                    'Assentamentos que levam a galgamento e erosão externa',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None),
                    (1, 2, 'Liquefação sísmica',
                    'Liquefação do núcleo ou fundação devido a sismos',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None),
                    (1, 2, 'Rotura por corte na fundação',
                    'Falha em argilas plásticas com amolecimento por molhagem',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None),

                    # Roturas Hidráulicas (id_tipo_modo_falha = 3)
                    (1, 3, 'Galgamento por capacidade insuficiente',
                    'Galgamento devido à incapacidade do descarregador de cheias',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None),
                    (1, 3, 'Galgamento por erro operacional',
                    'Falha no manejo de comportas do descarregador',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None),
                    (1, 3, 'Erosão no dissipador de energia',
                    'Erosão no canal ou bacia de dissipação do descarregador',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None),
                    (1, 3, 'Galgamento do canal do descarregador',
                    'Erosão externa da fundação/aterro por galgamento das paredes',
                    'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', None)
                ]
            )

        # Tabela anomalias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                descricao TEXT,
                gravidade REAL,
                peso REAL,
                referencia_tecnica TEXT,
                image_path TEXT
            );
            """)
        

        # Tabela de relacionamento anomalia_modo_falha
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalia_modo_falha (
                anomalia_id INTEGER NOT NULL,
                modo_falha_id INTEGER NOT NULL,
                FOREIGN KEY (anomalia_id) REFERENCES anomalias(id),
                FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
                PRIMARY KEY (anomalia_id, modo_falha_id)
            );
            """)
        
        # Tabela de relacionamento anomalia_zona
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalia_zona (
                anomalia_id INTEGER NOT NULL,
                zona_id INTEGER NOT NULL,
                FOREIGN KEY (anomalia_id) REFERENCES anomalias(id),
                FOREIGN KEY (zona_id) REFERENCES tipos_zonas_bar(id),
                PRIMARY KEY (anomalia_id, zona_id)
            );
            """)
        
        # Tabela de relacionamento anomalia_tipo_material
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalia_tipo_material (
                anomalia_id INTEGER NOT NULL,
                tipo_mat_id INTEGER NOT NULL,
                FOREIGN KEY (anomalia_id) REFERENCES anomalias(id),
                FOREIGN KEY (tipo_mat_id) REFERENCES tipos_materiais(id),
                PRIMARY KEY (anomalia_id, tipo_mat_id)
            );
            """)
        
        # Tabela de relacionamento anomalia_tipo_barragem
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalia_tipo_barragem (
                anomalia_id INTEGER NOT NULL,
                tipo_barragem_id INTEGER NOT NULL,
                FOREIGN KEY (anomalia_id) REFERENCES anomalias(id),
                FOREIGN KEY (tipo_barragem_id) REFERENCES tipos_barragem(id),
                PRIMARY KEY (anomalia_id, tipo_barragem_id)
            );
            """)
        
        # Criar índices para melhorar performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_modos_falha_tipo ON modos_falha(id_tipo_modo_falha);
            """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomalia_modo_falha ON anomalia_modo_falha(anomalia_id, modo_falha_id);
            """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomalia_zona ON anomalia_zona(anomalia_id, zona_id);
            """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomalia_tipo_material ON anomalia_tipo_material(anomalia_id, tipo_mat_id);
            """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomalia_tipo_barragem ON anomalia_tipo_barragem(anomalia_id, tipo_barragem_id);
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

def remover_tipo_barragem(tipo_id):
    """Remove um tipo de barragem pelo ID"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tipos_barragem WHERE id = ?", (tipo_id,))
        conn.commit()
        return cursor.rowcount > 0

def cadastrar_barragem(usuario_id, nome, tipo_id, localizacao, altura, comprimento, rel_cordaaltura):
    """Insere uma nova barragem no banco de dados"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO barragens 
        (usuario_id, nome, tipo_id, localizacao, altura, comprimento, rel_cordaaltura) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (usuario_id, nome, tipo_id, localizacao, altura, comprimento, rel_cordaaltura)
    )
    conn.commit()
    conn.close()

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

#----------- Operações de Barragens ----------
# Zonas de Barragem
def obter_zonas_por_barragem(barragem_id):
    """Retorna todas as zonas de uma barragem com a nova estrutura"""
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, usuario_id, barragem_id, material_id, nome, descricao
            FROM zonas_barragem 
            WHERE barragem_id = ?
            ORDER BY nome
        """, (barragem_id,))
        return cursor.fetchall()
    finally:
        conn.close()

def cadastrar_zona_db(usuario_id, barragem_id, material_id, nome, descricao=None):
    """Cadastra uma nova zona com a estrutura atualizada"""
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO zonas_barragem 
            (usuario_id, barragem_id, material_id, nome, descricao)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario_id, barragem_id, material_id, nome, descricao))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao cadastrar zona: {str(e)}")
        return False
    finally:
        conn.close()


# Tipos de Materiais
def obter_todos_materiais():
    """Retorna todos os materiais cadastrados"""
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, usuario_id, nome, descricao FROM tipos_materiais")
        return cursor.fetchall()
    finally:
        conn.close()


def cadastrar_material_db(nome: str, descricao: str = None):
    """
    Insere um novo tipo de material na tabela 'tipos_materiais'.
    Retorna True se bem-sucedido, False se houver erro de integridade.
    """
    conn = conectar_db()
    try:
        conn.execute(
            "INSERT INTO tipos_materiais (nome, descricao) VALUES (?, ?)",
            (nome.strip(), descricao.strip() if descricao else None)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def excluir_material_db(material_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tipos_materiais WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()
    return True  # se quiser pode validar se deletou mesmo

def obter_material_por_id(material_id):
    """Obtém material de forma segura"""
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome, descricao 
            FROM tipos_materiais
            WHERE id = ?
        """, (material_id,))
        return cursor.fetchone()  # Retorna (id, nome, descricao) ou None
    except Exception as e:
        print(f"Erro ao obter material: {str(e)}")
        return None
    finally:
        conn.close()

# def obter_modos_falha_por_zona(zona_id):
#     """Obtém modos de falha de forma segura"""
#     conn = conectar_db()
#     try:
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT id, nome, descricao 
#             FROM modos_falha
#             WHERE zona_id = ?
#         """, (zona_id,))
#         return cursor.fetchall()  # Retorna lista de tuplas ou lista vazia
#     except Exception as e:
#         print(f"Erro ao obter modos de falha: {str(e)}")
#         return []
#     finally:
#         conn.close()

def obter_materiais_por_usuario(usuario_id):
    """Lista todos os materiais cadastrados por um usuário"""
    conn = None
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome, descricao 
            FROM tipos_materiais 
            WHERE usuario_id = ?
            ORDER BY nome
        """, (usuario_id,))
        
        return [{'id': row[0], 'nome': row[1], 'descricao': row[2]} for row in cursor.fetchall()]
        
    except sqlite3.Error as e:
        print(f"Erro ao listar materiais: {str(e)}")
        return []
        
    finally:
        if conn:
            conn.close()

def pesquisar_materiais(termo):
    """Pesquisa materiais por nome ou descrição"""
    conn = None
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome, descricao 
            FROM tipos_materiais 
            WHERE nome LIKE ? OR descricao LIKE ?
            ORDER BY nome
        """, (f"%{termo}%", f"%{termo}%"))
        
        return cursor.fetchall()
        
    except sqlite3.Error as e:
        print(f"Erro na pesquisa: {str(e)}")
        return []
        
    finally:
        if conn:
            conn.close()

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
    cursor.execute("SELECT id, nome, tipo_id, localizacao, altura, comprimento, rel_cordaaltura FROM barragens WHERE usuario_id = ?", (usuario_id,))
    barragens = cursor.fetchall()
    conn.close()
    return barragens

def obter_barragem_analise(usuario_id):
    """Retorna a barragem atualmente em análise pelo usuário, com todos os dados"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.usuario_id, b.nome, b.tipo_id, b.localizacao, 
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

def atualizar_barragem(barragem_id, nome, tipo_id, localizacao, altura, comprimento, rel_cordaaltura):
    """Atualiza os dados de uma barragem existente"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE barragens 
        SET nome = ?, tipo_id = ?, localizacao = ?, altura = ?, comprimento = ?, rel_cordaaltura = ?
        WHERE id = ?
    """, (nome, tipo_id, localizacao, altura, comprimento, rel_cordaaltura, barragem_id))
    conn.commit()
    conn.close()

def excluir_barragem(barragem_id):
    """Remove uma barragem do sistema"""

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