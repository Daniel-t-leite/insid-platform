import sqlite3
import streamlit as st
import re
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, JsCode
# import logging
import os
import time
from datetime import datetime


from db import (
    conectar_db, criar_usuario, verificar_credenciais, email_existe,
    obter_proximo_codigo_usuario, obter_tipos_barragem, 
    definir_barragem_analise, obter_barragem_analise, 
    obter_barragens_usuario, atualizar_barragem, excluir_barragem, 
    cadastrar_barragem, listar_usuarios, atualizar_status_usuario, 
    atualizar_admin_usuario, excluir_usuario, obter_zonas_por_barragem,
    cadastrar_zona_db, obter_todos_materiais, cadastrar_material_db, 
    obter_material_por_id, excluir_material_db, obter_materiais_por_usuario
 
)

# Configuração da página
st.set_page_config(page_title="Sistema inSID", page_icon="🔐", layout="wide")

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

def pagina_cadastro_barragem():
    """Página para cadastro de novas barragens com navegação por abas (para administradores)"""
    st.title("📝 Cadastro de barragens")

    # ========== MENU SUPERIOR COM st.tabs (RESTRITO A ADMINISTRADORES) ==========
    if st.session_state.get('is_admin', False):
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Cadastro de barragens", "Categoria de barragens", "Zonas da barragem", "Cadastro avançado"])

        with tab1:
            # Conteúdo padrão da página de cadastro
            exibir_formulario_cadastro_barragem()

        with tab2:
            listar_tipos_barragem()
            adicionar_tipo_barragem()
        
        with tab3:
            gerenciar_zonas_barragem()
            #gerenciar_tipos_materiais()

        with tab4:
            st.info("Seção de cadastro avançado — campos técnicos extras")
            # Aqui você pode adicionar campos extras ou formulário diferenciado
            #exibir_formulario_avancado()
    
    else:
        # Usuário comum vê diretamente o formulário básico
        exibir_formulario_cadastro_barragem()

def gerenciar_zonas_barragem():
    """Página principal para gerenciamento de zonas"""
    st.title("🏗️ Gerenciamento de Zonas de Barragem")
    
    # Verifica se está no modo de edição
    if st.session_state.get('pagina') == "editar_zona":
        editar_zona_barragem()
        return
    
    # Restante da lógica original
    barragem_analise = obter_barragem_analise(st.session_state['usuario_id'])
    if not barragem_analise:
        st.error("Selecione uma barragem para análise primeiro")
        if st.button("← Voltar"):
            st.session_state['pagina'] = "principal"
            st.rerun()
        return
    
    st.subheader(f"Zonas da Barragem: {barragem_analise[1]} (ID: {barragem_analise[0]})")
    
    # Abas para diferentes funcionalidades
    tab1, tab2 = st.tabs(["📋 Lista de Zonas", "➕ Nova Zona"])
    
    with tab1:
        listar_zonas_barragem(barragem_analise[0])
    
    with tab2:
        cadastrar_zona_barragem(barragem_analise[0])
    
    if st.button("← Voltar para Página Principal"):
        st.session_state['pagina'] = "principal"
        st.rerun()

# def gerenciar_zonas_barragem():
#     """Página principal para gerenciamento de zonas e modos de falha"""
#     st.title("🏗️ Gerenciamento de Zonas de Barragem")
    
#     # Verifica se há uma barragem selecionada
#     barragem_analise = obter_barragem_analise(st.session_state['usuario_id'])
#     if not barragem_analise:
#         st.error("Selecione uma barragem para análise primeiro")
#         if st.button("← Voltar"):
#             st.session_state['pagina'] = "principal"
#             st.rerun()
#         return
    
#     st.subheader(f"Zonas da Barragem: {barragem_analise[1]} (ID: {barragem_analise[0]})")
    
#     # Abas para diferentes funcionalidades
#     tab1, tab2, tab3 = st.tabs(["📋 Lista de Zonas", "➕ Nova Zona", "🧱 Materiais"])
    
#     with tab1:
#         listar_zonas_barragem(barragem_analise[0])
    
#     with tab2:
#         cadastrar_zona_barragem(barragem_analise[0])
    
