import sqlite3
from contextlib import closing
import hashlib
import pandas as pd
#import json
from typing import Optional

def conectar_db():
    """Estabelece conexão com o banco de dados"""
    return sqlite3.connect('inSID.db')

def hash_senha(senha):
    """Gera hash SHA-256 para senhas"""
    return hashlib.sha256(senha.encode()).hexdigest()

def inicializar_bd():
    """Cria as tabelas e insere dados iniciais se necessário"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            codigo TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            funcao TEXT,
            organizacao TEXT,
            senha_hash TEXT NOT NULL,
            ativo TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin INTEGER DEFAULT 0
        )
        """)
        
        # Tabela de tipos de barragem
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_barragem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de tipos de fundação
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_fundacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de barragens
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS barragens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT NOT NULL,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            fundacao TEXT NOT NULL,
            localizacao TEXT,
            em_analise INTEGER DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (codigo)
        )
        """)
        
        # Tabelas para o sistema de modos de falha
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS classificacoes_suscetibilidade (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            peso INTEGER NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS niveis_risco (
            id INTEGER PRIMARY KEY,
            nivel TEXT UNIQUE NOT NULL,
            cor_alerta TEXT NOT NULL,
            acao_recomendada TEXT NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_materiais (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT,
            classificacao_unificada TEXT,
            propriedades_json TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS condicoes_criticas (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            tipo_condicao TEXT NOT NULL,
            descricao TEXT,
            referencia_tecnica TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS modos_falha (
            id INTEGER PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            mecanismo TEXT NOT NULL,
            fase_operacao TEXT NOT NULL,
            referencia_tecnica TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS barragem_modos_falha (
            id INTEGER PRIMARY KEY,
            tipo_barragem_id INTEGER NOT NULL,
            modo_falha_id INTEGER NOT NULL,
            relevancia INTEGER CHECK(relevancia BETWEEN 1 AND 5),
            fonte TEXT NOT NULL,
            observacoes TEXT,
            FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS falha_materiais_suscetiveis (
            id INTEGER PRIMARY KEY,
            modo_falha_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            suscetibilidade_id INTEGER NOT NULL,
            mecanismo_especifico TEXT,
            fonte TEXT NOT NULL,
            FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
            FOREIGN KEY (material_id) REFERENCES tipos_materiais(id),
            FOREIGN KEY (suscetibilidade_id) REFERENCES classificacoes_suscetibilidade(id),
            UNIQUE(modo_falha_id, material_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS falha_condicoes_criticas (
            id INTEGER PRIMARY KEY,
            modo_falha_id INTEGER NOT NULL,
            condicao_id INTEGER NOT NULL,
            peso_relativo INTEGER CHECK(peso_relativo BETWEEN 1 AND 5),
            fonte TEXT NOT NULL,
            FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
            FOREIGN KEY (condicao_id) REFERENCES condicoes_criticas(id),
            UNIQUE(modo_falha_id, condicao_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias_anomalias (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS localizacoes_anomalias (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomalias (
            id INTEGER PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria_id INTEGER NOT NULL,
            localizacao_id INTEGER NOT NULL,
            gravidade_padrao INTEGER,
            referencia_tecnica TEXT,
            FOREIGN KEY (categoria_id) REFERENCES categorias_anomalias(id),
            FOREIGN KEY (localizacao_id) REFERENCES localizacoes_anomalias(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS falha_anomalias (
            id INTEGER PRIMARY KEY,
            modo_falha_id INTEGER NOT NULL,
            anomalia_id INTEGER NOT NULL,
            importancia INTEGER CHECK(importancia BETWEEN 1 AND 5),
            frequencia_ocorrencia TEXT,
            fonte TEXT NOT NULL,
            FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
            FOREIGN KEY (anomalia_id) REFERENCES anomalias(id),
            UNIQUE(modo_falha_id, anomalia_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS criterios_risco (
            id INTEGER PRIMARY KEY,
            modo_falha_id INTEGER NOT NULL,
            nivel_risco_id INTEGER NOT NULL,
            pontuacao_minima INTEGER NOT NULL,
            acao_especifica TEXT,
            FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
            FOREIGN KEY (nivel_risco_id) REFERENCES niveis_risco(id)
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
        
        if not cursor.execute("SELECT 1 FROM tipos_fundacao LIMIT 1").fetchone():
            cursor.executemany(
                "INSERT INTO tipos_fundacao (nome, descricao) VALUES (?, ?)",
                [
                    ("Rochosa", "Fundação em rocha sã"),
                    ("Aluvionar", "Fundação em material aluvionar"),
                    ("Mista", "Fundação em rocha e material aluvionar")
                ]
            )
        
        # Verificar se usuário admin já existe antes de tentar criar
        cursor.execute("SELECT 1 FROM usuarios WHERE email = 'admin@insid.com'")
        if not cursor.fetchone():
            try:
                cursor.execute(
                    "INSERT INTO usuarios (codigo, nome, email, funcao, organizacao, senha_hash, ativo, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("1", "Administrador", "admin@insid.com", "Admin", "inSID", hash_senha("admin123"), "sim", 1)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                conn.rollback()
                print(f"Erro ao criar usuário admin: {e}")
        
        
        # Inserir dados iniciais
        if not cursor.execute("SELECT 1 FROM classificacoes_suscetibilidade LIMIT 1").fetchone():
            cursor.executemany(
                "INSERT INTO classificacoes_suscetibilidade (id, nome, peso) VALUES (?, ?, ?)",
                [
                    (1, 'Baixa', 1),
                    (2, 'Média', 2),
                    (3, 'Alta', 3),
                    (4, 'Crítica', 4)
                ]
            )
        
        if not cursor.execute("SELECT 1 FROM niveis_risco LIMIT 1").fetchone():
            cursor.executemany(
                "INSERT INTO niveis_risco (id, nivel, cor_alerta, acao_recomendada) VALUES (?, ?, ?, ?)",
                [
                    (1, 'Baixo', '#4CAF50', 'Monitoramento rotineiro'),
                    (2, 'Moderado', '#FFC107', 'Inspeções quinzenais'),
                    (3, 'Alto', '#FF9800', 'Ações corretivas recomendadas'),
                    (4, 'Crítico', '#F44336', 'Intervenção imediata necessária')
                ]
            )
        
        # Verificar se usuário admin já existe
        cursor.execute("SELECT 1 FROM usuarios WHERE email = 'admin@insid.com'")
        if not cursor.fetchone():
            try:
                cursor.execute(
                    "INSERT INTO usuarios (codigo, nome, email, funcao, organizacao, senha_hash, ativo, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("1", "Administrador", "admin@insid.com", "Admin", "inSID", hash_senha("admin123"), "sim", 1)
                )
            except sqlite3.IntegrityError as e:
                conn.rollback()
                print(f"Erro ao criar usuário admin: {e}")
        
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
        cursor.execute("SELECT id, nome FROM tipos_barragem ORDER BY nome")
        return cursor.fetchall()

def obter_tipos_fundacao():
    """Retorna todos os tipos de fundação cadastrados"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM tipos_fundacao ORDER BY nome")
        return cursor.fetchall()

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

