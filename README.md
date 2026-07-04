# 📝 API de Notas Markdown

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-009688.svg)


Uma API RESTful robusta desenvolvida em **Python** e **FastAPI** para criação, gerenciamento, visualização e verificação gramatical de notas em formato Markdown.

Este projeto foi construído com foco em boas práticas de engenharia de software, incluindo tipagem estática (Pydantic), isolamento de dados, prevenção contra vulnerabilidades (como *Path Traversal*) e tratamento global de exceções.

---

## 📑 Sumário

- [Funcionalidades](#-funcionalidades)
- [Tecnologias Utilizadas](#️-tecnologias-utilizadas)
- [Pré-requisitos](#️-pré-requisitos)
- [Instalação e Execução](#-instalação-e-execução)
- [Endpoints da API](#-endpoints-da-api)
  
---

## ✨ Funcionalidades

- **📝 CRUD Completo de Notas:** Crie, liste, visualize e delete notas Markdown com facilidade.
- **📤 Upload Seguro de Arquivos:** Suporte a upload de arquivos `.md` com limite de tamanho (5MB) e sanitização de nomes de arquivo para evitar *Path Traversal*.
- **🔍 Renderização HTML Avançada:** Converta suas notas Markdown para HTML estático, incluindo:
  - *Syntax highlighting* para blocos de código (via `Pygments`)
  - Suporte a tabelas, listas de tarefas e links internos
  - Índice automático (Table of Contents)
  - CSS responsivo com tema claro/escuro
- **✅ Verificação Gramatical Integrada:** Analise o texto das notas em busca de erros gramaticais e receba sugestões de correção em português (pt-BR) utilizando `language-tool-python`.
- **🔒 Segurança em Primeiro Lugar:**
  - Sanitização de nomes de arquivo contra *Path Traversal*
  - Validação rigorosa de tipos MIME
  - Limite de tamanho de upload configurável
- **📊 Metadados Estruturados:** Cada nota salva gera automaticamente metadados em JSON com título, data de criação e tamanho.
- **📚 Documentação Automática:** Swagger UI interativo acessível em `/docs` e ReDoc em `/redoc`.
- **🏗️ Arquitetura Limpa:** Separação clara entre rotas, serviços, modelos e middleware.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| [FastAPI](https://fastapi.tiangolo.com/) | 0.104+ | Framework web assíncrono de alta performance |
| [Uvicorn](https://www.uvicorn.org/) | 0.24+ | Servidor ASGI |
| [Pydantic](https://docs.pydantic.dev/) | 2.5+ | Validação de dados e serialização |
| [LanguageTool Python](https://pypi.org/project/language-tool-python/) | 2.7+ | Verificação gramatical (requer Java) |
| [Python-Markdown](https://python-markdown.github.io/) | 3.5+ | Conversão Markdown → HTML |
| [Pygments](https://pygments.org/) | 2.16+ | Syntax highlighting em blocos de código |
| [Python-Multipart](https://pypi.org/project/python-multipart/) | 0.0.6+ | Upload de arquivos |

---

## ⚙️ Pré-requisitos

Antes de iniciar, certifique-se de ter instalado:

1. **Python 3.10 ou superior** → [Download](https://www.python.org/downloads/)
2. **Java Runtime Environment (JRE) 8 ou superior** → [Download](https://www.java.com/download/)
   > ⚠️ **Importante:** O serviço de gramática (`language-tool-python`) necessita do Java para executar o motor LanguageTool.
3. **pip** (gerenciador de pacotes Python) - Geralmente já incluso com Python 3.4+
4. **Git** → [Download](https://git-scm.com/downloads)

### Verificando as instalações:
```bash
python --version    # Deve mostrar 3.10 ou superior
java --version      # Deve mostrar 8 ou superior
pip --version       # Deve mostrar a versão instalada
git --version       # Deve mostrar a versão instalada
```
## 🚀 Instalação e Execução

### 1. Clone o repositório

```bash
git clone https://github.com/SEU-USUARIO/markdown-notes-api.git
cd markdown-notes-api
```
### 2.Crie e ative um ambiente virtual

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute o servidor

```bash
# Modo desenvolvimento (com hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Acesse a aplicação

· API: http://localhost:8000

· Swagger UI: http://localhost:8000/docs

· ReDoc: http://localhost:8000/redoc

· Health Check: http://localhost:8000/health

## 🔔 Endpoints da API

### Resumo dos Endpoints

| Método | Endpoint | Descrição | Status Codes |
|--------|----------|-----------|--------------|
| `GET` | `/health` | Verifica status da API | 200 |
| `POST` | `/notes/upload` | Upload de arquivo `.md` | 201, 400, 413 |
| `POST` | `/notes` | Cria nota via JSON | 201, 422 |
| `GET` | `/notes` | Lista todas as notas | 200 |
| `GET` | `/notes/{note_id}` | Obtém uma nota específica | 200, 404 |
| `PUT` | `/notes/{note_id}` | Atualiza uma nota | 200, 404 |
| `DELETE` | `/notes/{note_id}` | Remove uma nota | 200, 404 |
| `GET` | `/notes/{note_id}/html` | Renderiza nota em HTML | 200, 404 |
| `POST` | `/notes/check-grammar` | Verifica gramática de texto | 200, 422 |
