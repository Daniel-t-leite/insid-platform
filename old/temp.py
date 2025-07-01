import sqlite3
import json
from contextlib import closing
import streamlit as st

# Lista de materiais para construção de barragens
MATERIAIS_BARRAGEM = [
    {
        "nome": "Concreto Compactado com Rolo (CCR)",
        "descricao": "Concreto de baixo teor de cimento compactado com rolo vibratório",
        "classificacao_unificada": "MCC-01",
        "propriedades_json": json.dumps({
            "resistencia_compressao_28d": "15-25 MPa",
            "modulo_elasticidade": "15-25 GPa",
            "permeabilidade": "10^-8 - 10^-10 m/s",
            "teor_cimento": "60-120 kg/m³"
        })
    },
    {
        "nome": "Enrocamento",
        "descricao": "Rochas de tamanho variado para construção de barragens de enrocamento",
        "classificacao_unificada": "MEN-02",
        "propriedades_json": json.dumps({
            "dimensoes_typical": "0.3-1.0 m",
            "densidade_aparente": "1.8-2.2 t/m³",
            "angulo_atrito": "35-45°",
            "permeabilidade": "10^-1 - 10^-3 m/s"
        })
    },
    {
        "nome": "Terra Homogênea",
        "descricao": "Material terroso compactado para núcleo de barragens",
        "classificacao_unificada": "MTH-03",
        "propriedades_json": json.dumps({
            "plasticidade": "IP = 10-30",
            "compactacao": "95% Proctor",
            "permeabilidade": "10^-6 - 10^-8 m/s",
            "umidade_otima": "12-18%"
        })
    }
]

def conectar_db():
    """Estabelece conexão com o banco de dados"""
    return sqlite3.connect('inSID.db')

def criar_tabela_materiais():
    """Cria a tabela tipos_materiais se não existir"""
    try:
        with closing(conectar_db()) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tipos_materiais (
                    id INTEGER PRIMARY KEY,
                    nome TEXT UNIQUE NOT NULL,
                    descricao TEXT,
                    classificacao_unificada TEXT,
                    propriedades_json TEXT
                )
            """)
            conn.commit()
    except Exception as e:
        st.error(f"Erro ao criar tabela: {str(e)}")

def tabela_materiais_vazia():
    """Verifica se a tabela de materiais está vazia"""
    try:
        with closing(conectar_db()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tipos_materiais")
            return cursor.fetchone()[0] == 0
    except:
        return True  # Se a tabela não existir, considera como vazia

def popular_tabela_materiais():
    """Insere os materiais padrão na tabela tipos_materiais"""
    try:
        with closing(conectar_db()) as conn:
            cursor = conn.cursor()
            
            # Verifica se a tabela está vazia
            cursor.execute("SELECT COUNT(*) FROM tipos_materiais")
            if cursor.fetchone()[0] > 0:
                st.warning("A tabela já contém registros. Operação cancelada.")
                return False
            
            # Prepara a query de inserção
            query = """
            INSERT INTO tipos_materiais (nome, descricao, classificacao_unificada, propriedades_json)
            VALUES (?, ?, ?, ?)
            """
            
            # Prepara os valores para inserção
            valores = [
                (mat["nome"], mat["descricao"], mat["classificacao_unificada"], mat["propriedades_json"])
                for mat in MATERIAIS_BARRAGEM
            ]
            
            # Executa a inserção em massa
            cursor.executemany(query, valores)
            conn.commit()
            
            st.success(f"✅ {len(MATERIAIS_BARRAGEM)} materiais foram inseridos com sucesso!")
            return True
            
    except sqlite3.IntegrityError as e:
        st.error(f"Erro de integridade: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Erro ao popular tabela: {str(e)}")
        return False

def limpar_tabela_materiais():
    """Remove todos os registros da tabela de materiais"""
    try:
        with closing(conectar_db()) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tipos_materiais")
            conn.commit()
            st.success("Tabela de materiais limpa com sucesso!")
            return True
    except Exception as e:
        st.error(f"Erro ao limpar tabela: {str(e)}")
        return False

def pagina_popular_materiais():
    """Página para popular a tabela de materiais"""
    st.title("📦 Popular Tabela de Materiais")
    
    criar_tabela_materiais()
    
    if tabela_materiais_vazia():
        st.warning("A tabela de materiais está vazia.")
        if st.button("Popular Tabela com Materiais Padrão"):
            if popular_tabela_materiais():
                st.rerun()
    else:
        st.success("A tabela já contém materiais cadastrados.")
        if st.button("Limpar e Recriar Tabela", type="secondary"):
            if limpar_tabela_materiais():
                st.rerun()
    
    # Mostra os materiais que serão inseridos
    st.subheader("Materiais Padrão")
    st.json(MATERIAIS_BARRAGEM)

# Execução principal
if __name__ == "__main__":
    pagina_popular_materiais()
    