def adicionar_tipo_fundacao(nome, descricao):
    """Adiciona um novo tipo de fundação"""
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
    """Remove um tipo de barragem pelo ID"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tipos_barragem WHERE id = ?", (tipo_id,))
        conn.commit()
        return cursor.rowcount > 0

def remover_tipo_fundacao(tipo_id):
    """Remove um tipo de fundação pelo ID"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tipos_fundacao WHERE id = ?", (tipo_id,))
        conn.commit()
        return cursor.rowcount > 0


# ---------- Operações de Barragem ----------

def criar_barragem(usuario_id, nome, tipo, fundacao, localizacao):
    """Cadastra uma nova barragem"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO barragens (usuario_id, nome, tipo, fundacao, localizacao) VALUES (?, ?, ?, ?, ?)",
            (usuario_id, nome, tipo, fundacao, localizacao)
        )
        conn.commit()

def listar_barragens():
    """Lista todas as barragens cadastradas"""
    with closing(conectar_db()) as conn:
        query = """
        SELECT b.id, u.nome as usuario, b.nome, b.tipo, b.fundacao, b.localizacao, 
               strftime('%d/%m/%Y %H:%M', b.data_criacao) as data_criacao
        FROM barragens b
        JOIN usuarios u ON b.usuario_id = u.codigo
        """
        return pd.read_sql(query, conn)

def obter_usuario_id(email):
    """Obtém o ID do usuário a partir do email"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT codigo FROM usuarios WHERE email = ?", (email,))
        result = cursor.fetchone()
        return result[0] if result else None

def definir_barragem_analise(barragem_id):
    """Marca uma barragem como em análise"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            # Primeiro remove qualquer análise existente
            cursor.execute("UPDATE barragens SET em_analise = 0 WHERE em_analise = 1")
            # Define a nova barragem em análise
            cursor.execute("UPDATE barragens SET em_analise = 1 WHERE id = ?", (barragem_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            print(f"Erro ao definir barragem para análise: {e}")
            return False

def obter_barragem_analise():
    """Obtém a barragem atualmente em análise"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, tipo, fundacao, localizacao FROM barragens WHERE em_analise = 1 LIMIT 1")
        return cursor.fetchone()

