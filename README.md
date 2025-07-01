# insid-platform
Open-source platform for embankment dam monitoring using the inSID methodology

# Plataforma inSID

Sistema de **inspeção, monitorização e diagnóstico de barragens de aterro** com foco na metodologia inSID.

## 🚀 Funcionalidades

✅ Cadastro e gestão de usuários (com controle de permissões admin)
✅ Cadastro e gestão de barragens (altura, comprimento, tipo, localização)
✅ Seleção de barragem em análise por usuário
✅ Listagem e edição de barragens
✅ Interface amigável com Streamlit
✅ Preparado para integração futura com módulos de identificação de modos de falha (em desenvolvimento)

---

## 📂 Estrutura do Projeto

- `app.py` - Aplicação principal Streamlit.
- `db.py` - Criação e operações do banco de dados SQLite.
- `inSID.db` - Será criado automaticamente ao iniciar.
- `requirements.txt` - Dependências necessárias.
- `inSID_logo.jpg` - (Opcional) Logo a ser exibido na tela de login.

---

## ⚙️ Instalação

1️⃣ Clone ou copie o repositório para a tua máquina:

```bash
git clone https://github.com/Daniel-t-leite/insid-platform
cd insid-platform

2️⃣ Cria e ativa um ambiente virtual (opcional mas recomendado):
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows

3️⃣ Instala as dependências:
pip install -r requirements.txt


4️⃣ Executa o sistema:
streamlit run app.py

O navegador abrirá automaticamente em http://localhost:8501.

🛠️ Pré-requisitos

Python 3.10 ou superior

Pip configurado corretamente

Permissão de escrita na pasta do projeto para criação do inSID.db

Usuário padrão: admin@insid.com
Senha: admin123

Versão oficial para colaboração com a plataforma:
https://insid-platform-dam-safety.streamlit.app/

🛰️ Autor

Plataforma inSID gerida e acompanhada por Daniel Teixeira Leite.
