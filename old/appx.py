import streamlit as st
import sqlite3
import hashlib
import re
import pandas as pd  # Adicionado para exibição de dados
from contextlib import closing

# Importa as funções do db.py
try:
    from dbx import (
        criar_barragem, listar_barragens, obter_usuario_id,
        obter_tipos_barragem, obter_tipos_fundacao
    )
except ImportError as e:
    st.error(f"Erro ao importar do módulo db: {e}")
    st.stop()

# Configuração da página
st.set_page_config(page_title="Sistema inSID", page_icon="🔐", layout="wide")

# ---------- Conexão com o Banco de Dados ----------
def conectar_db():
    return sqlite3.connect('inSID.db')

# Função simplificada caso db.py não esteja disponível
if 'criar_barragem' not in locals():
    def criar_barragem(usuario_id, nome, tipo, fundacao, localizacao):
        pass

# ---------- Funções Utilitárias ----------
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_credenciais(email, senha):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 1 FROM usuarios 
        WHERE email = ? AND senha_hash = ? AND LOWER(ativo) = 'sim'
        """, (email, hash_senha(senha)))
        return cursor.fetchone() is not None

def email_valido(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def obter_proximo_codigo():
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(CAST(codigo AS INTEGER)) FROM usuarios")
        max_codigo = cursor.fetchone()[0]
        return str(max_codigo + 1) if max_codigo is not None else "1"

def verificar_email_existente(email):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,))
        return cursor.fetchone() is not None

# ---------- Página de Cadastro ----------
def pagina_cadastro():
    st.subheader("📝 Cadastro de Novo Usuário")

    proximo_codigo = obter_proximo_codigo()

    with st.form("cadastro_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Código do Usuário", value=proximo_codigo, disabled=True)
            nome = st.text_input("Nome Completo", max_chars=100)
            funcao = st.text_input("Função/Cargo", max_chars=50)
            organizacao = st.text_input("Organização", max_chars=100)

        with col2:
            email = st.text_input("Email", max_chars=100)
            senha = st.text_input("Senha", type="password", max_chars=50)
            confirmar_senha = st.text_input("Confirmar Senha", type="password", max_chars=50)
            ativo = st.selectbox("Usuário Ativo?", ["sim", "não"])

        enviar = st.form_submit_button("Cadastrar")

        if enviar:
            if not email_valido(email):
                st.error("❌ Email inválido.")
            elif senha != confirmar_senha:
                st.error("❌ As senhas não coincidem.")
            elif len(senha) < 6:
                st.error("❌ A senha deve ter pelo menos 6 caracteres.")
            elif verificar_email_existente(email):
                st.warning("⚠️ Este email já está cadastrado.")
            else:
                novo_usuario = {
                    "codigo": proximo_codigo,
                    "nome": nome,
                    "email": email,
                    "funcao": funcao,
                    "organizacao": organizacao,
                    "senha_hash": hash_senha(senha),
                    "ativo": ativo
                }
                salvar_usuario(novo_usuario)
                st.success(f"✅ Usuário '{nome}' cadastrado com sucesso!")
                st.balloons()

def salvar_usuario(novo_usuario):
    with closing(conectar_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO usuarios (codigo, nome, email, funcao, organizacao, senha_hash, ativo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            novo_usuario['codigo'],
            novo_usuario['nome'],
            novo_usuario['email'],
            novo_usuario['funcao'],
            novo_usuario['organizacao'],
            novo_usuario['senha_hash'],
            novo_usuario['ativo']
        ))
        conn.commit()

# ---------- Página de Login ----------
def pagina_login():
    st.title("🔐 Bem-vindo ao Sistema inSID")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("inSID_logo.jpg", caption="Metodologia inSID", width=150)
    with col2:
        with st.form("login_form"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar")

            if entrar:
                if verificar_credenciais(email, senha):
                    st.session_state['logado'] = True
                    st.session_state['email'] = email
                    st.success("✅ Login efetuado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas ou usuário inativo.")

# ---------- Página Principal ----------
def pagina_principal():
    st.title("📊 Página Inicial - Sistema inSID")
    st.write(f"👤 Usuário logado: `{st.session_state['email']}`")

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

# ---------- Página de Cadastro de Barragens ----------
def pagina_cadastro_barragem():
    st.title("📋 Cadastro de Barragens")

    aba = st.sidebar.selectbox("Selecione a opção", ["Cadastrar", "Visualizar"])

    if aba == "Cadastrar":
        st.subheader("➕ Nova Barragem")

        tipos_barragem = obter_tipos_barragem()
        tipos_fundacao = obter_tipos_fundacao()

        if not tipos_barragem or not tipos_fundacao:
            st.error("⚠️ Erro ao carregar tipos de barragem ou fundação.")
            return

        nome_tipos_barragem = [tipo[1] for tipo in tipos_barragem]
        nome_tipos_fundacao = [tipo[1] for tipo in tipos_fundacao]

        nome = st.text_input("Nome da Barragem")
        tipo_selecionado = st.selectbox("Tipo de Barragem", nome_tipos_barragem)
        fundacao_selecionada = st.selectbox("Tipo de Fundação", nome_tipos_fundacao)
        localizacao = st.text_input("Localização (latitude,longitude)")

        if st.button("Salvar"):
            email_logado = st.session_state.get("email")
            usuario_id = obter_usuario_id(email_logado)

            if usuario_id and nome and tipo_selecionado and fundacao_selecionada and localizacao:
                criar_barragem(usuario_id, nome, tipo_selecionado, fundacao_selecionada, localizacao)
                st.success("✅ Barragem cadastrada com sucesso!")
            else:
                st.warning("⚠️ Preencha todos os campos.")

    elif aba == "Visualizar":
        st.subheader("📄 Barragens Cadastradas")
        dados = listar_barragens()
        if dados:
            st.dataframe(dados, use_container_width=True)
        else:
            st.info("Nenhuma barragem cadastrada ainda.")

# ---------- Função Principal ----------
def main():
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
        st.session_state['pagina'] = "login"

    if not st.session_state['logado']:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Cadastro"])
        with tab1:
            pagina_login()
        with tab2:
            pagina_cadastro()
    else:
        if st.session_state.get('pagina') == "cadastro_barragem":
            pagina_cadastro_barragem()
            if st.button("⬅️ Voltar"):
                st.session_state['pagina'] = "principal"
                st.rerun()
        else:
            pagina_principal()
            if st.button("➕ Cadastrar Barragem"):
                st.session_state['pagina'] = "cadastro_barragem"
                st.rerun()


if __name__ == "__main__":
    main()