def listar_barragens_com_status():
    """Lista todas as barragens com status de análise"""
    with closing(conectar_db()) as conn:
        query = """
        SELECT b.id, u.nome as usuario, b.nome, b.tipo, b.fundacao, b.localizacao,
               strftime('%d/%m/%Y %H:%M', b.data_criacao) as data_criacao,
               CASE WHEN b.em_analise = 1 THEN '✅' ELSE '' END as em_analise
        FROM barragens b
        JOIN usuarios u ON b.usuario_id = u.codigo
        ORDER BY b.em_analise DESC, b.nome
        """
        return pd.read_sql(query, conn)

# ---------- Operações de Anomalias ----------
def obter_modos_falha():
    """Retorna todos os modos de falha cadastrados"""
    with closing(conectar_db()) as conn:
        return pd.read_sql("SELECT id, codigo, nome FROM modos_falha ORDER BY nome", conn)

def obter_materiais():
    """Retorna todos os materiais cadastrados"""
    with closing(conectar_db()) as conn:
        df = pd.read_sql("SELECT id, nome FROM tipos_materiais ORDER BY nome", conn)
        return list(df.itertuples(index=False, name=None))

def obter_condicoes_criticas():
    """Retorna todas as condições críticas cadastradas"""
    with closing(conectar_db()) as conn:
        df =  pd.read_sql("SELECT id, nome FROM condicoes_criticas ORDER BY nome", conn)
        return list(df.itertuples(index=False, name=None))

# ---------- Operações de Anomalias ----------
def obter_anomalias():
    """Retorna todas as anomalias cadastradas como lista de tuplas"""
    with closing(conectar_db()) as conn:
        query = """
        SELECT a.id, a.codigo, a.nome, c.nome as categoria, l.nome as localizacao
        FROM anomalias a
        JOIN categorias_anomalias c ON a.categoria_id = c.id
        JOIN localizacoes_anomalias l ON a.localizacao_id = l.id
        ORDER BY a.nome
        """
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()