#     with tab3:
#         gerenciar_tipos_materiais()
    
#     if st.button("← Voltar para Página Principal"):
#         st.session_state['pagina'] = "principal"
#         st.rerun()

# def listar_zonas_barragem(barragem_id):
#     """Lista zonas com a nova estrutura de colunas"""
#     zonas = obter_zonas_por_barragem(barragem_id)
#     print(zonas)
    
#     if not zonas:
#         st.info("Nenhuma zona cadastrada para esta barragem ainda.")
#         return
    
#     for zona in zonas:
#         with st.expander(f"Zona: {zona[4]} (ID: {zona[0]})"):  # índice 4 para nome
#             col1, col2 = st.columns([3, 1])
            
#             with col1:
#                 material = obter_material_por_id(zona[3])  # índice 3 para material_id
#                 print(material)
#                 st.write(f"**Material:** {material[2] if material else 'Não especificado'}")
#                 if zona[5]:  # índice 5 para descricao
#                     st.write(f"**Descrição:** {zona[5]}")
                
#                 # modos_falha = obter_modos_falha_por_zona(zona[0])
#                 # if modos_falha:
#                 #     st.write("**Modos de Falha Associados:**")
#                 #     for modo in modos_falha:
#                 #         st.write(f"- {modo[1]}")

