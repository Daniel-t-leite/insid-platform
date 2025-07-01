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


def gerenciar_anomalias():
    """Página de gerenciamento de anomalias e seus relacionamentos"""
    st.title("⚠️ Gerenciamento de Anomalias")

    # Verifica permissão
    if not st.session_state.get('is_admin'):
        st.error("⛔ Acesso permitido apenas para administradores")
        if st.button("← Voltar"):
            st.session_state['pagina'] = "principal"
            st.rerun()
        return

    # Conexão com o banco
    conn = conectar_db()

    # Modo de operação
    modo = st.radio("Modo:", ["Visualizar", "Adicionar", "Editar", "Excluir", "Relacionamentos"], horizontal=True)

    # Carrega dados básicos
    df_anomalias = pd.read_sql("SELECT id, nome, gravidade, peso FROM anomalias ORDER BY nome", conn)
    
    if modo == "Visualizar":
        st.subheader("Anomalias cadastradas")
        if not df_anomalias.empty:
            st.dataframe(df_anomalias.set_index('id'), use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma anomalia cadastrada ainda.")

    elif modo == "Adicionar":
        st.subheader("Adicionar Nova Anomalia")
        with st.form("form_add_anomalia", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome da Anomalia*", max_chars=100)
                gravidade = st.slider("Gravidade (0-10)*", 0.0, 10.0, 5.0, 0.1)
            with col2:
                peso = st.slider("Peso (0-10)*", 0.0, 10.0, 5.0, 0.1)
                imagem = st.file_uploader("Imagem (opcional)", type=["jpg", "jpeg", "png"])
            
            descricao = st.text_area("Descrição Técnica*", height=100)
            referencia = st.text_input("Referência Técnica (opcional)")

            if st.form_submit_button("💾 Salvar Anomalia"):
                if not nome.strip() or not descricao.strip():
                    st.error("Nome e descrição são campos obrigatórios")
                else:
                    # Processa a imagem se houver
                    caminho_imagem = None
                    if imagem is not None:
                        if imagem.size > 5 * 1024 * 1024:
                            st.error("Arquivo muito grande (máx. 5MB)")
                            return
                        os.makedirs("uploads/anomalias", exist_ok=True)
                        extensao = os.path.splitext(imagem.name)[1].lower()
                        nome_arquivo = f"anomalia_{nome.lower().replace(' ', '_')}_{int(time.time())}{extensao}"
                        caminho_imagem = f"uploads/anomalias/{nome_arquivo}"
                        with open(caminho_imagem, "wb") as f:
                            f.write(imagem.getbuffer())

                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO anomalias 
                            (usuario_id, nome, descricao, gravidade, peso, referencia_tecnica, image_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            st.session_state['usuario_id'],
                            nome.strip(),
                            descricao.strip(),
                            gravidade,
                            peso,
                            referencia.strip() if referencia else None,
                            caminho_imagem
                        ))
                        conn.commit()
                        st.success("Anomalia cadastrada com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Já existe uma anomalia com este nome.")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {str(e)}")

    elif modo == "Editar":
        st.subheader("Editar Anomalia Existente")

        if df_anomalias.empty:
            st.warning("Nenhuma anomalia cadastrada para editar.")
        else:
            anomalia_id = st.selectbox(
                "Selecione a anomalia para editar:",
                options=df_anomalias['id'],
                format_func=lambda x: f"{df_anomalias[df_anomalias['id']==x]['nome'].values[0]} (Grav: {df_anomalias[df_anomalias['id']==x]['gravidade'].values[0]})"
            )

            anomalia = pd.read_sql(f"""
                SELECT * FROM anomalias WHERE id = {anomalia_id}
            """, conn).iloc[0]

            with st.form("form_edit_anomalia"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_nome = st.text_input("Nome da Anomalia*", value=anomalia['nome'], max_chars=100)
                    nova_gravidade = st.slider("Gravidade (0-10)*", 0.0, 10.0, float(anomalia['gravidade']), 0.1)
                with col2:
                    novo_peso = st.slider("Peso (0-10)*", 0.0, 10.0, float(anomalia['peso']), 0.1)
                    nova_imagem = st.file_uploader("Substituir Imagem", type=["jpg", "jpeg", "png"])
                
                nova_descricao = st.text_area("Descrição Técnica*", value=anomalia['descricao'], height=100)
                nova_referencia = st.text_input("Referência Técnica", value=anomalia['referencia_tecnica'] or "")

                if st.form_submit_button("💾 Salvar Alterações"):
                    if not novo_nome.strip() or not nova_descricao.strip():
                        st.error("Nome e descrição são campos obrigatórios")
                    else:
                        caminho_imagem = anomalia['image_path']
                        if nova_imagem is not None:
                            if nova_imagem.size > 5 * 1024 * 1024:
                                st.error("Arquivo muito grande (máx. 5MB)")
                                return
                            os.makedirs("uploads/anomalias", exist_ok=True)
                            extensao = os.path.splitext(nova_imagem.name)[1].lower()
                            nome_arquivo = f"anomalia_{novo_nome.lower().replace(' ', '_')}_{int(time.time())}{extensao}"
                            caminho_imagem = f"uploads/anomalias/{nome_arquivo}"
                            with open(caminho_imagem, "wb") as f:
                                f.write(nova_imagem.getbuffer())

                        try:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE anomalias 
                                SET nome = ?, descricao = ?, gravidade = ?, peso = ?, 
                                    referencia_tecnica = ?, image_path = ?
                                WHERE id = ?
                            """, (
                                novo_nome.strip(),
                                nova_descricao.strip(),
                                nova_gravidade,
                                novo_peso,
                                nova_referencia.strip() if nova_referencia else None,
                                caminho_imagem,
                                anomalia_id
                            ))
                            conn.commit()
                            st.success("Anomalia atualizada com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Já existe outra anomalia com este nome.")
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {str(e)}")

    elif modo == "Excluir":
        st.subheader("Excluir Anomalia")

        if df_anomalias.empty:
            st.warning("Nenhuma anomalia cadastrada para excluir.")
        else:
            anomalia_id = st.selectbox(
                "Selecione a anomalia para excluir:",
                options=df_anomalias['id'],
                format_func=lambda x: f"{df_anomalias[df_anomalias['id']==x]['nome'].values[0]}"
            )

            anomalia = pd.read_sql(f"""
                SELECT * FROM anomalias WHERE id = {anomalia_id}
            """, conn).iloc[0]

            st.warning("⚠️ Você está prestes a excluir permanentemente esta anomalia:")
            st.write(f"**Nome:** {anomalia['nome']}")
            st.write(f"**Gravidade:** {anomalia['gravidade']}")
            st.write(f"**Peso:** {anomalia['peso']}")
            st.write(f"**Descrição:** {anomalia['descricao'][:100]}..." if anomalia['descricao'] else "Sem descrição")

            if anomalia['image_path'] and os.path.exists(anomalia['image_path']):
                st.image(anomalia['image_path'], caption="Imagem da Anomalia", use_column_width=True)

            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                try:
                    # Primeiro remove os relacionamentos
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM anomalia_modo_falha WHERE anomalia_id = ?", (anomalia_id,))
                    cursor.execute("DELETE FROM anomalia_zona WHERE anomalia_id = ?", (anomalia_id,))
                    cursor.execute("DELETE FROM anomalia_tipo_material WHERE anomalia_id = ?", (anomalia_id,))
                    cursor.execute("DELETE FROM anomalia_tipo_barragem WHERE anomalia_id = ?", (anomalia_id,))
                    
                    # Depois remove a anomalia
                    cursor.execute("DELETE FROM anomalias WHERE id = ?", (anomalia_id,))
                    conn.commit()
                    
                    # Remove a imagem se existir
                    if anomalia['image_path'] and os.path.exists(anomalia['image_path']):
                        try:
                            os.remove(anomalia['image_path'])
                        except:
                            pass
                    
                    st.success("Anomalia e seus relacionamentos excluídos com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {str(e)}")

    elif modo == "Relacionamentos":
        st.subheader("Gerenciar Relacionamentos de Anomalias")
        
        if df_anomalias.empty:
            st.warning("Nenhuma anomalia cadastrada para gerenciar relacionamentos.")
        else:
            anomalia_id = st.selectbox(
                "Selecione a anomalia:",
                options=df_anomalias['id'],
                format_func=lambda x: f"{df_anomalias[df_anomalias['id']==x]['nome'].values[0]}"
            )
            
            tab1, tab2, tab3, tab4 = st.tabs(["Modos de Falha", "Zonas", "Tipos de Material", "Tipos de Barragem"])
            
            with tab1:  # Modos de Falha
                modos_falha = pd.read_sql("""
                    SELECT mf.id, mf.nome, tmf.nome as tipo 
                    FROM modos_falha mf
                    JOIN tipo_modo_falha tmf ON mf.id_tipo_modo_falha = tmf.id
                    ORDER BY mf.nome
                """, conn)
                
                relacionados = pd.read_sql(f"""
                    SELECT modo_falha_id 
                    FROM anomalia_modo_falha 
                    WHERE anomalia_id = {anomalia_id}
                """, conn)['modo_falha_id'].tolist()
                
                options = st.multiselect(
                    "Modos de Falha relacionados:",
                    options=modos_falha['id'],
                    default=relacionados,
                    format_func=lambda x: f"{modos_falha[modos_falha['id']==x]['nome'].values[0]} ({modos_falha[modos_falha['id']==x]['tipo'].values[0]})"
                )
                
                if st.button("💾 Salvar Modos de Falha", key="save_modos_falha"):
                    try:
                        cursor = conn.cursor()
                        # Remove todos os relacionamentos existentes
                        cursor.execute("DELETE FROM anomalia_modo_falha WHERE anomalia_id = ?", (anomalia_id,))
                        # Adiciona os novos selecionados
                        for modo_id in options:
                            cursor.execute("""
                                INSERT INTO anomalia_modo_falha (anomalia_id, modo_falha_id)
                                VALUES (?, ?)
                            """, (anomalia_id, modo_id))
                        conn.commit()
                        st.success("Relacionamentos com modos de falha atualizados!")
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {str(e)}")
            
            with tab2:  # Zonas
                zonas = pd.read_sql("SELECT id, nome FROM tipos_zonas_bar ORDER BY nome", conn)
                relacionados = pd.read_sql(f"""
                    SELECT zona_id 
                    FROM anomalia_zona 
                    WHERE anomalia_id = {anomalia_id}
                """, conn)['zona_id'].tolist()
                
                options = st.multiselect(
                    "Zonas relacionadas:",
                    options=zonas['id'],
                    default=relacionados,
                    format_func=lambda x: zonas[zonas['id']==x]['nome'].values[0]
                )
                
                if st.button("💾 Salvar Zonas", key="save_zonas"):
                    try:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM anomalia_zona WHERE anomalia_id = ?", (anomalia_id,))
                        for zona_id in options:
                            cursor.execute("""
                                INSERT INTO anomalia_zona (anomalia_id, zona_id)
                                VALUES (?, ?)
                            """, (anomalia_id, zona_id))
                        conn.commit()
                        st.success("Relacionamentos com zonas atualizados!")
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {str(e)}")
            
            with tab3:  # Tipos de Material
                materiais = pd.read_sql("SELECT id, nome FROM tipos_materiais ORDER BY nome", conn)
                relacionados = pd.read_sql(f"""
                    SELECT tipo_mat_id 
                    FROM anomalia_tipo_material 
                    WHERE anomalia_id = {anomalia_id}
                """, conn)['tipo_mat_id'].tolist()
                
                options = st.multiselect(
                    "Tipos de Material relacionados:",
                    options=materiais['id'],
                    default=relacionados,
                    format_func=lambda x: materiais[materiais['id']==x]['nome'].values[0]
                )
                
                if st.button("💾 Salvar Tipos de Material", key="save_materiais"):
                    try:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM anomalia_tipo_material WHERE anomalia_id = ?", (anomalia_id,))
                        for mat_id in options:
                            cursor.execute("""
                                INSERT INTO anomalia_tipo_material (anomalia_id, tipo_mat_id)
                                VALUES (?, ?)
                            """, (anomalia_id, mat_id))
                        conn.commit()
                        st.success("Relacionamentos com tipos de material atualizados!")
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {str(e)}")
            
            with tab4:  # Tipos de Barragem
                tipos_bar = pd.read_sql("SELECT id, nome FROM tipos_barragem ORDER BY nome", conn)
                relacionados = pd.read_sql(f"""
                    SELECT tipo_barragem_id 
                    FROM anomalia_tipo_barragem 
                    WHERE anomalia_id = {anomalia_id}
                """, conn)['tipo_barragem_id'].tolist()
                
                options = st.multiselect(
                    "Tipos de Barragem relacionados:",
                    options=tipos_bar['id'],
                    default=relacionados,
                    format_func=lambda x: tipos_bar[tipos_bar['id']==x]['nome'].values[0]
                )
                
                if st.button("💾 Salvar Tipos de Barragem", key="save_tipos_bar"):
                    try:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM anomalia_tipo_barragem WHERE anomalia_id = ?", (anomalia_id,))
                        for tipo_id in options:
                            cursor.execute("""
                                INSERT INTO anomalia_tipo_barragem (anomalia_id, tipo_barragem_id)
                                VALUES (?, ?)
                            """, (anomalia_id, tipo_id))
                        conn.commit()
                        st.success("Relacionamentos com tipos de barragem atualizados!")
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {str(e)}")

    conn.close()
    
    if st.button("← Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()



def gerenciar_modos_falha():
    """Página de gerenciamento dos modos de falha"""
    st.title("⚙️ Gerenciamento de modos de falha")

    # Verifica permissão
    if not st.session_state.get('is_admin'):
        st.error("⛔ Acesso permitido apenas para administradores")
        if st.button("← Voltar"):
            st.session_state['pagina'] = "principal"
            st.rerun()
        return

    # Conexão com o banco
    conn = conectar_db()

    # Modo de operação
    modo = st.radio("Modo:", ["Visualizar", "Adicionar", "Editar", "Excluir"], horizontal=True)

    # Carrega os dados existentes com join para o tipo de modo falha
    df = pd.read_sql("""
        SELECT mf.id, mf.nome, mf.descricao, mf.referencia_tecnica, 
               mf.image_path, tmf.nome as tipo_modo_falha, mf.id_tipo_modo_falha
        FROM modos_falha mf
        LEFT JOIN tipo_modo_falha tmf ON mf.id_tipo_modo_falha = tmf.id
        ORDER BY mf.nome
    """, conn)

    # Carrega tipos de modo falha para os selectboxes
    tipos_falha = pd.read_sql("SELECT id, nome FROM tipo_modo_falha ORDER BY nome", conn)
    
    if tipos_falha.empty:
        st.error("Nenhum tipo de modo de falha cadastrado. Cadastre tipos primeiro.")
        if st.button("← Voltar"):
            st.session_state['pagina'] = "principal"
            st.rerun()
        conn.close()
        return

    if modo == "Visualizar":
        st.subheader("Modos de falha cadastrados")
        if not df.empty:
            # Renomeia colunas para melhor exibição
            df_display = df.rename(columns={
                'tipo_modo_falha': 'Tipo de modo falha'
            }).set_index('id')
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("ℹ️ Nenhum modo de falha cadastrado ainda.")

    elif modo == "Adicionar":
        st.subheader("Adicionar modo de falha")
        
        with st.form("form_add_modo_falha", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do modo de falha*", max_chars=50)
                id_tipo = st.selectbox(
                    "Tipo de modo de falha*",
                    options=tipos_falha['id'],
                    format_func=lambda x: tipos_falha[tipos_falha['id']==x]['nome'].values[0]
                )
            with col2:
                referencia = st.text_input("Referência técnica (opcional)")
                imagem = st.file_uploader("Imagem representativa (opcional)", type=["jpg", "jpeg", "png"])
            
            descricao = st.text_area("Descrição técnica", height=100)

            if st.form_submit_button("💾 Salvar Novo Modo"):
                if not nome.strip():
                    st.error("O nome do modo de falha é obrigatório")
                else:
                    # Processa a imagem se houver
                    caminho_imagem = None
                    if imagem is not None:
                        if imagem.size > 5 * 1024 * 1024:
                            st.error("Arquivo muito grande (máx. 5MB)")
                            return
                        os.makedirs("uploads/modos_falha", exist_ok=True)
                        extensao = os.path.splitext(imagem.name)[1].lower()
                        nome_arquivo = f"modo_falha_{nome.lower().replace(' ', '_')}_{int(time.time())}{extensao}"
                        caminho_imagem = f"uploads/modos_falha/{nome_arquivo}"
                        with open(caminho_imagem, "wb") as f:
                            f.write(imagem.getbuffer())

                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO modos_falha 
                            (usuario_id, id_tipo_modo_falha, nome, descricao, referencia_tecnica, image_path)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            st.session_state['usuario_id'],
                            id_tipo,
                            nome.strip(),
                            descricao.strip() if descricao else None,
                            referencia.strip() if referencia else None,
                            caminho_imagem
                        ))
                        conn.commit()
                        st.success("Modo de falha adicionado com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Já existe um modo de falha com este nome.")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {str(e)}")

    elif modo == "Editar":
        st.subheader("Editar modo de falha Existente")

        if df.empty:
            st.warning("Nenhum modo de falha cadastrado para editar.")
        else:
            modo_id = st.selectbox(
                "Selecione o modo de falha para editar:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} "
            )

            modo_falha = df[df['id'] == modo_id].iloc[0]

            with st.form("form_edit_modo_falha"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_nome = st.text_input("Nome do modo de falha*", value=modo_falha['nome'], max_chars=50)
                    novo_id_tipo = st.selectbox(
                        "Tipo de modo de falha*",
                        options=tipos_falha['id'],
                        index=list(tipos_falha['id']).index(modo_falha['id_tipo_modo_falha']),
                        format_func=lambda x: tipos_falha[tipos_falha['id']==x]['nome'].values[0]
                    )
                with col2:
                    nova_referencia = st.text_input("Referência técnica", 
                                                  value=modo_falha['referencia_tecnica'] or "")
                    nova_imagem = st.file_uploader("Substituir Imagem", 
                                                  type=["jpg", "jpeg", "png"])
                
                nova_descricao = st.text_area("Descrição Técnica", 
                                            value=modo_falha['descricao'] or "", 
                                            height=100)

                if st.form_submit_button("💾 Salvar Alterações"):
                    if not novo_nome.strip():
                        st.error("O nome do modo de falha é obrigatório")
                    else:
                        caminho_imagem = modo_falha['image_path']
                        if nova_imagem is not None:
                            if nova_imagem.size > 5 * 1024 * 1024:
                                st.error("Arquivo muito grande (máx. 5MB)")
                                return
                            os.makedirs("uploads/modos_falha", exist_ok=True)
                            extensao = os.path.splitext(nova_imagem.name)[1].lower()
                            nome_arquivo = f"modo_falha_{novo_nome.lower().replace(' ', '_')}_{int(time.time())}{extensao}"
                            caminho_imagem = f"uploads/modos_falha/{nome_arquivo}"
                            with open(caminho_imagem, "wb") as f:
                                f.write(nova_imagem.getbuffer())

                        try:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE modos_falha 
                                SET id_tipo_modo_falha = ?, nome = ?, descricao = ?, 
                                    referencia_tecnica = ?, image_path = ?
                                WHERE id = ?
                            """, (
                                novo_id_tipo,
                                novo_nome.strip(),
                                nova_descricao.strip() if nova_descricao else None,
                                nova_referencia.strip() if nova_referencia else None,
                                caminho_imagem,
                                modo_id
                            ))
                            conn.commit()
                            st.success("Modo de falha atualizado com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Já existe outro modo de falha com este nome.")
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {str(e)}")

    elif modo == "Excluir":
        st.subheader("Excluir modo de falha")

        if df.empty:
            st.warning("Nenhum modo de falha cadastrado para excluir.")
        else:
            modo_id = st.selectbox(
                "Selecione o modo de falha para excluir:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} "
            )

            modo_falha = df[df['id'] == modo_id].iloc[0]

            st.warning("⚠️ Você está prestes a excluir permanentemente o modo de falha:")
            st.write(f"**Nome:** {modo_falha['nome']}")
            st.write(f"**Tipo:** {modo_falha['tipo_modo_falha']}")
            st.write(f"**Descrição:** {modo_falha['descricao'] or 'Sem descrição'}")
            st.write(f"**Referência:** {modo_falha['referencia_tecnica'] or 'Sem referência'}")

            if modo_falha['image_path'] and os.path.exists(modo_falha['image_path']):
                st.image(modo_falha['image_path'], caption="Imagem Representativa", use_column_width=True)

            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM modos_falha WHERE id = ?", (modo_id,))
                    conn.commit()
                    
                    # Remove a imagem associada se existir
                    if modo_falha['image_path'] and os.path.exists(modo_falha['image_path']):
                        try:
                            os.remove(modo_falha['image_path'])
                        except:
                            pass  # Não impede a exclusão se falhar ao remover a imagem
                    
                    st.success("Modo de falha excluído com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Erro ao excluir: {str(e)}")

    conn.close()
    
    # Rodapé
    if st.button("← Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()
    
def gerenciar_tipos_modo_falha():
    """Página de gerenciamento dos modos de falha"""
    st.title("⚙️ Tipos de modos de falha")

    # Verifica permissão
    if not st.session_state.get('is_admin'):
        st.error("⛔ Acesso permitido apenas para administradores")
        if st.button("← Voltar"):
            st.session_state['pagina'] = "principal"
            st.rerun()
        return

    # Conexão com o banco
    conn = conectar_db()

    # Modo de operação
    modo = st.radio("Modo:", ["Visualizar", "Adicionar", "Editar", "Excluir"], horizontal=True)

    # Carrega os tipos existentes
    df = pd.read_sql("SELECT id, nome, descricao, referencia_tecnica FROM tipo_modo_falha ORDER BY nome", conn)

    if modo == "Visualizar":
        st.subheader("Categorias de modos de falha cadastrados")
        st.dataframe(df.set_index('id'), use_container_width=True)

    elif modo == "Adicionar":
        st.subheader("Adicionar nova categoria de modo de falha")
        with st.form("form_add_modo_falha", clear_on_submit=True):
            nome = st.text_input("Nome do Modo de Falha*", max_chars=50)
            descricao = st.text_area("Descrição Técnica*", height=100)
            referencia = st.text_input("Referência Técnica (opcional)")

            if st.form_submit_button("💾 Salvar Novo Modo de Falha"):
                if not nome.strip() or not descricao.strip():
                    st.error("Nome e descrição são campos obrigatórios")
                else:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO tipo_modo_falha 
                            (usuario_id, nome, descricao, referencia_tecnica)
                            VALUES (?, ?, ?, ?)
                        """, (
                            st.session_state['usuario_id'],
                            nome.strip(),
                            descricao.strip(),
                            referencia.strip() if referencia else None
                        ))
                        conn.commit()
                        st.success("Modo de falha adicionado com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Já existe um modo de falha com este nome.")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {str(e)}")

    elif modo == "Editar":
        st.subheader("Editar Modo de Falha Existente")

        if df.empty:
            st.warning("Nenhum modo de falha cadastrado para editar.")
        else:
            modo_id = st.selectbox(
                "Selecione o modo de falha para editar:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} "
            )

            modo_falha = df[df['id'] == modo_id].iloc[0]

            with st.form("form_edit_modo_falha"):
                novo_nome = st.text_input("Nome do Modo de Falha*", value=modo_falha['nome'], max_chars=50)
                nova_descricao = st.text_area("Descrição Técnica*", value=modo_falha['descricao'], height=100)
                nova_referencia = st.text_input("Referência Técnica (opcional)", value=modo_falha['referencia_tecnica'] or "")

                if st.form_submit_button("💾 Salvar Alterações"):
                    if not novo_nome.strip() or not nova_descricao.strip():
                        st.error("Nome e descrição são campos obrigatórios")
                    else:
                        try:
                            # Verifica se já existe outro com o mesmo nome (exceto o atual)
                            existente = pd.read_sql(
                                "SELECT 1 FROM tipo_modo_falha WHERE LOWER(nome) = LOWER(?) AND id != ?", 
                                conn, 
                                params=(novo_nome.strip(), modo_id)
                            ).empty
                            
                            if not existente:
                                st.error("Já existe outro modo de falha com este nome")
                            else:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE tipo_modo_falha 
                                    SET nome = ?, descricao = ?, referencia_tecnica = ?
                                    WHERE id = ?
                                """, (
                                    novo_nome.strip(), 
                                    nova_descricao.strip(), 
                                    nova_referencia.strip() or None, 
                                    modo_id
                                ))
                                conn.commit()
                                st.success("Modo de falha atualizado com sucesso!")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {str(e)}")

    elif modo == "Excluir":
        st.subheader("Excluir Modo de Falha")

        if df.empty:
            st.warning("Nenhum modo de falha cadastrado para excluir.")
        else:
            modo_id = st.selectbox(
                "Selecione o modo de falha para excluir:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} "
            )

            modo_falha = df[df['id'] == modo_id].iloc[0]

            st.warning("⚠️ Você está prestes a excluir permanentemente o modo de falha:")
            st.write(f"**Nome:** {modo_falha['nome']}")
            st.write(f"**Descrição:** {modo_falha['descricao']}")
            st.write(f"**Referência:** {modo_falha['referencia_tecnica'] or 'Sem referência'}")

            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM tipo_modo_falha WHERE id = ?", (modo_id,))
                    conn.commit()
                    st.success("Modo de falha excluído com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Erro ao excluir: {str(e)}")

    conn.close()
    
    # Rodapé
    if st.button("← Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()

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
        with st.expander(f"Zona: {zona[4]} "):
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
        with st.expander(f"Zona: {zona[4]}"):
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
    """Página de gerenciamento dos tipos de materiais"""
    st.title("⚙️ Gerenciamento de Tipos de Materiais")

    # Verifica permissão
    if not st.session_state.get('is_admin'):
        st.error("⛔ Acesso permitido apenas para administradores")
        if st.button("← Voltar"):
            st.session_state['pagina'] = "principal"
            st.rerun()
        return

    # Conexão com o banco
    conn = conectar_db()

    # Modo de operação
    modo = st.radio("Modo:", ["Visualizar", "Adicionar", "Editar", "Excluir"], horizontal=True)

    # Carrega os materiais existentes
    df = pd.read_sql("SELECT id, nome, descricao FROM tipos_materiais ORDER BY nome", conn)

    if modo == "Visualizar":
        st.subheader("Tipos de materiais cadastrados")
        if not df.empty:
            st.dataframe(df.set_index('id'), use_container_width=True)
        else:
            st.info("ℹ️ Nenhum material cadastrado ainda.")

    elif modo == "Adicionar":
        st.subheader("Adicionar Novo Tipo de Material")
        with st.form("form_add_tipo_material", clear_on_submit=True):
            nome = st.text_input("Nome do Material*", max_chars=50)
            descricao = st.text_area("Descrição Técnica", height=100)

            if st.form_submit_button("💾 Salvar Novo Material"):
                if not nome.strip():
                    st.error("⚠️ O nome do material é obrigatório.")
                else:
                    success, message = cadastrar_tipo_material_db(
                        usuario_id=st.session_state['usuario_id'],
                        nome=nome.strip(),
                        descricao=descricao.strip() if descricao else None
                    )
                    
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

    elif modo == "Editar":
        st.subheader("Editar Tipo de Material Existente")

        if df.empty:
            st.warning("Nenhum tipo de material cadastrado para editar.")
        else:
            material_id = st.selectbox(
                "Selecione o material para editar:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} "
            )

            material = df[df['id'] == material_id].iloc[0]

            with st.form("form_edit_tipo_material"):
                novo_nome = st.text_input("Nome do Material*", value=material['nome'], max_chars=50)
                nova_descricao = st.text_area("Descrição Técnica", value=material['descricao'] or "", height=100)

                if st.form_submit_button("💾 Salvar Alterações"):
                    if not novo_nome.strip():
                        st.error("⚠️ O nome do material é obrigatório.")
                    else:
                        try:
                            # Verifica se o novo nome já existe (excluindo o próprio material)
                            existente = pd.read_sql(
                                "SELECT 1 FROM tipos_materiais WHERE LOWER(nome) = LOWER(?) AND id != ?", 
                                conn, 
                                params=(novo_nome.strip(), material_id)
                            ).empty
                            
                            if not existente:
                                st.error(f"⛔ Já existe outro material com o nome '{novo_nome.strip()}'")
                            else:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE tipos_materiais 
                                    SET nome = ?, descricao = ?
                                    WHERE id = ?
                                """, (novo_nome.strip(), nova_descricao.strip() or None, material_id))
                                conn.commit()
                                st.success("✅ Material atualizado com sucesso!")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar material: {str(e)}")

    elif modo == "Excluir":
        st.subheader("Excluir Tipo de Material")

        if df.empty:
            st.warning("Nenhum tipo de material cadastrado para excluir.")
        else:
            material_id = st.selectbox(
                "Selecione o material para excluir:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} )"
            )

            material = df[df['id'] == material_id].iloc[0]

            st.warning("⚠️ Você está prestes a excluir permanentemente o material:")
            st.write(f"**Nome:** {material['nome']}")
            st.write(f"**Descrição:** {material['descricao'] or 'Sem descrição'}")

            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                try:
                    # Lista de tabelas para verificar
                    tabelas_para_verificar = [
                        ("materiais_utilizados", "tipo_material_id"),
                        ("estoque", "material_id"),
                        # Adicione mais aqui se precisar
                    ]

                    em_uso = False

                    for tabela, coluna in tabelas_para_verificar:
                        try:
                            query = f"SELECT 1 FROM {tabela} WHERE {coluna} = ? LIMIT 1"
                            resultado = pd.read_sql(query, conn, params=(material_id,))
                            if not resultado.empty:
                                em_uso = True
                                st.error(
                                    f"⛔ Este material está vinculado à tabela **{tabela}** e não pode ser excluído."
                                )
                                break  # Para na primeira ocorrência de vínculo
                        except Exception as e:
                            # Mostra o aviso se a tabela não existir
                            st.info(f"Tabela `{tabela}` não existe ou não pode ser consultada: {e}")

                    if not em_uso:
                        conn.execute("DELETE FROM tipos_materiais WHERE id = ?", (material_id,))
                        conn.commit()
                        st.success("✅ Material excluído com sucesso!")
                        time.sleep(1)
                        st.rerun()

                except Exception as e:
                    st.error(f"Erro ao excluir material: {str(e)}")



    conn.close()
    
    # Rodapé
    if st.button("← Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()

def cadastrar_tipo_material_db(usuario_id, nome, descricao=None):
    """Insere novo tipo de material no banco de dados"""
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO tipos_materiais (usuario_id, nome, descricao)
            VALUES (?, ?, ?)
        """, (usuario_id, nome, descricao))
        conn.commit()
        return (True, "✅ Material cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        return (False, "⛔ Já existe um material com esse nome.")
    except Exception as e:
        return (False, f"Erro inesperado: {str(e)}")
    finally:
        conn.close()

def gerenciar_tipos_zonas():
    """Página de gerenciamento dos tipos de zonas de barragens"""
    st.title("⚙️ Gerenciamento de tipos de zonas de barragens")
    
    # Conexão com o banco
    conn = conectar_db()
    
    # Modo de visualização/edição
    modo = st.radio("Modo:", ["Visualizar", "Adicionar", "Editar", "Excluir"], horizontal=True)
    
    # Carrega os dados existentes
    df = pd.read_sql("SELECT id, nome, descricao FROM tipos_zonas_bar ORDER BY nome", conn)
    
    if modo == "Visualizar":
        st.subheader("Tipos de Zonas Cadastradas")
        st.dataframe(df.set_index('id'), use_container_width=True)
        
    elif modo == "Adicionar":
        st.subheader("Adicionar Novo Tipo de Zona")
        with st.form("form_add_zona", clear_on_submit=True):
            nome = st.text_input("Nome da Zona*", max_chars=100)
            descricao = st.text_area("Descrição Técnica", height=100)
            
            if st.form_submit_button("💾 Salvar Novo Tipo"):
                if nome:
                    try:
                        conn.execute("INSERT INTO tipos_zonas_bar (nome, descricao) VALUES (?, ?)", 
                                   (nome.strip(), descricao.strip() if descricao else None))
                        conn.commit()
                        st.success("Tipo de zona adicionado com sucesso!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Já existe um tipo de zona com este nome")
                else:
                    st.error("O nome da zona é obrigatório")
    
    elif modo == "Editar":
        st.subheader("Editar Tipo de Zona Existente")
        
        if df.empty:
            st.warning("Nenhum tipo de zona cadastrado para editar")
        else:
            zona_id = st.selectbox(
                "Selecione o tipo de zona para editar:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} "
            )
            
            zona = df[df['id']==zona_id].iloc[0]
            
            with st.form("form_edit_zona"):
                novo_nome = st.text_input("Nome da Zona*", value=zona['nome'], max_chars=100)
                nova_descricao = st.text_area(
                    "Descrição Técnica", 
                    value=zona['descricao'] if zona['descricao'] else "",
                    height=100
                )
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    if novo_nome:
                        try:
                            conn.execute(
                                "UPDATE tipos_zonas_bar SET nome = ?, descricao = ? WHERE id = ?",
                                (novo_nome.strip(), nova_descricao.strip() if nova_descricao else None, zona_id)
                            )
                            conn.commit()
                            st.success("Tipo de zona atualizado com sucesso!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Já existe outro tipo de zona com este nome")
                    else:
                        st.error("O nome da zona é obrigatório")
    
    elif modo == "Excluir":
        st.subheader("Excluir Tipo de Zona")
        
        if df.empty:
            st.warning("Nenhum tipo de zona cadastrado para excluir")
        else:
            zona_id = st.selectbox(
                "Selecione o tipo de zona para excluir:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} "
            )
            
            zona = df[df['id']==zona_id].iloc[0]
            
            st.warning(f"Você está prestes a excluir permanentemente o tipo de zona:")
            st.write(f"**Nome:** {zona['nome']}")
            st.write(f"**Descrição:** {zona['descricao'] or 'Sem descrição'}")
            
            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                try:
                    conn.execute("DELETE FROM tipos_zonas_bar WHERE id = ?", (zona_id,))
                    conn.commit()
                    st.success("Tipo de zona excluído com sucesso!")
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Erro ao excluir: {str(e)}")
    
    conn.close()

def exibir_formulario_cadastro_barragem():
    """Exibe o formulário padrão de cadastro de barragem"""
    st.title("📝 Cadastro de barragens")   

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

def excluir_tipo_material_db(material_id):
    """Exclui um tipo de material pelo ID"""
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM tipos_materiais WHERE id = ?", (material_id,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir material: {e}")
        return False
    finally:
        conn.close()

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
        st.success(f"Tipo de barragem cadastrado com sucesso!")
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

def gerenciar_tipos_barragem():
    """Página de gerenciamento dos tipos de barragem"""
    st.title("⚙️ Gerenciamento de tipos de barragem")

    # Verifica permissão
    if not st.session_state.get('is_admin'):
        st.error("⛔ Acesso permitido apenas para administradores")
        if st.button("← Voltar"):
            st.session_state['pagina'] = "principal"
            st.rerun()
        return

    # Conexão com o banco
    conn = conectar_db()

    # Modo de operação
    modo = st.radio("Modo:", ["Visualizar", "Adicionar", "Editar", "Excluir"], horizontal=True)

    # Carrega os tipos existentes
    df = pd.read_sql("SELECT id, nome, descricao, referencia_tecnica, image_path FROM tipos_barragem ORDER BY nome", conn)

    if modo == "Visualizar":
        st.subheader("Tipos de barragem cadastrados")
        st.dataframe(df.set_index('id'), use_container_width=True)

    elif modo == "Adicionar":
        st.subheader("Adicionar Novo Tipo de Barragem")
        with st.form("form_add_tipo_barragem", clear_on_submit=True):
            nome = st.text_input("Nome do Tipo*", max_chars=50)
            descricao = st.text_area("Descrição Técnica*", height=100)
            referencia = st.text_input("Referência Normativa (opcional)")
            imagem = st.file_uploader("Imagem Representativa (opcional)", type=["jpg", "jpeg", "png"])

            if st.form_submit_button("💾 Salvar Novo Tipo"):
                # Processa a imagem se houver
                caminho_imagem = None
                if imagem is not None:
                    if imagem.size > 5 * 1024 * 1024:
                        st.error("Arquivo muito grande (máx. 5MB)")
                        return
                    os.makedirs("uploads/tipos_barragem", exist_ok=True)
                    extensao = os.path.splitext(imagem.name)[1].lower()
                    nome_arquivo = f"tipo_{nome.lower().replace(' ', '_')}_{int(time.time())}{extensao}"
                    caminho_imagem = f"uploads/tipos_barragem/{nome_arquivo}"
                    with open(caminho_imagem, "wb") as f:
                        f.write(imagem.getbuffer())

                # Insere no banco usando função robusta
                resultado = cadastrar_tipo_barragem_db(
                    usuario_id=st.session_state['usuario_id'],
                    nome=nome.strip(),
                    descricao=descricao.strip(),
                    referencia_tecnica=referencia.strip() if referencia else None,
                    image_path=caminho_imagem
                )

                if resultado:
                    st.success("Tipo de barragem adicionado com sucesso!")
                    st.rerun()

    elif modo == "Editar":
        st.subheader("Editar Tipo de Barragem Existente")

        if df.empty:
            st.warning("Nenhum tipo de barragem cadastrado para editar.")
        else:
            tipo_id = st.selectbox(
                "Selecione o tipo de barragem para editar:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} "
            )

            tipo = df[df['id'] == tipo_id].iloc[0]

            with st.form("form_edit_tipo_barragem"):
                novo_nome = st.text_input("Nome do Tipo*", value=tipo['nome'], max_chars=50)
                nova_descricao = st.text_area("Descrição Técnica*", value=tipo['descricao'], height=100)
                nova_referencia = st.text_input("Referência Normativa (opcional)", value=tipo['referencia_tecnica'] or "")
                nova_imagem = st.file_uploader("Substituir Imagem Representativa (opcional)", type=["jpg", "jpeg", "png"])

                if st.form_submit_button("💾 Salvar Alterações"):
                    caminho_imagem = tipo['image_path']
                    if nova_imagem is not None:
                        if nova_imagem.size > 5 * 1024 * 1024:
                            st.error("Arquivo muito grande (máx. 5MB)")
                            return
                        os.makedirs("uploads/tipos_barragem", exist_ok=True)
                        extensao = os.path.splitext(nova_imagem.name)[1].lower()
                        nome_arquivo = f"tipo_{novo_nome.lower().replace(' ', '_')}_{int(time.time())}{extensao}"
                        caminho_imagem = f"uploads/tipos_barragem/{nome_arquivo}"
                        with open(caminho_imagem, "wb") as f:
                            f.write(nova_imagem.getbuffer())

                    try:
                        conn.execute("""
                            UPDATE tipos_barragem 
                            SET nome = ?, descricao = ?, referencia_tecnica = ?, image_path = ?
                            WHERE id = ?
                        """, (novo_nome.strip(), nova_descricao.strip(), nova_referencia.strip() or None, caminho_imagem, tipo_id))
                        conn.commit()
                        st.success("Tipo de barragem atualizado com sucesso!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Já existe outro tipo de barragem com este nome.")

    elif modo == "Excluir":
        st.subheader("Excluir Tipo de Barragem")

        if df.empty:
            st.warning("Nenhum tipo de barragem cadastrado para excluir.")
        else:
            tipo_id = st.selectbox(
                "Selecione o tipo de barragem para excluir:",
                options=df['id'],
                format_func=lambda x: f"{df[df['id']==x]['nome'].values[0]} "
            )

            tipo = df[df['id'] == tipo_id].iloc[0]

            st.warning("⚠️ Você está prestes a excluir permanentemente o tipo de barragem:")
            st.write(f"**Nome:** {tipo['nome']}")
            st.write(f"**Descrição:** {tipo['descricao']}")
            st.write(f"**Referência:** {tipo['referencia_tecnica'] or 'Sem referência'}")

            if tipo['image_path'] and os.path.exists(tipo['image_path']):
                st.image(tipo['image_path'], caption="Imagem Representativa", use_column_width=True)

            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                try:
                    conn.execute("DELETE FROM tipos_barragem WHERE id = ?", (tipo_id,))
                    conn.commit()
                    st.success("Tipo de barragem excluído com sucesso!")
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Erro ao excluir: {str(e)}")

    conn.close()

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

        with st.expander(f"{nome_barragem}"):
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

# Página principal com gestão completa de barragens
def pagina_principal():
    """Página principal após login com gestão completa de barragens"""
    st.title("📊 Página Inicial - Sistema inSID")
    st.write(f"👤 Usuário logado: {st.session_state['usuario_nome']}")
    
    # Barra de seleção de barragem em análise
    st.subheader("🔍 Barragem em Análise")
    barragens_usuario = obter_barragens_usuario(st.session_state['usuario_id'])
    barragem_analise = obter_barragem_analise(st.session_state['usuario_id'])

    if barragem_analise:
        st.success(f"Barragem atual em análise: {barragem_analise[2]}")

    else:
        st.warning("Nenhuma barragem selecionada para análise")
    
    if barragens_usuario:
        # Seleciona a barragem atual em análise ou vazio se nenhuma
        barragem_selecionada = str(barragem_analise[0]) if barragem_analise else ""
        
        # Cria lista de opções para o selectbox
        opcoes_barragens = {str(b[0]): f"{b[1]}" for b in barragens_usuario}
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

def menu_lateral():
    """Menu lateral otimizado para performance"""
    with st.sidebar:
        # Variável para controlar redirecionamentos
        redirecionar = None
               
        # Seção de Administração
        if st.session_state.get('is_admin'):
            st.subheader("🛡️ Administração")
            if st.button("👥 Gerenciar Usuários"):
                redirecionar = "admin_usuarios"

        st.markdown("---")

        # Menu Principal
        if st.button("🏠 Metodologia inSID"):
            redirecionar = "principal"
        
        st.markdown("---")

        # Menu Principal
        st.subheader("📋 Gerenciar barragens")
        if st.button("➕ Cadastrar nova barragem"):
            redirecionar = "cadastro_barragem"
        
        # Seção de Administração
        if st.session_state.get('is_admin'):

            st.markdown("---")

            st.subheader("⚙️Configurações das barragens")

            if st.button("➕ Tipos de barragens"):
                redirecionar = "gerenciar_tipos_barragem"
            
            if st.button("➕ Zonas das barragens"):
                redirecionar = "cadastro_zonas_barragem"
            
            if st.button("➕ Tipos de materiais"):
                redirecionar = "gerenciar_tipos_materiais"
            
            st.subheader("⚙️Configurações dos modos de falha")

            if st.button("➕ Tipos de modos de falha"):
                redirecionar = "gerenciar_tipos_modo_falha"
            
            if st.button("➕ Gerenciar modos de falha"):
                redirecionar = "gerenciar_modos_falha"
                
            if st.button("➕ Gerenciar anomalias"):
                redirecionar = "gerenciar_anomalias"
            
            

        st.markdown("---")
        
        # Logout
        if st.button("🚪 Sair"):
            logout()
            return  # Encerra a execução após logout
        
        # Processa redirecionamento se necessário
        if redirecionar:
            st.session_state['pagina'] = redirecionar
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

        menu_lateral()

        if st.session_state.get('pagina') == "cadastro_barragem":
            exibir_formulario_cadastro_barragem()

        elif st.session_state.get('pagina') == "admin_usuarios" and st.session_state.get('is_admin'):
            pagina_admin_usuarios()

        elif st.session_state.get('pagina') == "gerenciar_tipos_barragem":
            gerenciar_tipos_barragem()
        
        elif st.session_state.get('pagina') == "cadastro_zonas_barragem":
            gerenciar_tipos_zonas()
        
        elif st.session_state.get('pagina') == "gerenciar_tipos_materiais":
            gerenciar_tipos_materiais()
        
        elif st.session_state.get('pagina') == "gerenciar_tipos_modo_falha":
            gerenciar_tipos_modo_falha()
            
        elif st.session_state.get('pagina') == "gerenciar_modos_falha":
            gerenciar_modos_falha()    

        elif st.session_state.get('pagina') == "gerenciar_anomalias":
            gerenciar_anomalias()        
            
        else:
            pagina_principal()

if __name__ == "__main__":
    main()