def inserir_anomalia(codigo, nome, descricao, categoria_id, localizacao_id, gravidade_padrao=None, referencia_tecnica=None):
    """
    Insere uma nova anomalia na base de dados
    Retorna o ID da anomalia inserida em caso de sucesso
    """
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            # Verifica se código já existe
            cursor.execute("SELECT id FROM anomalias WHERE codigo = ?", (codigo,))
            if cursor.fetchone():
                raise ValueError("Anomalia com este código já existe")
            
            # Verifica existência das FKs
            cursor.execute("SELECT id FROM categorias_anomalias WHERE id = ?", (categoria_id,))
            if not cursor.fetchone():
                raise ValueError("Categoria de anomalia não encontrada")
                
            cursor.execute("SELECT id FROM localizacoes_anomalias WHERE id = ?", (localizacao_id,))
            if not cursor.fetchone():
                raise ValueError("Localização de anomalia não encontrada")
            
            # Insere nova anomalia
            cursor.execute("""
                INSERT INTO anomalias 
                (codigo, nome, descricao, categoria_id, localizacao_id, gravidade_padrao, referencia_tecnica)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (codigo, nome, descricao, categoria_id, localizacao_id, gravidade_padrao, referencia_tecnica))
            
            conn.commit()
            return cursor.lastrowid
        except ValueError as ve:
            raise ve
        except Exception as e:
            conn.rollback()
            logging.error(f"Erro ao inserir anomalia: {str(e)}")
            raise Exception("Erro interno ao cadastrar anomalia")

def listar_anomalias(filtro_codigo=None, filtro_categoria=None, filtro_localizacao=None):
    """
    Lista anomalias com possibilidade de filtros
    Retorna lista de tuplas (id, codigo, nome, descricao, categoria_id, localizacao_id, 
                            gravidade_padrao, referencia_tecnica, categoria_nome, localizacao_nome)
    """
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            query = """
                SELECT a.id, a.codigo, a.nome, a.descricao, 
                       a.categoria_id, a.localizacao_id, 
                       a.gravidade_padrao, a.referencia_tecnica,
                       c.nome as categoria_nome, 
                       l.nome as localizacao_nome
                FROM anomalias a
                JOIN categorias_anomalias c ON a.categoria_id = c.id
                JOIN localizacoes_anomalias l ON a.localizacao_id = l.id
                WHERE 1=1
            """
            params = []
            
            if filtro_codigo:
                query += " AND a.codigo LIKE ?"
                params.append(f"%{filtro_codigo}%")
                
            if filtro_categoria:
                query += " AND a.categoria_id = ?"
                params.append(filtro_categoria)
                
            if filtro_localizacao:
                query += " AND a.localizacao_id = ?"
                params.append(filtro_localizacao)
                
            query += " ORDER BY a.codigo"
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Erro ao listar anomalias: {str(e)}")
            raise Exception("Erro ao recuperar anomalias")

def atualizar_anomalia(anomalia_id, codigo, nome, descricao, categoria_id, localizacao_id, 
                      gravidade_padrao=None, referencia_tecnica=None):
    """
    Atualiza uma anomalia existente
    Retorna True em caso de sucesso
    """
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            # Verifica se anomalia existe
            cursor.execute("SELECT id FROM anomalias WHERE id = ?", (anomalia_id,))
            if not cursor.fetchone():
                raise ValueError("Anomalia não encontrada")
            
            # Verifica se novo código já existe em outro registro
            cursor.execute("SELECT id FROM anomalias WHERE codigo = ? AND id != ?", 
                         (codigo, anomalia_id))
            if cursor.fetchone():
                raise ValueError("Outra anomalia já usa este código")
            
            # Verifica existência das FKs
            cursor.execute("SELECT id FROM categorias_anomalias WHERE id = ?", (categoria_id,))
            if not cursor.fetchone():
                raise ValueError("Categoria de anomalia não encontrada")
                
            cursor.execute("SELECT id FROM localizacoes_anomalias WHERE id = ?", (localizacao_id,))
            if not cursor.fetchone():
                raise ValueError("Localização de anomalia não encontrada")
            
            # Atualiza anomalia
            cursor.execute("""
                UPDATE anomalias
                SET codigo = ?,
                    nome = ?,
                    descricao = ?,
                    categoria_id = ?,
                    localizacao_id = ?,
                    gravidade_padrao = ?,
                    referencia_tecnica = ?
                WHERE id = ?
            """, (codigo, nome, descricao, categoria_id, localizacao_id, 
                 gravidade_padrao, referencia_tecnica, anomalia_id))
            
            conn.commit()
            return True
        except ValueError as ve:
            raise ve
        except Exception as e:
            conn.rollback()
            logging.error(f"Erro ao atualizar anomalia: {str(e)}")
            raise Exception("Erro interno ao atualizar anomalia")

def excluir_anomalia(anomalia_id):
    """
    Exclui uma anomalia
    Retorna True em caso de sucesso
    """
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            # Verifica se anomalia existe
            cursor.execute("SELECT id FROM anomalias WHERE id = ?", (anomalia_id,))
            if not cursor.fetchone():
                raise ValueError("Anomalia não encontrada")
                
            # Verifica referências (exemplo - ajustar conforme seu modelo)
            cursor.execute("SELECT 1 FROM barragens_anomalias WHERE anomalia_id = ? LIMIT 1", (anomalia_id,))
            if cursor.fetchone():
                raise ValueError("Anomalia está em uso e não pode ser excluída")
            
            cursor.execute("DELETE FROM anomalias WHERE id = ?", (anomalia_id,))
            conn.commit()
            return True
        except ValueError as ve:
            raise ve
        except Exception as e:
            conn.rollback()
            logging.error(f"Erro ao excluir anomalia: {str(e)}")
            raise Exception("Erro interno ao excluir anomalia")

def obter_anomalia(anomalia_id):
    """
    Obtém os detalhes de uma anomalia específica
    Retorna uma tupla com os dados ou None se não encontrado
    """
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT a.id, a.codigo, a.nome, a.descricao, 
                       a.categoria_id, a.localizacao_id, 
                       a.gravidade_padrao, a.referencia_tecnica,
                       c.nome as categoria_nome, 
                       l.nome as localizacao_nome
                FROM anomalias a
                JOIN categorias_anomalias c ON a.categoria_id = c.id
                JOIN localizacoes_anomalias l ON a.localizacao_id = l.id
                WHERE a.id = ?
            """, (anomalia_id,))
            return cursor.fetchone()
        except Exception as e:
            logging.error(f"Erro ao obter anomalia: {str(e)}")
            raise Exception("Erro ao recuperar anomalia")