def listar_zonas_barragem(barragem_id):
    """Lista todas as zonas cadastradas para uma barragem específica"""
    if not barragem_id:
        st.error("Nenhuma barragem selecionada")
        return
    
    zonas = obter_zonas_por_barragem(barragem_id)
    
    if not zonas:
        st.info("Nenhuma zona cadastrada para esta barragem ainda.")
        return
    
    for zona in zonas:
        with st.expander(f"Zona: {zona[4]} (ID: {zona[0]})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Tratamento seguro para o material
                material = obter_material_por_id(zona[3])
                material_nome = 'Não especificado'
                if material:
                    try:
                        # Acessa o nome do material de forma segura
                        material_nome = material[2] if len(material) > 2 else material[1]
                    except (IndexError, TypeError):
                        material_nome = 'Desconhecido'
                
                st.write(f"**Material:** {material_nome}")
                
                if len(zona) > 5 and zona[5]:  # Verifica se existe descrição
                    st.write(f"**Descrição:** {zona[5]}")
                
                # Tratamento seguro para modos de falha
                # modos_falha = obter_modos_falha_por_zona(zona[0])
                # if modos_falha:
                #     st.write("**Modos de Falha Associados:**")
                #     for modo in modos_falha:
                #         try:
                #             st.write(f"- {modo[1]}")
                #         except (IndexError, TypeError):
                #             st.write("- Modo de falha desconhecido")

            with col2:
                if st.button("✏️ Editar", key=f"edit_zona_{zona[0]}"):
                    st.session_state['editar_zona_id'] = zona[0]
                    st.rerun()
                
                if st.button("🗑️ Excluir", key=f"del_zona_{zona[0]}"):
                    if excluir_zona_barragem(zona[0]):
                        st.rerun()

def cadastrar_zona_barragem(barragem_id):
    """Formulário atualizado para nova estrutura"""
    with st.form("form_nova_zona", clear_on_submit=True):
        st.subheader("Cadastrar Nova Zona")
        
        # Seleção de material primeiro (nova ordem)
        materiais = obter_todos_materiais()
        material_opcoes = {m[0]: m[2] for m in materiais} if materiais else {}
        
        material_id = st.selectbox(
            "Material Principal*",
            options=list(material_opcoes.keys()),
            format_func=lambda x: material_opcoes.get(x, "Selecione...")
        )
        
        nome = st.text_input("Nome da Zona*", max_chars=50)
        descricao = st.text_area("Descrição Técnica")
        
        submitted = st.form_submit_button("Salvar Zona")
        
        if submitted:
            if not nome or not material_id:
                st.error("Preencha os campos obrigatórios (*)")
            else:
                sucesso = cadastrar_zona_db(
                    usuario_id=st.session_state['usuario_id'],
                    barragem_id=barragem_id,
                    material_id=material_id,
                    nome=nome.strip(),
                    descricao=descricao.strip() if descricao else None
                )
                
                if sucesso:
                    st.success("Zona cadastrada com sucesso!")
                    time.sleep(1)
                    st.rerun()

def atualizar_zona_db(zona_id, material_id, nome, descricao=None):
    """
    Atualiza uma zona de barragem no banco de dados
    :param zona_id: ID da zona a ser atualizada
    :param material_id: ID do material associado
    :param nome: Nome da zona
    :param descricao: Descrição técnica (opcional)
    :return: True se atualizado com sucesso, False caso contrário
    """
    conn = None
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Verifica se a zona existe
        cursor.execute("SELECT id FROM zonas_barragem WHERE id = ?", (zona_id,))
        if not cursor.fetchone():
            st.error("Zona não encontrada")
            return False
        
        # Atualiza os dados
        cursor.execute("""
            UPDATE zonas_barragem 
            SET material_id = ?, nome = ?, descricao = ?
            WHERE id = ?
        """, (material_id, nome.strip(), descricao.strip() if descricao else None, zona_id))
        
        conn.commit()
        
        # Verifica se a atualização foi bem-sucedida
        if cursor.rowcount == 1:
            st.success("Zona atualizada com sucesso!")
            return True
        else:
            st.error("Nenhuma alteração realizada")
            return False
            
    except sqlite3.IntegrityError as e:
        if "FOREIGN KEY constraint failed" in str(e):
            st.error("Material selecionado não existe")
        elif "UNIQUE constraint" in str(e):
            st.error("Já existe uma zona com este nome")
        else:
            st.error(f"Erro de integridade no banco de dados: {str(e)}")
        return False
        
    except sqlite3.Error as e:
        st.error(f"Erro no banco de dados: {str(e)}")
        return False
        
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return False
        
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass  # Garante que não falhe ao fechar conexão

def excluir_zona_barragem(zona_id):
    """
    Exclui uma zona de barragem do sistema de forma segura
    :param zona_id: ID da zona a ser excluída
    :return: 
        - True se a exclusão foi bem-sucedida
        - False se houve falha ou a zona não pode ser excluída
    """
    # Verificação inicial do ID
    try:
        zona_id = int(zona_id)
        if zona_id <= 0:
            st.error("ID da zona inválido")
            return False
    except (ValueError, TypeError):
        st.error("ID da zona deve ser um número inteiro positivo")
        return False

    conn = None
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        # 1. Verifica se a zona existe
        cursor.execute("SELECT barragem_id FROM zonas_barragem WHERE id = ?", (zona_id,))
        resultado = cursor.fetchone()
        
        if not resultado:
            st.error("Zona não encontrada")
            return False

        barragem_id = resultado[0]

        # 2. Verifica se existem modos de falha associados (se aplicável)
        cursor.execute("SELECT COUNT(*) FROM modos_falha_zona WHERE zona_id = ?", (zona_id,))
        if cursor.fetchone()[0] > 0:
            st.error("Não é possível excluir: existem modos de falha associados a esta zona")
            return False

        # 3. Executa a exclusão
        cursor.execute("DELETE FROM zonas_barragem WHERE id = ?", (zona_id,))
        conn.commit()

        # Verifica se realmente excluiu
        if cursor.rowcount == 1:
            st.success(f"Zona {zona_id} da barragem {barragem_id} excluída com sucesso!")
            return True
        else:
            st.error("Nenhuma zona foi excluída")
            return False

    except sqlite3.Error as e:
        st.error(f"Erro no banco de dados: {str(e)}")
        return False

    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return False

    finally:
        if conn:
            try:
                conn.close()
            except:
                pass  # Garante que não falhe ao fechar conexão

def atualizar_zona_db(zona_id, material_id, nome, descricao=None):
    """
    Atualiza uma zona de barragem no banco de dados
    :param zona_id: ID da zona a ser atualizada
    :param material_id: ID do material associado
    :param nome: Nome da zona
    :param descricao: Descrição técnica (opcional)
    :return: True se atualizado com sucesso, False caso contrário
    """
    conn = None
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Verifica se a zona existe
        cursor.execute("SELECT id FROM zonas_barragem WHERE id = ?", (zona_id,))
        if not cursor.fetchone():
            st.error("Zona não encontrada")
            return False
        
        # Atualiza os dados
        cursor.execute("""
            UPDATE zonas_barragem 
            SET material_id = ?, nome = ?, descricao = ?
            WHERE id = ?
        """, (material_id, nome.strip(), descricao.strip() if descricao else None, zona_id))
        
        conn.commit()
        
        # Verifica se a atualização foi bem-sucedida
        if cursor.rowcount == 1:
            st.success("Zona atualizada com sucesso!")
            return True
        else:
            st.error("Nenhuma alteração realizada")
            return False
            
    except sqlite3.IntegrityError as e:
        if "FOREIGN KEY constraint failed" in str(e):
            st.error("Material selecionado não existe")
        elif "UNIQUE constraint" in str(e):
            st.error("Já existe uma zona com este nome")
        else:
            st.error(f"Erro de integridade no banco de dados: {str(e)}")
        return False
        
    except sqlite3.Error as e:
        st.error(f"Erro no banco de dados: {str(e)}")
        return False
        
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return False
        
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass  # Garante que não falhe ao fechar conexão

# def editar_zona_barragem(zona_id):
#     """Formulário de edição atualizado"""
#     zona = obter_zona_por_id(zona_id)
#     if not zona:
#         st.error("Zona não encontrada")
#         st.session_state.pop('editar_zona_id', None)
#         st.rerun()
    
#     with st.form("form_editar_zona"):
#         st.subheader(f"Editando Zona: {zona[4]}")  # índice 4 para nome
        
#         materiais = obter_todos_materiais()
#         material_opcoes = {m[0]: m[2] for m in materiais}
        
#         material_id = st.selectbox(
#             "Material Principal*",
#             options=list(material_opcoes.keys()),
#             index=list(material_opcoes.keys()).index(zona[3]),  # índice 3 para material_id
#             format_func=lambda x: material_opcoes.get(x, "Selecione...")
#         )
        
#         nome = st.text_input("Nome da Zona*", value=zona[4])  # índice 4 para nome
#         descricao = st.text_area("Descrição Técnica", value=zona[5] if zona[5] else "")  # índice 5 para descricao
        
#         col1, col2 = st.columns(2)
#         with col1:
#             if st.form_submit_button("💾 Salvar Alterações"):
#                 if atualizar_zona_db(zona_id, material_id, nome, descricao):
#                     st.success("Zona atualizada!")
#                     time.sleep(1)
#                     st.session_state.pop('editar_zona_id', None)
#                     st.rerun()
#         with col2:
#             if st.button("❌ Cancelar"):
#                 st.session_state.pop('editar_zona_id', None)
#                 st.rerun()

def listar_zonas_barragem(barragem_id):
    """Lista todas as zonas cadastradas para uma barragem específica"""
    if not barragem_id:
        st.error("Nenhuma barragem selecionada")
        return
    
    zonas = obter_zonas_por_barragem(barragem_id)
    
    if not zonas:
        st.info("Nenhuma zona cadastrada para esta barragem ainda.")
        return
    
    for zona in zonas:
        with st.expander(f"Zona: {zona[4]} (ID: {zona[0]})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                material = obter_material_por_id(zona[3])
                material_nome = material[1] if material and len(material) > 1 else 'Não especificado'
                st.write(f"**Material:** {material_nome}")
                
                if len(zona) > 5 and zona[5]:
                    st.write(f"**Descrição:** {zona[5]}")
                
                # modos_falha = obter_modos_falha_por_zona(zona[0])
                # if modos_falha:
                #     st.write("**Modos de Falha Associados:**")
                #     for modo in modos_falha:
                #         st.write(f"- {modo[1] if len(modo) > 1 else 'Modo desconhecido'}")

            with col2:
                if st.button("✏️ Editar", key=f"edit_zona_{zona[0]}"):
                    # Redireciona para a edição
                    st.session_state['pagina'] = "editar_zona"
                    st.session_state['zona_edit_id'] = zona[0]
                    st.rerun()
                
                if st.button("🗑️ Excluir", key=f"del_zona_{zona[0]}"):
                    if excluir_zona_barragem(zona[0]):
                        st.rerun()

def gerenciar_tipos_materiais():
    """Cadastro e listagem de tipos de materiais"""
    st.subheader("Tipos de Materiais")
    
    with st.expander("➕ Cadastrar Novo Material"):
        with st.form("form_novo_material"):
            nome = st.text_input("Nome do Material*", max_chars=50)
            descricao = st.text_area("Descrição Técnica")
            
            if st.form_submit_button("Salvar Material"):
                if nome:
                    sucesso = cadastrar_material_db(
                        usuario_id=st.session_state['usuario_id'],
                        nome=nome.strip(),
                        descricao=descricao.strip() if descricao else None
                    )
                    if sucesso:
                        st.success("Material cadastrado!")
                        st.rerun()
                else:
                    st.error("Nome do material é obrigatório")
    
    # Listagem de materiais existentes
    materiais = obter_todos_materiais()
    if materiais:
        st.write("**Materiais Cadastrados:**")
        for material in materiais:
            cols = st.columns([3, 1])
            cols[0].write(f"**{material[2]}** - {material[3] or 'Sem descrição'}")
            
            if cols[1].button("Excluir", key=f"del_mat_{material[0]}"):
                if excluir_material_db(material[0]):
                    st.rerun()

def exibir_formulario_cadastro_barragem():
    """Exibe o formulário padrão de cadastro de barragem"""
    # Voltar para página principal
    if st.button("⬅️ Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()

    st.subheader("Informações Básicas")
    nome = st.text_input("Nome da Barragem*", placeholder="Ex: Barragem do Rio Preto")

    # Lista de tipos de barragem: (id, nome)
    tipos = obter_tipos_barragem()

    # Criar dicionário nome -> id
    opcoes = {t[2]: t[0] for t in tipos}

    # Criar dicionário inverso id -> nome (para uso no valor inicial)
    id_para_nome = {t[0]: t[2] for t in tipos}

    # Obter nome correspondente ao ID atual (ou "" se não encontrado)
    tipo_nome_atual = id_para_nome.get(1, "")

    # Selectbox que mostra o nome e armazena o ID
    tipo_nome = st.selectbox(
        "Tipo de Barragem*",
        options=list(opcoes.keys()),
        index=list(opcoes.keys()).index(tipo_nome_atual) if tipo_nome_atual in opcoes else 0,
        help="Selecione o tipo construtivo da barragem"
    )

    # Recuperar o tipo_id correspondente ao nome selecionado
    tipo_id = opcoes[tipo_nome]

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
            if not nome or not tipo_id or not localizacao or altura == 0 or comprimento == 0:
                st.error("Preencha todos os campos obrigatórios (*) e certifique-se de que altura e comprimento sejam maiores que zero.")
            else:
                try:
                    cadastrar_barragem(
                        st.session_state['usuario_id'],
                        nome,
                        tipo_id,
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

def cadastrar_tipo_barragem_db(usuario_id, nome, descricao, referencia_tecnica=None, image_path=None):
    """
    Cadastra novo tipo de barragem com tratamento completo de erros e validações
    Retorna:
        - ID do novo registro se bem-sucedido
        - None em caso de falha
    """
    conn = None
    try:
        # Validações iniciais
        if not nome or not isinstance(nome, str) or len(nome.strip()) == 0:
            st.error("Nome do tipo de barragem é obrigatório")
            return None
            
        if len(nome.strip()) > 50:
            st.error("Nome deve ter no máximo 50 caracteres")
            return None
            
        if not descricao or len(descricao.strip()) == 0:
            st.error("Descrição técnica é obrigatória")
            return None

        # Conecta ao banco de dados
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Verifica se já existe um tipo com o mesmo nome
        cursor.execute("SELECT id FROM tipos_barragem WHERE nome = ?", (nome.strip(),))
        if cursor.fetchone():
            st.error("Já existe um tipo de barragem com este nome")
            return None
        
        # Insere o novo registro
        cursor.execute("""
            INSERT INTO tipos_barragem 
            (usuario_id, nome, descricao, referencia_tecnica, image_path)
            VALUES (?, ?, ?, ?, ?)
        """, (
            usuario_id,
            nome.strip(),
            descricao.strip(),
            referencia_tecnica.strip() if referencia_tecnica else None,
            image_path if image_path and os.path.exists(image_path) else None
        ))
        
        conn.commit()
        
        # Retorna o ID do novo registro
        novo_id = cursor.lastrowid
        st.success(f"Tipo de barragem cadastrado com sucesso! (ID: {novo_id})")
        return novo_id
        
    except sqlite3.IntegrityError as e:
        st.error(f"Erro de integridade no banco de dados: {str(e)}")
        return None
        
    except sqlite3.Error as e:
        st.error(f"Erro no banco de dados: {str(e)}")
        return None
        
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return None
        
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass  # Garante que não falhe ao fechar conexão

def adicionar_tipo_barragem():
    """
    Página para cadastro de novos tipos de barragem
    - Acesso restrito a administradores
    - Integrado com a estrutura revisada da tabela tipos_barragem
    """
    
    st.title("📝 Cadastrar Novo Tipo de Barragem")
    
    # Verificação de permissão
    if not st.session_state.get('is_admin'):
        st.error("⛔ Acesso permitido apenas para administradores")
        if st.button("← Voltar"):
            st.session_state['pagina'] = "principal"
            st.rerun()
        return
    
    with st.form("novo_tipo_barragem", clear_on_submit=True):
        # Campos obrigatórios
        nome = st.text_input("Nome do Tipo*", 
                           help="Nome técnico do tipo de barragem (ex: 'Terra Homogênea')")
        
        descricao = st.text_area("Descrição Técnica*", height=120,
                               help="Características construtivas e técnicas relevantes")
        
        # Campos opcionais
        referencia = st.text_input("Referência Normativa",
                                 help="Norma técnica ou documento de referência (ex: 'ABNT NBR 15421')")
        
        imagem = st.file_uploader("Imagem Representativa (opcional)",
                                type=["jpg", "jpeg", "png"],
                                help="Upload de imagem ilustrativa (máx. 5MB)")
        
        submitted = st.form_submit_button("Salvar Novo Tipo")
        
        if submitted:
            # Validação dos campos obrigatórios
            if not nome.strip() or not descricao.strip():
                st.error("Preencha todos os campos obrigatórios (*)")
            elif len(nome.strip()) > 50:  # Validação manual do comprimento máximo
                st.error("O nome deve ter no máximo 50 caracteres")
            else:
                try:
                    # Processamento da imagem
                    caminho_imagem = None
                    if imagem is not None:
                        # Verifica tamanho do arquivo (máx 5MB)
                        if imagem.size > 5 * 1024 * 1024:
                            st.error("Arquivo muito grande (tamanho máximo: 5MB)")
                            return
                        
                        # Cria diretório se não existir
                        os.makedirs("uploads/tipos_barragem", exist_ok=True)
                        
                        # Gera nome único para o arquivo
                        extensao = os.path.splitext(imagem.name)[1].lower()
                        nome_arquivo = f"tipo_{nome.lower().replace(' ', '_')}_{int(time.time())}{extensao}"
                        caminho_imagem = f"uploads/tipos_barragem/{nome_arquivo}"
                        
                        # Salva o arquivo
                        with open(caminho_imagem, "wb") as f:
                            f.write(imagem.getbuffer())
                    
                    # Cadastra no banco de dados
                    sucesso = cadastrar_tipo_barragem_db(
                        usuario_id=st.session_state['usuario_id'],
                        nome=nome.strip(),
                        descricao=descricao.strip(),
                        referencia_tecnica=referencia.strip() if referencia else None,
                        image_path=caminho_imagem
                    )
                    
                    if sucesso:
                        st.success("✅ Tipo de barragem cadastrado com sucesso!")
                        time.sleep(1.5)
                        st.session_state['pagina'] = "lista_tipos_barragem"
                        st.rerun()
                    else:
                        st.error("Erro: Tipo de barragem já existe ou dados inválidos")
                        
                except Exception as e:
                    st.error(f"Falha no cadastro: {str(e)}")
                    # Limpeza em caso de falha
                    if caminho_imagem and os.path.exists(caminho_imagem):
                        os.remove(caminho_imagem)
    
    # Rodapé com ações
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Voltar"):
            st.session_state['pagina'] = "lista_tipos_barragem"
            st.rerun()
    with col2:
        st.caption("Campos marcados com (*) são obrigatórios")

def listar_tipos_barragem():
    """Página para listagem segura dos tipos de barragem com tratamento completo de imagens"""
    st.title("📋 Tipos de Barragem Cadastrados")
    
    # Carrega os tipos do banco de dados
    tipos = obter_tipos_barragem()
    
    if not tipos:
        st.warning("Nenhum tipo de barragem cadastrado ainda.")
    else:
        for i, tipo in enumerate(tipos):
            with st.expander(f"{tipo[2]} (ID: {tipo[0]})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Descrição:** {tipo[3]}")
                    if tipo[3]:
                        st.write(f"**Referência:** {tipo[4]}")
                    
                    # Tratamento avançado para exibição de imagens
                    if tipo[4]:  # Se há image_path definido
                        exibir_imagem_segura(tipo[5], tipo[2])
                    else:
                        st.info("ℹ️ Nenhuma imagem cadastrada para este tipo")
                
                with col2:
                    if st.session_state.get('is_admin'):
                        if st.button("🗑️ Excluir", key=f"del_tipo_{tipo[0]}_{i}"):
                            if excluir_tipo_barragem(tipo[0]):
                                st.rerun()
    
    # Rodapé com ações
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("⬅️ Voltar", key="voltar_lista_tipos"):
            st.session_state['pagina'] = "principal"
            st.rerun()
    with col2:
        if st.session_state.get('is_admin'):
            if st.button("➕ Adicionar Novo Tipo", key="add_novo_tipo"):
                st.session_state['pagina'] = "adicionar_tipo_barragem"
                st.rerun()

def exibir_imagem_segura(caminho_imagem, nome_tipo):
    """
    Exibe uma imagem com tratamento completo de erros
    :param caminho_imagem: Caminho da imagem a ser exibida
    :param nome_tipo: Nome do tipo para mensagens de erro
    """
    print(caminho_imagem)
    try:
        # Verifica se o caminho é uma URL
        if isinstance(caminho_imagem, str) and caminho_imagem.startswith(('http://', 'https://')):
            st.image(caminho_imagem, width=200, caption=f"Imagem: {nome_tipo}")
            return
        
        # Verifica se o arquivo existe localmente
        if not os.path.exists(caminho_imagem):
            st.warning(f"⚠️ Imagem não encontrada no caminho: {caminho_imagem}")
            return
        
        # Verifica se é um arquivo de imagem válido
        extensoes_validas = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        if not caminho_imagem.lower().endswith(extensoes_validas):
            st.warning(f"⚠️ Formato de imagem não suportado: {caminho_imagem}")
            return
        
        # Tenta exibir a imagem
        st.image(caminho_imagem, width=200, caption=f"Imagem: {nome_tipo}")
        
    except Exception as e:
        st.error(f"⛔ Erro ao carregar imagem: {str(e)}")
        st.info("ℹ️ Entre em contato com o administrador para corrigir este registro")

def excluir_tipo_barragem(tipo_id):
    """
    Exclui um tipo de barragem do sistema
    :param tipo_id: ID do tipo a ser excluído
    :return: True se bem-sucedido, False caso contrário
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Primeiro verifica se existem barragens usando este tipo
        cursor.execute("SELECT COUNT(*) FROM barragens WHERE tipo_id = ?", (tipo_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            st.error("Não é possível excluir: existem barragens cadastradas com este tipo")
            return False
        
        # Exclui o registro
        cursor.execute("DELETE FROM tipos_barragem WHERE id = ?", (tipo_id,))
        conn.commit()
        
        # Verifica se realmente foi excluído
        if cursor.rowcount == 1:
            st.success("Tipo de barragem excluído com sucesso!")
            return True
        else:
            st.error("Tipo de barragem não encontrado")
            return False
            
    except sqlite3.Error as e:
        st.error(f"Erro ao excluir tipo de barragem: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def editar_barragem(barragem):
    """Formulário para edição de barragem existente"""
    with st.form("editar_barragem_form"):
        nome = st.text_input("Nome", value=barragem[2])


        # Lista de tipos de barragem: (id, nome)
        tipos = obter_tipos_barragem()

        # Criar dicionário nome -> id
        opcoes = {t[2]: t[0] for t in tipos}

        # Criar dicionário inverso id -> nome (para uso no valor inicial)
        id_para_nome = {t[0]: t[2] for t in tipos}

        # tipo_id previamente armazenado
    
        tipo_id_atual = barragem[3]

        # Obter nome correspondente ao ID atual (ou "" se não encontrado)
        tipo_nome_atual = id_para_nome.get(tipo_id_atual, "")

        # Selectbox que mostra o nome e armazena o ID
        tipo_nome = st.selectbox(
            "Tipo de Barragem*",
            options=list(opcoes.keys()),
            index=list(opcoes.keys()).index(tipo_nome_atual) if tipo_nome_atual in opcoes else 0,
            help="Selecione o tipo construtivo da barragem"
        )

        # Recuperar o tipo_id correspondente ao nome selecionado
        tipo_id = opcoes[tipo_nome]

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
                    barragem[0], nome, tipo_id, localizacao, altura, comprimento, rel_cordaaltura
                )
                st.success("Barragem atualizada com sucesso!")
                st.rerun()
       
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

    """Página para cadastro e gestão de zonas da barragem"""
    st.title("🏗️ Gerenciamento de Zonas da Barragem")

    from db import (
        obter_barragem_analise, obter_tipos_materiais_usuario,
        cadastrar_zona, obter_zonas_barragem, excluir_zona
    )

    # Obter barragem em análise
    barragem = obter_barragem_analise(st.session_state['usuario_id'])
    if not barragem:
        st.error("Selecione uma barragem para análise primeiro.")
        if st.button("⬅️ Voltar"):
            st.session_state['pagina'] = "principal"
            st.rerun()
        return

    barragem_id = barragem[0]
    st.info(f"Barragem em análise: {barragem[1]}")

    # Carregar materiais do usuário
    materiais = obter_tipos_materiais_usuario(st.session_state['usuario_id'])
    if not materiais:
        st.warning("Cadastre pelo menos um tipo de material antes de continuar.")
        if st.button("🧱 Ir para Cadastro de Materiais"):
            st.session_state['pagina'] = "gerenciar_materiais"
            st.rerun()
        return

    opcoes_materiais = {m[0]: m[1] for m in materiais}

    # Formulário de cadastro de zona
    st.subheader("➕ Cadastrar Nova Zona")
    with st.form("form_cadastro_zona"):
        nome = st.text_input("Nome da Zona*")
        material_id = st.selectbox(
            "Tipo de Material",
            options=list(opcoes_materiais.keys()),
            format_func=lambda x: opcoes_materiais[x]
        )
        submitted = st.form_submit_button("Cadastrar Zona")

        if submitted:
            if not nome.strip():
                st.error("Digite um nome para a zona.")
            else:
                cadastrar_zona(
                    st.session_state['usuario_id'],
                    barragem_id,
                    nome,
                    material_id
                )
                st.success("Zona cadastrada com sucesso!")
                st.rerun()

    # Lista de zonas já cadastradas
    st.subheader("📋 Zonas Cadastradas")
    zonas = obter_zonas_barragem(barragem_id)
    if zonas:
        for zona in zonas:
            col1, col2 = st.columns([4, 1])
            with col1:
                material_nome = opcoes_materiais.get(zona[3], "Desconhecido")
                st.markdown(f"**{zona[2]}** - Material: {material_nome}")
            with col2:
                if st.button("🗑️ Excluir", key=f"excluir_zona_{zona[0]}"):
                    excluir_zona(zona[0])
                    st.success("Zona excluída!")
                    st.rerun()
    else:
        st.info("Nenhuma zona cadastrada ainda.")

    # Botões extras
    if st.button("🧱 Gerenciar Materiais"):
        st.session_state['pagina'] = "gerenciar_materiais"
        st.rerun()

    if st.button("⬅️ Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()

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