import streamlit as st
import re
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, JsCode
# import logging


from db import (
    criar_usuario, verificar_credenciais, email_existe,
    obter_proximo_codigo_usuario, obter_tipos_barragem, 
    definir_barragem_analise, obter_barragem_analise, 
    obter_barragens_usuario, atualizar_barragem, excluir_barragem, 
    cadastrar_barragem, listar_usuarios, atualizar_status_usuario, 
    atualizar_admin_usuario, excluir_usuario
 
)

# Configuração da página
st.set_page_config(page_title="Sistema inSID", page_icon="🔐", layout="wide")

# ---------- Funções Utilitárias ----------
def email_valido(email):
    """Valida o formato do email"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# ---------- Páginas ----------
def pagina_cadastro():
    """Página de cadastro de novos usuários"""
    st.subheader("📝 Cadastro de Novo Usuário")
    proximo_codigo = obter_proximo_codigo_usuario()

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
            elif email_existe(email):
                st.warning("⚠️ Este email já está cadastrado.")
            else:
                if criar_usuario(proximo_codigo, nome, email, funcao, organizacao, senha, ativo):
                    st.success(f"✅ Usuário '{nome}' cadastrado com sucesso!")
                    st.balloons()
                else:
                    st.error("❌ Erro ao cadastrar usuário.")




def pagina_principal():
    """Página principal após login com gestão completa de barragens"""
    st.title("📊 Página Inicial - Sistema inSID")
    st.write(f"👤 Usuário logado: {st.session_state['usuario_nome']}")
    
    # Barra de seleção de barragem em análise
    st.subheader("🔍 Barragem em Análise")
    barragens_usuario = obter_barragens_usuario(st.session_state['usuario_id'])
    barragem_analise = obter_barragem_analise(st.session_state['usuario_id'])

    if barragem_analise:
        st.success(f"Barragem atual em análise:  [id: {barragem_analise[0]}] - {barragem_analise[2]}")

    else:
        st.warning("Nenhuma barragem selecionada para análise")
    
    if barragens_usuario:
        # Seleciona a barragem atual em análise ou vazio se nenhuma
        barragem_selecionada = str(barragem_analise[0]) if barragem_analise else ""
        
        # Cria lista de opções para o selectbox
        opcoes_barragens = {str(b[0]): f"{b[1]} (ID: {b[0]})" for b in barragens_usuario}
        opcoes_barragens[""] = "Selecione uma barragem..."
        
              
        # Widget para seleção/edição da barragem em análise
        col1, col2 = st.columns([3, 1])
        with col1:
            nova_barragem = st.selectbox(
                "Selecione a barragem para análise:",
                options=opcoes_barragens.keys(),
                format_func=lambda x: opcoes_barragens.get(x, "Selecione..."),
                index=list(opcoes_barragens.keys()).index(barragem_selecionada) if barragem_selecionada else 0
            )
        
        with col2:
            st.write("")  # Espaçamento
            st.write("")  # Espaçamento
            if st.button("💾 Salvar Seleção"):
                if nova_barragem:
                    definir_barragem_analise(st.session_state['usuario_id'], int(nova_barragem))
                    st.success(f"Barragem {opcoes_barragens[nova_barragem]} definida para análise!")
                    st.rerun()
                else:
                    st.error("Selecione uma barragem válida")

        # Mostra detalhes da barragem em análise
        if barragem_analise:
            with st.expander("📝 Editar Barragem"):
                editar_barragem(barragem_analise)
   

            
        
        
    else:
        st.warning("Você ainda não cadastrou nenhuma barragem")
    
    # Seção de ações principais
    st.subheader("📋 Ações")
    col1, col2, col3 = st.columns(3)
    
    with col2:  
        if st.button("🔍 Identificar Modos de Falha"):
            if barragem_analise:
                st.session_state['pagina'] = "identificacao_falhas"
                st.rerun()
            else:
                st.error("Selecione uma barragem para análise primeiro")
        
        
    
    # Seção de administração (se for admin)
    if st.session_state.get('is_admin'):
        st.sidebar.subheader("🛡️ Administração")
        if st.sidebar.button("👥 Gerenciar Usuários"):
            st.session_state['pagina'] = "admin_usuarios"
            st.rerun()
    
    if st.sidebar.button("➕ Cadastrar Nova Barragem"):
        st.session_state['pagina'] = "cadastro_barragem"
        st.rerun()

    # Botão de logout
    st.sidebar.button("🚪 Sair", on_click=logout)

def pagina_admin_usuarios():
    """Página de administração de usuários"""
    st.title("👥 Administração de Usuários")
    
    # Lista de usuários em formato de tabela editável
    usuarios = listar_usuarios()
    
    if not usuarios.empty:
        # Exibir tabela com opções de edição
        for _, usuario in usuarios.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                st.write(f"**{usuario['nome']}**")
                st.caption(f"Email: {usuario['email']}")
                st.caption(f"Criado em: {usuario['data_criacao']}")
            
            with col2:
                novo_status = st.selectbox(
                    "Status",
                    ["sim", "não"],
                    index=0 if usuario['ativo'] == "sim" else 1,
                    key=f"status_{usuario['codigo']}"
                )
                if novo_status != usuario['ativo']:
                    if st.button("Atualizar Status", key=f"upd_status_{usuario['codigo']}"):
                        if atualizar_status_usuario(usuario['codigo'], novo_status):
                            st.success("Status atualizado!")
                            st.rerun()
            
            with col3:
                admin_status = st.checkbox(
                    "Administrador",
                    value=bool(usuario['is_admin']),
                    key=f"admin_{usuario['codigo']}"
                )
                if admin_status != usuario['is_admin']:
                    if st.button("Atualizar Acesso", key=f"upd_admin_{usuario['codigo']}"):
                        if atualizar_admin_usuario(usuario['codigo'], int(admin_status)):
                            st.success("Acesso atualizado!")
                            st.rerun()
            
            with col4:
                if usuario['email'] != "admin@insid.com":  # Não permitir excluir o admin principal
                    if st.button("Excluir", key=f"del_{usuario['codigo']}"):
                        if excluir_usuario(usuario['codigo']):
                            st.success("Usuário excluído!")
                            st.rerun()
                else:
                    st.write("")  # Espaço vazio para alinhamento
    else:
        st.warning("Nenhum usuário cadastrado.")

    # Adicionar espaço e botão de voltar
    st.write("")
    if st.button("⬅️ Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()



def pagina_cadastro_barragem():
    """Página para cadastro de novas barragens"""
    st.title("📝 Cadastro de Nova Barragem")
    
    # Voltar para página principal
    if st.button("⬅️ Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()

    st.subheader("Informações Básicas")
    nome = st.text_input("Nome da Barragem*", placeholder="Ex: Barragem do Rio Preto")
    tipo = st.selectbox(
        "Tipo de Barragem*", 
        options=[t[1] for t in obter_tipos_barragem()],
        help="Selecione o tipo construtivo da barragem"
    )
    localizacao = st.text_input("Localização*", placeholder="Ex: Município/Estado")

    st.subheader("Dimensões")
    col1, col2 = st.columns(2)
    with col1:
        altura = st.number_input("Altura (m)*", min_value=0.0, step=0.1, format="%.1f", key="altura_input")
    with col2:
        comprimento = st.number_input("Comprimento (m)*", min_value=0.0, step=0.1, format="%.1f", key="comprimento_input")

    # Cálculo dinâmico da relação Corda/Altura
    if altura > 0:
        rel_cordaaltura = round(comprimento / altura, 1)
        st.success(f"📐 Relação Corda/Altura: **{rel_cordaaltura:.1f}**")
    else:
        rel_cordaaltura = 0.0
        st.warning("⚠️ Informe um valor de altura maior que zero para calcular a relação Corda/Altura.")

    # Formulário de envio
    sucesso_cadastro = False
    with st.form("form_cadastro_barragem"):
        submitted = st.form_submit_button("Cadastrar Barragem")

        if submitted:
            if not nome or not tipo or not localizacao or altura == 0 or comprimento == 0:
                st.error("Preencha todos os campos obrigatórios (*) e certifique-se de que altura e comprimento sejam maiores que zero.")
            else:
                try:
                    cadastrar_barragem(
                        st.session_state['usuario_id'],
                        nome,
                        tipo,
                        localizacao,
                        altura,
                        comprimento,
                        rel_cordaaltura
                    )
                    st.success("✅ Barragem cadastrada com sucesso!")
                    sucesso_cadastro = True
                except Exception as e:
                    st.error(f"Erro ao cadastrar barragem: {str(e)}")

    # Botão externo ao formulário (ativado apenas após sucesso)
    if sucesso_cadastro:
        if st.button("📌 Definir como Barragem em Análise"):
            barragens = obter_barragens_usuario(st.session_state['usuario_id'])
            if barragens:
                ultima_barragem = barragens[-1][0]
                definir_barragem_analise(st.session_state['usuario_id'], ultima_barragem)
                st.success("Barragem definida para análise!")
                st.session_state['pagina'] = "principal"
                st.rerun()




def editar_barragem(barragem):
    """Formulário para edição de barragem existente"""
    with st.form("editar_barragem_form"):
        nome = st.text_input("Nome", value=barragem[2])


        # Lista de tipos de barragem: (id, nome)
        tipos = obter_tipos_barragem()

        # Criar dicionário nome -> id
        opcoes = {t[1]: t[0] for t in tipos}

        # Criar dicionário inverso id -> nome (para uso no valor inicial)
        id_para_nome = {t[0]: t[1] for t in tipos}

        # tipo_id previamente armazenado
    
        tipo_id_atual = barragem[3]

        # Obter nome correspondente ao ID atual (ou "" se não encontrado)
        tipo_nome_atual = id_para_nome.get(tipo_id_atual, "")

        print(id_para_nome)

        print(tipo_id_atual)

        print(tipo_nome_atual)

        # Selectbox que mostra o nome e armazena o ID
        tipo_nome = st.selectbox(
            "Tipo de Barragem*",
            options=list(opcoes.keys()),
            index=list(opcoes.keys()).index(tipo_nome_atual) if tipo_nome_atual in opcoes else 0,
            help="Selecione o tipo construtivo da barragem"
        )

        # Recuperar o tipo_id correspondente ao nome selecionado
        tipo_id = opcoes[tipo_nome]

        # Atribuir tipo_id final
        tipo = tipo_id

        localizacao = st.text_input("Localização", value=barragem[4])
        altura = st.number_input("Altura (m)", value=barragem[5], min_value=0.0)
        comprimento = st.number_input("Comprimento (m)", value=barragem[6], min_value=0.0)
        rel_cordaaltura = st.number_input("Relação Corda/Altura", value=barragem[7], min_value=0.0)
        
        col1, col2, col3 = st.columns(3)
        with col2:
            submitted1 = st.form_submit_button("🗑️ Excluir")
            if submitted1:
                excluir_barragem(barragem[0])
                st.success("Barragem excluida com sucesso!")
                st.rerun()

        with col3:
            submitted = st.form_submit_button("Salvar Alterações")
            if submitted:
                atualizar_barragem(
                    barragem[0], nome, tipo, localizacao, altura, comprimento, rel_cordaaltura
                )
                st.success("Barragem atualizada com sucesso!")
                st.rerun()

import streamlit as st

# def mostrar_lista_barragens(barragens):
#     """Mostra lista de barragens com exclusão segura"""
#     st.subheader("📋 Lista de Barragens Cadastradas")
    
#     if not barragens:
#         st.warning("Nenhuma barragem cadastrada")
#         return
    
#     print("pt01")

#     for barragem in barragens:
#         barragem_id = barragem[0]
        
#         print("pt02")
#         with st.expander(f"{barragem[1]} (ID: {barragem_id})"):
#             # Informações da barragem
#             print("pt03")
#             st.write(f"**Tipo:** {barragem[2]}")
#             st.write(f"**Localização:** {barragem[3]}")
#             st.write(f"**Altura:** {barragem[4]} m")
#             st.write(f"**Comprimento:** {barragem[5]} m")
            
            
#             # Botões de ação
#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button("Selecionar", key=f"select_{barragem_id}"):
#                     definir_barragem_analise(st.session_state['usuario_id'], barragem_id)
#                     st.success(f"Barragem {barragem[1]} selecionada!")
#                     st.rerun()
            
#             with col2:
#                 print("pt04")
#                 # Botão de exclusão principal
#                 if st.button("🗑️ Excluir", key=f"delete_{barragem_id}"):
#                     st.session_state['excluindo'] = barragem_id  # Marca para confirmação
#                     print("pt05")
#                     st.rerun()
#                 print("pt06")
#                 # Diálogo de confirmação (aparece apenas para a barragem marcada)
#                 if st.session_state.get('excluindo') == barragem_id:
#                     print("pt07")
#                     st.error("⚠️ Confirmar exclusão permanente?")
                    
#                     col_confirm, col_cancel = st.columns(2)
#                     with col_confirm:
#                         if st.button("✅ Sim, excluir", key=f"confirm_{barragem_id}"):
#                             excluir_barragem(barragem_id)
#                             st.session_state.pop('excluindo')  # Limpa o estado
#                             st.success("Barragem excluída!")
#                             st.rerun()
                    
#                     with col_cancel:
#                         if st.button("❌ Cancelar", key=f"cancel_{barragem_id}"):
#                             st.session_state.pop('excluindo')
#                             st.rerun()

              
def mostrar_lista_barragens(barragens):
    """Mostra lista de barragens com exclusão segura"""
    st.subheader("📋 Lista de Barragens Cadastradas")
    
    if not barragens:
        st.warning("Nenhuma barragem cadastrada")
        return

    for barragem in barragens:
        barragem_id = barragem[0]
        nome_barragem = barragem[1]

        with st.expander(f"{nome_barragem} (ID: {barragem_id})"):
            st.write(f"**Tipo:** {barragem[2]}")
            st.write(f"**Localização:** {barragem[3]}")
            st.write(f"**Altura:** {barragem[4]} m")
            st.write(f"**Comprimento:** {barragem[5]} m")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Selecionar para Análise", key=f"select_{barragem_id}"):
                    definir_barragem_analise(st.session_state['usuario_id'], barragem_id)
                    st.success(f"✅ Barragem **{barragem_nome}** selecionada para análise!")
                    st.rerun()

            with col2:
                if st.button("🗑️ Excluir", key=f"delete_{barragem_id}"):
                    st.session_state[f'confirm_{barragem_id}'] = True
                    st.rerun()


                  



def pagina_login():
    """Página de login"""
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
                resultado = verificar_credenciais(email, senha)
                if resultado:
                    usuario_id, nome, is_admin = resultado
                    st.session_state.update({
                        'logado': True,
                        'email': email,
                        'usuario_id': usuario_id,
                        'usuario_nome': nome,
                        'is_admin': bool(is_admin)
                    })
                    st.success(f"✅ Bem-vindo, {nome}!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas ou usuário inativo.")

def logout():
    """Limpa a sessão e volta para o login"""
    st.session_state.clear()
    st.rerun()


def main():
    """Função principal que controla o fluxo do aplicativo"""
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
        elif st.session_state.get('pagina') == "admin_usuarios" and st.session_state.get('is_admin'):
            pagina_admin_usuarios()
        elif st.session_state.get('pagina') == "identificacao_falhas":
            pagina_identificacao_falhas()
        else:
            pagina_principal()

if __name__ == "__main__":
    main()