def listar_categorias_anomalias():
    """Lista todas as categorias de anomalias"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, nome FROM categorias_anomalias ORDER BY nome")
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Erro ao listar categorias: {str(e)}")
            raise Exception("Erro ao recuperar categorias")

def listar_localizacoes_anomalias():
    """Lista todas as localizações de anomalias"""
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, nome FROM localizacoes_anomalias ORDER BY nome")
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Erro ao listar localizações: {str(e)}")
            raise Exception("Erro ao recuperar localizações")



def inferir_modos_falha(tipo_barragem_id, tipo_fundacao_id, materiais_ids, condicoes_ids, anomalias_ids):
    """Identifica modos de falha com base nos parâmetros fornecidos"""
    with closing(conectar_db()) as conn:
        # Consulta complexa que cruza todos os fatores
        query = """
        SELECT mf.id, mf.codigo, mf.nome, mf.descricao,
               COALESCE(MAX(bmf.relevancia), 0) as peso_barragem,
               COALESCE(MAX(fms.peso), 0) as peso_materiais,
               COALESCE(SUM(fcc.peso_relativo), 0) as peso_condicoes,
               COALESCE(SUM(fa.importancia), 0) as peso_anomalias
        FROM modos_falha mf
        LEFT JOIN barragem_modos_falha bmf ON mf.id = bmf.modo_falha_id AND bmf.tipo_barragem_id = ?
        LEFT JOIN falha_materiais_suscetiveis fms ON mf.id = fms.modo_falha_id AND fms.material_id IN ({})
        LEFT JOIN falha_condicoes_criticas fcc ON mf.id = fcc.modo_falha_id AND fcc.condicao_id IN ({})
        LEFT JOIN falha_anomalias fa ON mf.id = fa.modo_falha_id AND fa.anomalia_id IN ({})
        GROUP BY mf.id
        ORDER BY (peso_barragem + peso_materiais + peso_condicoes + peso_anomalias) DESC
        """.format(
            ','.join(['?']*len(materiais_ids)),
            ','.join(['?']*len(condicoes_ids)),
            ','.join(['?']*len(anomalias_ids))
        )
        
        params = [tipo_barragem_id] + materiais_ids + condicoes_ids + anomalias_ids
        resultados = pd.read_sql(query, conn, params=params)
        
        # Adicionar nível de risco
        if not resultados.empty:
            query_risco = """
            SELECT mf.id, nr.nivel, nr.cor_alerta, cr.acao_especifica
            FROM modos_falha mf
            JOIN criterios_risco cr ON mf.id = cr.modo_falha_id
            JOIN niveis_risco nr ON cr.nivel_risco_id = nr.id
            WHERE mf.id IN ({})
            """.format(','.join(['?']*len(resultados['id'].tolist())))
            
            riscos = pd.read_sql(query_risco, conn, params=resultados['id'].tolist())
            resultados = resultados.merge(riscos, on='id')
        
        return resultados


# ------------- Cadastro de Materiais -------------
def inserir_material(nome, descricao, classificacao, propriedades_json):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        print(1)
        try:
            cursor.execute("""
                INSERT INTO tipos_materiais (nome, descricao, classificacao_unificada, propriedades_json)
                VALUES (?, ?, ?, ?)
            """, (nome, descricao, classificacao, propriedades_json))
            conn.commit()
            return True
        except Exception as e:
            print("Erro ao inserir material:", e)
            return False

def listar_materiais():
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, descricao, classificacao_unificada, propriedades_json FROM tipos_materiais")
        return cursor.fetchall()

def excluir_material(material_id):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM tipos_materiais WHERE id = ?", (material_id,))
            conn.commit()
            return True
        except Exception as e:
            print("Erro ao excluir material:", e)
            return False

# ------------- Cadastro de Condições Críticas -------------
def inserir_condicao_critica(nome, tipo_condicao, descricao, referencia_tecnica):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO condicoes_criticas (nome, tipo_condicao, descricao, referencia_tecnica)
                VALUES (?, ?, ?, ?)
            """, (nome, tipo_condicao, descricao, referencia_tecnica))
            conn.commit()
            return True
        except Exception as e:
            print("Erro ao inserir condição crítica:", e)
            return False

def listar_condicoes_criticas():
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, tipo_condicao, descricao, referencia_tecnica FROM condicoes_criticas")
        return cursor.fetchall()

def excluir_condicao_critica(condicao_id):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM condicoes_criticas WHERE id = ?", (condicao_id,))
            conn.commit()
            return True
        except Exception as e:
            print("Erro ao excluir condição crítica:", e)
            return False


# Inicializa o banco de dados
inicializar_bd()