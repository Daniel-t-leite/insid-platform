import streamlit as st
import re
# import pandas as pd


from db import (
    hash_senha, criar_usuario, verificar_credenciais, email_existe,
    obter_proximo_codigo_usuario, obter_tipos_barragem, obter_tipos_fundacao,
    criar_barragem, listar_barragens, obter_usuario_id,
    adicionar_tipo_barragem, adicionar_tipo_fundacao,
    remover_tipo_barragem, remover_tipo_fundacao, listar_usuarios, 
    atualizar_status_usuario, atualizar_admin_usuario, excluir_usuario,
    obter_modos_falha, obter_materiais, obter_condicoes_criticas, obter_anomalias,
    inferir_modos_falha, definir_barragem_analise, obter_barragem_analise, 
    listar_barragens_com_status, inserir_material, listar_materiais, excluir_material, 
    conectar_db, inserir_condicao_critica, listar_condicoes_criticas, 
    excluir_condicao_critica, excluir_anomalia, listar_localizacoes_anomalias, 
    listar_categorias_anomalias, listar_localizacoes_anomalias, 
    listar_categorias_anomalias, obter_anomalia, listar_anomalias, inserir_anomalia, atualizar_anomalia,
    closing, pd
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

def pagina_principal():
    """Página principal após login"""
    st.title("📊 Página Inicial - Sistema inSID")
    st.write(f"👤 Usuário logado: {st.session_state['usuario_nome']}")
    
    # Mostra a barragem atual em análise
    barragem_analise = obter_barragem_analise()
    if barragem_analise:
        st.success(f"🔍 Barragem em análise: {barragem_analise[1]} (ID: {barragem_analise[0]})")
    else:
        st.warning("Nenhuma barragem definida para análise")
    
    if st.session_state['is_admin']:
        st.write("🛡️ Você tem privilégios de administrador")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Cadastrar Barragem"):
            st.session_state['pagina'] = "cadastro_barragem"
            st.rerun()
    with col2:
        if st.button("🔍 Identificar Modos de Falha", key="btn_identificar_falha_1"):
            if barragem_analise:
                st.session_state['pagina'] = "identificacao_falhas"
                st.rerun()
            else:
                st.error("Defina uma barragem para análise primeiro")
    
    if st.session_state.get('is_admin'):
        if st.button("👥 Gerenciar Usuários", key="btn_gerenciar_usuarios_1"):
            st.session_state['pagina'] = "admin_usuarios"
            st.rerun()
    
    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

def pagina_admin_tipos():
    """Página de administração de tipos"""
    st.title("⚙️ Administração de Tipos")
    
    tab1, tab2 = st.tabs(["Tipos de Barragem", "Tipos de Fundação"])
    
    with tab1:
        st.subheader("Tipos de Barragem")
        tipos = obter_tipos_barragem()
        
        if tipos:
            st.write("Tipos disponíveis:")
            for tipo_id, nome in tipos:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"- {nome}")
                with col2:
                    if st.button(f"Remover", key=f"rm_barragem_{tipo_id}"):
                        if remover_tipo_barragem(tipo_id):
                            st.success(f"Tipo removido!")
                            st.rerun()
        
        with st.expander("Adicionar novo tipo"):
            with st.form("novo_tipo_barragem"):
                nome = st.text_input("Nome do tipo")
                descricao = st.text_area("Descrição")
                if st.form_submit_button("Adicionar"):
                    if nome and adicionar_tipo_barragem(nome, descricao):
                        st.success("Tipo adicionado!")
                        st.rerun()
    
    with tab2:
        st.subheader("Tipos de Fundação")
        tipos = obter_tipos_fundacao()
        
        if tipos:
            st.write("Tipos disponíveis:")
            for tipo_id, nome in tipos:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"- {nome}")
                with col2:
                    if st.button(f"Remover", key=f"rm_fundacao_{tipo_id}"):
                        if remover_tipo_fundacao(tipo_id):
                            st.success(f"Tipo removido!")
                            st.rerun()
        
        with st.expander("Adicionar novo tipo"):
            with st.form("novo_tipo_fundacao"):
                nome = st.text_input("Nome do tipo")
                descricao = st.text_area("Descrição")
                if st.form_submit_button("Adicionar"):
                    if nome and adicionar_tipo_fundacao(nome, descricao):
                        st.success("Tipo adicionado!")
                        st.rerun()


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
    """Página de cadastro de barragens"""
    st.title("📋 Cadastro de Barragens")
    
    opcoes = ["Cadastrar", "Visualizar"]
    if st.session_state.get('is_admin'):
        opcoes.append("Administrar Tipos")
    
    aba = st.sidebar.selectbox("Menu", opcoes)

    if aba == "Cadastrar":
        st.subheader("➕ Nova Barragem")
        
        tipos_barragem = obter_tipos_barragem()
        tipos_fundacao = obter_tipos_fundacao()
        
        if not tipos_barragem or not tipos_fundacao:
            st.error("Erro ao carregar tipos!")
            return
        
        nome = st.text_input("Nome da Barragem")
        tipo_selecionado = st.selectbox(
            "Tipo de Barragem",
            [tipo[1] for tipo in tipos_barragem]
        )
        fundacao_selecionada = st.selectbox(
            "Tipo de Fundação",
            [tipo[1] for tipo in tipos_fundacao]
        )
        localizacao = st.text_input("Localização (latitude,longitude)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Salvar"):
                if nome and tipo_selecionado and fundacao_selecionada and localizacao:
                    criar_barragem(
                        st.session_state['usuario_id'],
                        nome,
                        tipo_selecionado,
                        fundacao_selecionada,
                        localizacao
                    )
                    st.success("✅ Barragem cadastrada com sucesso!")
                else:
                    st.warning("⚠️ Preencha todos os campos.")
        
        with col2:
            # Opção para definir como barragem em análise logo após cadastro
            if st.button("Salvar e Definir como Análise"):
                if nome and tipo_selecionado and fundacao_selecionada and localizacao:
                    criar_barragem(
                        st.session_state['usuario_id'],
                        nome,
                        tipo_selecionado,
                        fundacao_selecionada,
                        localizacao
                    )
                    # Obtém o ID da última barragem inserida
                    with closing(conectar_db()) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT last_insert_rowid()")
                        barragem_id = cursor.fetchone()[0]
                        definir_barragem_analise(barragem_id)
                    st.success("✅ Barragem cadastrada e definida como análise atual!")
    
    # Adicionar espaço e botão de voltar
    st.write("")
    if st.button("⬅️ Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()
    
    elif aba == "Visualizar":
        st.subheader("📄 Barragens Cadastradas")
        
        # Mostra qual barragem está atualmente em análise
        barragem_analise = obter_barragem_analise()
        if barragem_analise:
            st.info(f"Barragem em análise atual: {barragem_analise[1]} (ID: {barragem_analise[0]})")
        
        dados = listar_barragens_com_status()
        if not dados.empty:
            # Exibe a tabela com opção de seleção
            st.data_editor(
                dados,
                column_config={
                    "em_analise": st.column_config.CheckboxColumn(
                        "Em Análise",
                        help="Selecione a barragem para análise",
                        default=False,
                    )
                },
                disabled=["id", "usuario", "nome", "tipo", "fundacao", "localizacao", "data_criacao"],
                hide_index=True,
                use_container_width=True,
                key="editor_barragens"
            )
            
            # Botão para aplicar a seleção
            if st.button("Definir Barragem Selecionada como Análise", key="btn_definir_barragem"):
                edited_rows = st.session_state["editor_barragens"]["edited_rows"]
                selected_id = None
                
                for row_idx, changes in edited_rows.items():
                    if changes.get("em_analise") == True:
                        selected_id = dados.iloc[row_idx]["id"]
                        break
                
                if selected_id:                    
                    if definir_barragem_analise(int(selected_id)):
                        st.success(f"Barragem ID {selected_id} definida como análise atual!")
                        st.rerun()
                    else:
                        st.error("Erro ao definir barragem para análise")
                else:
                    st.warning("Selecione uma barragem marcando a coluna 'Em Análise'")
        else:
            st.info("Nenhuma barragem cadastrada ainda.")
    
    elif aba == "Administrar Tipos" and st.session_state.get('is_admin'):
        pagina_admin_tipos()



# ... Modos de Falha ...


def pagina_identificacao_falhas():
    """Página para identificação de modos de falha"""
    st.title("🔍 Identificação de Modos de Falha")

    # --- MENU LATERAL (apenas para administradores) ---
    if st.session_state.get('is_admin'):
        with st.sidebar:
            st.markdown("### 🔧 Cadastros Auxiliares")
            opcao_cadastro = st.radio(
                "Selecione uma categoria para cadastrar/editar:",
                ["Identificação de Modos de Falha", "Materiais Identificados", "Condições críticas observadas", "Anomalias Detectadas"],
                index=0,
                key="opcao_cadastro_sidebar"
            )

    # Mostra a barragem atual em análise
    barragem_analise = obter_barragem_analise()
    if barragem_analise:
        st.success(f"🔍 Barragem em análise: {barragem_analise[1]} (ID: {barragem_analise[0]})")
    else:
        st.warning("Nenhuma barragem definida para análise")

    with st.expander("🔧 Parâmetros da Barragem", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            tipo_barragem_input = st.text_input("Tipo de Barragem", value=barragem_analise[2], disabled=True)

            materiais = obter_materiais()
            #print(materiais)
            materiais_selecionados = st.multiselect(
                "Materiais Identificados",
                materiais,
                format_func=lambda x: x[1],
                key="materiais_select"
            )

        with col2:
            tipo_fundacao_id = st.text_input("Tipo de fundação", value=barragem_analise[3], disabled=True)

            condicoes = obter_condicoes_criticas()
            condicoes_selecionadas = st.multiselect(
                "Condições críticas observadas",
                condicoes,
                format_func=lambda x: x[1],
                key="condicoes_select"
            )

    with st.expander("🛠️ Anomalias Detectadas", expanded=True):
        anomalias = obter_anomalias()
        anomalias_selecionadas = st.multiselect(
            "Selecione as anomalias detectadas",
            anomalias,
            format_func=lambda x: f"{x[1]} ({x[3]} - {x[4]})",
            key="anomalias_select"
        )

    if st.button("🔎 Identificar Modos de Falha Potenciais", type="primary"):
        if barragem_analise and barragem_analise[2] and barragem_analise[3]:  # tipo_barragem e tipo_fundacao
            materiais_ids = [m[0] for m in materiais_selecionados]
            condicoes_ids = [c[0] for c in condicoes_selecionadas]
            anomalias_ids = [a[0] for a in anomalias_selecionadas]

            resultados = inferir_modos_falha(
                barragem_analise[2],  # tipo_barragem
                barragem_analise[3],  # tipo_fundacao
                materiais_ids,
                condicoes_ids,
                anomalias_ids
            )

            if not resultados.empty:
                st.subheader("📊 Resultados da Análise")

                for _, row in resultados.iterrows():
                    with st.container():
                        st.markdown(f"### {row['codigo']} - {row['nome']}")
                        st.markdown(f"**Descrição:** {row['descricao']}")

                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.markdown(f"**Nível de Risco:** <span style='color:{row['cor_alerta']};font-weight:bold'>{row['nivel']}</span>",
                                       unsafe_allow_html=True)
                            st.progress(min(int(row['peso_barragem'] + row['peso_materiais'] + row['peso_condicoes'] + row['peso_anomalias']), 100) / 100)

                        with col2:
                            st.markdown("**Fatores Contribuintes:**")
                            st.markdown(f"- Compatibilidade com tipo de barragem: {row['peso_barragem']}/5")
                            st.markdown(f"- Materiais suscetíveis: {row['peso_materiais']}/4")
                            st.markdown(f"- Condições críticas: {row['peso_condicoes']}/5")
                            st.markdown(f"- Anomalias correspondentes: {row['peso_anomalias']}/5")

                        st.markdown(f"**Ação Recomendada:** {row['acao_especifica']}")
                        st.divider()
            else:
                st.warning("Nenhum modo de falha identificado com os parâmetros fornecidos.")
        else:
            st.error("Tipo de barragem ou fundação não definidos.")

    if st.button("⬅️ Voltar"):
        st.session_state['pagina'] = "principal"
        st.rerun()

    # --- NAVEGAÇÃO PARA PÁGINAS DE CADASTRO (somente admin) ---
    if st.session_state.get('is_admin'):
        if opcao_cadastro == "Materiais Identificados":
            # Não mudar de página!
            pagina_admin_materiais()

        elif opcao_cadastro == "Condições críticas observadas":
            # Não mudar de página!
            pagina_admin_condicoes_criticas()

        elif opcao_cadastro == "Anomalias Detectadas":
            st.session_state["pagina"] = "cadastro_anomalias"
            st.rerun()


#------------------ Cadastro de Materiais ------------------
def pagina_admin_materiais():
    st.subheader("🧱 Gerenciar Materiais Identificados")
    # --- Formulário de cadastro ---
    with st.container():
        with st.form("form_cadastro_material", clear_on_submit=True):
            st.markdown("### ➕ Cadastrar Novo Material")
            nome = st.text_input("Nome do Material*")
            descricao = st.text_area("Descrição")
            classificacao = st.text_input("Classificação Unificada")
            propriedades_json = st.text_area("Propriedades (em formato JSON)")
            
            submitted = st.form_submit_button("Salvar Material")

            if submitted:                
                if nome:
                    sucesso = inserir_material(nome, descricao, classificacao, propriedades_json)                    
                    if sucesso:
                        st.success("✅ Material cadastrado com sucesso!")                        
                    else:
                        st.error("Erro ao cadastrar. Verifique se o nome já existe.")                        
                else:
                    st.warning("⚠️ O campo 'Nome' é obrigatório.")                    

        st.divider()

        # --- Tabela de materiais ---
        materiais = listar_materiais()
        if materiais:
            df = pd.DataFrame(materiais, columns=["ID", "Nome", "Descrição", "Classificação", "Propriedades JSON"])
            
            st.subheader("📋 Materiais Cadastrados")
            
            with st.form("form_excluir_material"):
                linha_selecionada = st.selectbox("Selecione um material para excluir", df["Nome"])
                
                if st.form_submit_button("🗑️ Excluir"):
                    material_id = int(df[df["Nome"] == linha_selecionada]["ID"].values[0])
                    if excluir_material(material_id):
                        st.success("Material excluído com sucesso.")
                    else:
                        st.error("Erro ao excluir material.")

            st.dataframe(df.drop(columns=["ID"]), use_container_width=True)
        else:
            st.info("Nenhum material cadastrado ainda.")

#------------------ Cadastro de Condições Criticas ----------------
def pagina_admin_condicoes_criticas():
    st.subheader("🌩️ Gerenciar Condições Críticas Observadas")

    with st.container():
        with st.form("form_cadastro_condicao", clear_on_submit=True):
            st.markdown("### ➕ Cadastrar Nova Condição Crítica")
            nome = st.text_input("Nome da Condição*")
            tipo = st.selectbox("Tipo da Condição*", ["Hidrológica", "Geológica", "Estrutural", "Operacional", "Outro"])
            descricao = st.text_area("Descrição")
            referencia = st.text_input("Referência Técnica")

            submitted = st.form_submit_button("Salvar Condição")

            if submitted:
                if nome and tipo:
                    sucesso = inserir_condicao_critica(nome, tipo, descricao, referencia)
                    if sucesso:
                        st.success("✅ Condição crítica cadastrada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao cadastrar. Verifique se o nome já existe.")
                else:
                    st.warning("⚠️ Os campos 'Nome' e 'Tipo' são obrigatórios.")

    st.divider()

    condicoes = listar_condicoes_criticas()
    if condicoes:
        df = pd.DataFrame(condicoes, columns=["ID", "Nome", "Tipo", "Descrição", "Referência Técnica"])
        st.subheader("📋 Condições Críticas Cadastradas")

        with st.form("form_excluir_condicao"):
            linha_selecionada = st.selectbox("Selecione uma condição para excluir", df["Nome"])
            if st.form_submit_button("🗑️ Excluir"):
                condicao_id = int(df[df["Nome"] == linha_selecionada]["ID"].values[0])
                if excluir_condicao_critica(condicao_id):
                    st.success("Condição crítica excluída com sucesso.")
                    st.rerun()
                else:
                    st.error("Erro ao excluir condição crítica.")

        st.dataframe(df.drop(columns=["ID"]), use_container_width=True)
    else:
        st.info("Nenhuma condição crítica cadastrada ainda.")

    #-------------------- Administração de anomalis----------
    def pagina_admin_anomalias():
    #"""Página de gerenciamento de anomalias"""
    
    # Configuração do layout
    st.set_page_config(layout="wide")
    st.title("🛠️ Gerenciamento de Anomalias")
    st.markdown("---")
    
    # Navegação
    if st.button("⬅️ Voltar"):
        st.session_state['pagina'] = "identificacao_falhas"
        st.rerun()
    
    # Abas para diferentes funcionalidades
    tab_cadastro, tab_lista = st.tabs(["Cadastrar/Editar", "Listagem"])
    
    with tab_cadastro:
        # Modo edição (se houver ID na sessão)
        editar_id = st.session_state.get('editar_anomalia_id')
        anomalia_editando = None
        
        if editar_id:
            try:
                anomalia_editando = obter_anomalia(editar_id)
            except Exception as e:
                st.error(f"Erro ao carregar anomalia: {str(e)}")
                st.session_state.pop('editar_anomalia_id', None)
        
        with st.form("form_anomalia", clear_on_submit=True):
            # Campos do formulário
            if anomalia_editando:
                st.markdown(f"### ✏️ Editando Anomalia: {anomalia_editando[1]}")
                codigo = st.text_input("Código*", value=anomalia_editando[1])
                nome = st.text_input("Nome*", value=anomalia_editando[2])
            else:
                st.markdown("### ➕ Nova Anomalia")
                codigo = st.text_input("Código*", placeholder="Ex: AN-EST-001")
                nome = st.text_input("Nome*")
            
            descricao = st.text_area("Descrição*", 
                                   value=anomalia_editando[3] if anomalia_editando else "",
                                   height=100)
            
            # Obter opções para selects
            try:
                categorias = listar_categorias_anomalias()
                localizacoes = listar_localizacoes_anomalias()
                
                col1, col2 = st.columns(2)
                with col1:
                    categoria_id = st.selectbox(
                        "Categoria*",
                        categorias,
                        index=[c[0] for c in categorias].index(anomalia_editando[4]) if anomalia_editando else 0,
                        format_func=lambda x: dict(categorias).get(x, x)
                    )
                with col2:
                    localizacao_id = st.selectbox(
                        "Localização*",
                        localizacoes,
                        index=[l[0] for l in localizacoes].index(anomalia_editando[5]) if anomalia_editando else 0,
                        format_func=lambda x: dict(localizacoes).get(x, x)
                    )
            except Exception as e:
                st.error(f"Erro ao carregar opções: {str(e)}")
            
            col1, col2 = st.columns(2)
            with col1:
                gravidade = st.slider(
                    "Gravidade Padrão (1-5)", 
                    min_value=1, max_value=5, 
                    value=anomalia_editando[6] if anomalia_editando and anomalia_editando[6] else 3
                )
            with col2:
                referencia = st.text_input(
                    "Referência Técnica",
                    value=anomalia_editando[7] if anomalia_editando else ""
                )
            
            st.markdown("*Campos obrigatórios")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Salvar", type="primary")
            with col2:
                if anomalia_editando:
                    if st.form_submit_button("❌ Cancelar Edição"):
                        st.session_state.pop('editar_anomalia_id', None)
                        st.rerun()
            
            if submit:
                try:
                    if not all([codigo, nome, descricao]):
                        st.warning("Preencha todos os campos obrigatórios")
                    else:
                        if anomalia_editando:
                            atualizar_anomalia(
                                anomalia_editando[0],
                                codigo,
                                nome,
                                descricao,
                                categoria_id,
                                localizacao_id,
                                gravidade,
                                referencia if referencia else None
                            )
                            st.success("Anomalia atualizada com sucesso!")
                        else:
                            novo_id = inserir_anomalia(
                                codigo,
                                nome,
                                descricao,
                                categoria_id,
                                localizacao_id,
                                gravidade,
                                referencia if referencia else None
                            )
                            st.success(f"Anomalia cadastrada com sucesso! ID: {novo_id}")
                        
                        st.session_state.pop('editar_anomalia_id', None)
                        st.rerun()
                except ValueError as ve:
                    st.error(str(ve))
                except Exception as e:
                    st.error(f"Erro ao salvar: {str(e)}")
    
    with tab_lista:
        st.markdown("### 📋 Anomalias Cadastradas")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_codigo = st.text_input("Filtrar por código")
        with col2:
            try:
                categorias = listar_categorias_anomalias()
                filtro_categoria = st.selectbox(
                    "Filtrar por categoria",
                    [None] + [c[0] for c in categorias],
                    format_func=lambda x: dict(categorias).get(x, "Todas") if x else "Todas"
                )
            except Exception as e:
                st.error(f"Erro ao carregar categorias: {str(e)}")
                filtro_categoria = None
        with col3:
            try:
                localizacoes = listar_localizacoes_anomalias()
                filtro_localizacao = st.selectbox(
                    "Filtrar por localização",
                    [None] + [l[0] for l in localizacoes],
                    format_func=lambda x: dict(localizacoes).get(x, "Todas") if x else "Todas"
                )
            except Exception as e:
                st.error(f"Erro ao carregar localizações: {str(e)}")
                filtro_localizacao = None
        
        try:
            anomalias = listar_anomalias(
                filtro_codigo if filtro_codigo else None,
                filtro_categoria if filtro_categoria else None,
                filtro_localizacao if filtro_localizacao else None
            )
            
            if anomalias:
                # Converter para DataFrame
                df = pd.DataFrame(anomalias, columns=[
                    "ID", "Código", "Nome", "Descrição", 
                    "Categoria_ID", "Localização_ID",
                    "Gravidade", "Referência",
                    "Categoria", "Localização"
                ])
                
                # Configurar AgGrid
                gb = GridOptionsBuilder.from_dataframe(df[["Código", "Nome", "Categoria", "Localização", "Gravidade"]])
                gb.configure_pagination(paginationPageSize=10)
                gb.configure_selection('single', use_checkbox=True)
                gb.configure_column("Gravidade", cellRenderer=JsCode('''
                    function(params) {
                        const colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336'];
                        const value = params.value;
                        const color = colors[value - 1] || '#607D8B';
                        return `<div style="background-color:${color}; color:white; border-radius:15px; width:100%; text-align:center">${value}</div>`;
                    }
                '''))
                grid_options = gb.build()
                
                grid_response = AgGrid(
                    df,
                    gridOptions=grid_options,
                    height=400,
                    width='100%',
                    theme='streamlit',
                    update_mode='MODEL_CHANGED',
                    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS
                )
                
                selected = grid_response['selected_rows']
                if selected:
                    with st.expander("🔍 Detalhes da Anomalia Selecionada", expanded=True):
                        anomalia = selected[0]
                        st.markdown(f"**Código:** {anomalia['Código']}")
                        st.markdown(f"**Nome:** {anomalia['Nome']}")
                        st.markdown(f"**Categoria:** {anomalia['Categoria']}")
                        st.markdown(f"**Localização:** {anomalia['Localização']}")
                        st.markdown(f"**Gravidade Padrão:** {anomalia['Gravidade']}/5")
                        
                        if anomalia['Referência']:
                            st.markdown(f"**Referência Técnica:** {anomalia['Referência']}")
                        
                        st.markdown("**Descrição:**")
                        st.markdown(anomalia['Descrição'])
                        
                        st.markdown("---")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("✏️ Editar", key="btn_editar_anomalia"):
                                st.session_state['editar_anomalia_id'] = anomalia['ID']
                                st.rerun()
                        with col2:
                            if st.button("🗑️ Excluir", type="secondary", key="btn_excluir_anomalia"):
                                if st.checkbox("Confirmar exclusão?", key="confirm_excluir_anomalia"):
                                    try:
                                        if excluir_anomalia(anomalia['ID']):
                                            st.success("Anomalia excluída")
                                            st.rerun()
                                    except ValueError as ve:
                                        st.error(str(ve))
                                    except Exception as e:
                                        st.error(f"Erro ao excluir: {str(e)}")
            else:
                st.info("Nenhuma anomalia encontrada com os filtros aplicados")
        except Exception as e:
            st.error(f"Erro ao carregar anomalias: {str(e)}")
    
    st.markdown("---")
    st.caption("Sistema de Análise de Barragens - Módulo de Anomalias")



# Atualize a função main para incluir a nova página
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