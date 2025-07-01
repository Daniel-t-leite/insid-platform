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
