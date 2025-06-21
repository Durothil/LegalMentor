# ⚖️ LegalMentor

**LegalMentor** é um sistema inteligente de análise jurídica baseado em **RAG (Retrieval-Augmented Generation)**. Evolução direta do projeto *rag_juridico*, esta nova versão oferece uma base profissional para copilotos jurídicos com uso de IA generativa, integração com **Claude Sonnet 4**, embeddings contextuais, vetorização com **Pinecone** e futura compatibilidade com o protocolo **MCP da Anthropic**.

---

## 🚀 Objetivo

Desenvolver uma solução robusta para leitura, análise e resposta contextual de documentos jurídicos em linguagem natural, com foco em:

- Eficiência na consulta de contratos, pareceres, decisões e leis.
- Assistência jurídica automatizada via LLM.
- Arquitetura modular e escalável para futuros upgrades (LangGraph, multimodalidade, SaaS, etc).

---

## 📸 Exemplo do Sistema

![Layout do sistema](/frontend/assets/layout_sistema.png)

---

## 🌐 Demonstração em Vídeo do Rag Jurídico

🔗 [Veja o projeto em ação no LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7326319147112402945/)

---

## 🧠 Tecnologias Utilizadas

### Backend
- **Python 3.12+** (requerido)
- **FastAPI** – API REST para servir o pipeline RAG
- **Uvicorn** – Servidor ASGI para FastAPI
- **LangChain** – Cadeia RAG com rastreamento e ferramentas
- **Claude Sonnet 4 (Anthropic)** – LLM principal via API
- **Pinecone** – Vetorstore para embeddings jurídicos
- **MCP (Memory – Controller – Planner)** – arquitetura de agente com memória contextual, planejamento de fluxo e controle de conversação  

### Frontend
- **Streamlit** – Interface Web
- **Requests** – Cliente HTTP para comunicação com a API

### Processamento de Documentos
- **Docling** – Processamento semântico de PDFs acessíveis
- **Tesseract OCR** + **LayoutLMv2Processor** – OCR com bounding boxes e estruturação visual
- **HuggingFace Embeddings** (`multilingual-e5-large`) – Embeddings semânticos
- **Sentence-BERT (MiniLM)** – Agrupamento semântico de cláusulas
- **Regex jurídico** – Extração e separação de seções legais

### DevOps & Observabilidade
- **LangSmith** – Observabilidade e rastreamento da cadeia RAG
- **Docker + Docker Compose** – Empacotamento e execução reprodutível
- **Pytest** – Testes automatizados e verificação de versão mínima do Python
- **python-dotenv** – Gerenciamento de variáveis de ambiente

---

## 📁 Estrutura do Projeto

```
legalmentor/
│
├── backend/
│   └── api.py              # API FastAPI principal
│
├── core/                   # Núcleo compartilhado do sistema
│   ├── __init__.py
│   ├── config.py          # Configurações centralizadas
│   ├── layout_ocr.py      # OCR e processamento de layouts
│   ├── rag_pipeline.py    # Pipeline RAG principal
│   ├── setup_langsmith.py # Configuração do LangSmith
│   ├── mcp.py             # Configuração do MCP
│   └── utils.py           # Funções auxiliares
│
├── frontend/
│   ├── app.py             # Interface Streamlit
│   ├── assets/
│   │   └── layout_sistema.png
│   └── .streamlit/
│       ├── config.toml         # Configurações visuais do Streamlit
│       └── secrets.toml        # Segredos do frontend (criar do secrets.example.toml)
│
├── tests/                  # Testes automatizados
│   ├── test_pipeline.py
│   ├── test_python_version.py
│   └── test_utils.py
│
├── uploaded_docs/          # Pasta para PDFs enviados (criada automaticamente)
├── data/                   # Dados e índices (criada automaticamente)
├── .env                    # Variáveis de ambiente 
│
├── requirements.txt        # Dependências Python
├── setup.py               # Configuração do pacote
├── pytest.ini             # Configuração dos testes
├── README.md              # Este arquivo
├── LICENSE                # Licença MIT
├── .gitignore            # Arquivos ignorados pelo Git
│
├── Dockerfile             # Container Docker
├── docker-compose.yml     # Orquestração Docker
├── .dockerignore         # Arquivos ignorados no Docker
└── build_and_up.bat      # Script para rebuild Docker
```

---

## ▶️ Como Executar Localmente

### Pré-requisitos
- Python 3.12 ou superior
- Chaves de API (Anthropic, Pinecone, etc)

### 1. Clone o repositório e prepare o ambiente

```bash
git clone https://github.com/seu-usuario/legalmentor.git
cd legalmentor

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar o pacote em modo desenvolvimento
pip install -e .
```

### 2. Configure as variáveis de ambiente

O projeto usa dois arquivos de configuração:

#### Backend (.env na raiz):
```bash
# Criar arquivo .env na raiz do projeto
cp .env.example .env

# Editar com suas credenciais:
PINECONE_API_KEY=your-pinecone-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
LANGSMITH_API_KEY=your-langsmith-key
# ... outras variáveis
```

#### Frontend (secrets.toml):
```bash
# Criar arquivo secrets.toml no frontend
cp frontend/.streamlit/secrets.example.toml frontend/.streamlit/secrets.toml

# Editar com suas credenciais:
# As mesmas chaves do .env, mas em formato TOML
```

### 3. Execute o sistema

Você precisa rodar **dois serviços** em terminais separados:

#### Terminal 1 - Backend (API):
```bash
cd backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

O backend estará disponível em: http://localhost:8000
- Documentação da API: http://localhost:8000/docs

#### Terminal 2 - Frontend (Streamlit):
```bash
cd frontend
streamlit run app.py
```

O frontend estará disponível em: http://localhost:8501

---

## 🐳 Executar com Docker (recomendado)

Para garantir compatibilidade total e ambiente isolado, você pode rodar o LegalMentor via Docker:

### 1. Pré-requisitos

- Docker e Docker Compose instalados

### 2. Build e execução automática

Use o script:

```bash
./build_and_up.bat
```

Este comando:
- 🛑 Para containers antigos
- 🛠️ Recria a imagem com as alterações recentes
- 🚀 Sobe o container atualizado

### 3. Acessar a aplicação

Após subir, acesse no navegador:

```
http://localhost:8501
```

### 4. Estrutura de secrets

Você pode copiar o arquivo de exemplo para configurar suas variáveis:

```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

Edite com suas credenciais:

```toml
GROQ_API_KEY = "your-groq-api-key"
PINECONE_API_KEY = "your-pinecone-api-key"
ANTHROPIC_API_KEY = "your-anthropic-api-key"

LANGSMITH_TRACING = "true"
LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
LANGSMITH_API_KEY = "your-langsmith-key"
LANGSMITH_PROJECT = "LegalMentor"
...
```

---

## 🧪 Testes dentro do container

Para rodar os testes direto no container:

```bash
docker exec -it legalmentor-container pytest
```

## 🧪 Testes Automatizados

Executar com:
```bash
pytest tests/
```

Os testes cobrem:
- Cálculo de tokens e sanitização de metadados
- Indexação vetorial e consulta contextual
- Erros controlados e fallback seguro

---

## ✅ Funcionalidades Implementadas

- [x] Upload de PDFs jurídicos  
- [x] Extração semântica com Docling  
- [x] Fallback com OCR avançado (LayoutLMv2 + Tesseract)  
- [x] Separação jurídica via regex (CLÁUSULAS, ARTs, §§)  
- [x] Agrupamento semântico adaptativo (Sentence-BERT)  
- [x] Geração de embeddings contextuais (E5)  
- [x] Indexação com Pinecone  
- [x] Consulta jurídica com LLM (Anthropic + Claude Sonnet 4)  
- [x] Sanitização de metadados compatível com Pinecone  
- [x] Testes automatizados com Pytest  
- [x] Telemetria com LangSmith:
  - [x] Cadeia RAG completa rastreada
  - [x] Tokenização, tempo de resposta e custo estimado
  - [x] Instrumentação das etapas (OCR, Embeddings, etc.)

Etapas pendentes:
- [ ] Salvar os chunks evitar reprocessar o mesmo documento 2 ou 3 vezes se ele for enviado repetidamente.
- [ ] Redução de Chunks Curtos - Documentos OCR podem gerar muitos trechos curtos com baixo valor semântico. Será necessário implementar uma lógica de fusão (ex: unir ao chunk anterior) para garantir embeddings mais ricos e melhorar a recuperação no RAG.
---

## 🧠 Roadmap de Evolução

### 📌 Etapa Atual:
- ✅ Pinecone em vez de FAISS  
- ✅ Substituir Groq por Claude Sonnet 4  
- ✅ OCR com LayoutLMv2 + regex jurídica + agrupamento semântico  
- ✅ Dockerizar 
- ✅ Simulação de MCP-like com LangChain (Planner, Controller, Memory)  

### 🔜 Etapas Futuras:

#### 0. Fundamentos de Engenharia
- Automação de testes → TDD (pytest, cobertura ≥ 80 %)
- SOLID & Design Patterns (interfaces para LLM, VectorStore; fábricas, inversão de dependência)
- CI ( GitHub Actions rodando lint + testes a cada PR )

#### 1. Deploy Cloud mínimo
- Container Docker (FastAPI + Streamlit)
- Publicação em AWS SageMaker ou Vertex AI
- Logs + métricas básicas; autoscaling do endpoint

#### 3. Enriquecimento de contexto (Re-ranking)
- Integrar Cohere ReRank ou bge-reranker
- Filtros semânticos por seção jurídica (cláusula, artigo, título)

#### 4. Feedback Loop + Auto-avaliação
- Endpoint /feedback gravando 👍/👎 e comentários
- Script offline de avaliação com LLM (estilo RHF)
- Ajuste automático de prompts/re-rank com base nos dados

#### 5. MLOps / Versionamento
- MLflow para rastrear execuções de embeddings / LLM
- DVC (ou Weights & Biases Artifacts) para versionar índices Pinecone e modelos fine-tuned
- Pipeline CI/CD separada para (i) imagem de inferência e (ii) imagem de treinamento/atualização de índice

#### 6. Evolução para LangGraph
- Converter pipeline em grafo (nós: Retrieval, Re-rank, LLM, Feedback)
- Suportar loops de validação e retries
- Permitir múltiplos fluxos autônomos e persistência de estado

#### 7. Microsserviços & API Gateway
- Quebrar OCR, RAG, Re-ranker, Memory em serviços FastAPI independentes
- GraphQL na borda para compor respostas e evitar múltiplas chamadas REST

#### 8. SaaS Multi-tenant
- Sessões, histórico, preferências, permissões por usuário
- Dashboards de uso / billing

#### 9. Multimodalidade
- Áudio (Whisper)
- Imagem (LayoutLM)
- Triggers por e-mail / geração de minutas etc.

#### 10. Orquestração Kubernetes
- Helm chart, Horizontal Pod Autoscaler
- Observabilidade (Prometheus/Grafana)
- Deploys zero-downtime e resiliência para alta demanda

---

## Observações 

#### Sobre Arquitetura de Agente
- **MCP (Memory – Controller – Planner)**  
  - **Memory:** mantém o contexto das últimas interações  
  - **Planner:** decide a estratégia (comparação, extração, sumarização…)  
  - **Controller:** enriquece a pergunta com contexto antes de enviar ao RAG  

#### Sobre o uso do LayoutLM

Atualmente, a aplicação utiliza uma abordagem leve e eficiente para estruturar documentos jurídicos digitalizados, composta por:

- 🧠 OCR com bounding boxes via pytesseract.
- 🧱 Estruturação visual com LayoutLMv2Processor (sem inferência com o modelo completo).
- ⚖️ Separação por cláusulas jurídicas usando regex.
- 🧬 Agrupamento semântico com Sentence-BERT (MiniLM).
- ✂️ Divisão inteligente por limite de tokens compatível com o modelo E5.

Essa estratégia cobre aproximadamente 80% dos casos reais de uso com documentos jurídicos escaneados, aliando desempenho e robustez.

##### Futuras melhorias:

Está nos planos evoluir essa estrutura para utilizar LayoutLMv2 ou LayoutLMv3 com inferência completa, o que permitirá:

- ✅ Maior precisão na compreensão visual de documentos complexos (ex: colunas, campos desalinhados).
- ✅ Aplicação de NER jurídico (Reconhecimento de Entidades) com extração automática de informações como cláusulas, datas, valores e partes do contrato.
- ✅ Possibilidade de fine-tuning para tarefas jurídicas específicas.

Essa evolução exigirá mais recursos computacionais (como GPU), mas trará ganhos significativos para casos de uso que demandam alta acurácia e extração inteligente de dados estruturados.

---

## 👨‍💼 Desenvolvido por

**Mewerton de Melo Silva**  
🔗 [LinkedIn](https://www.linkedin.com/in/mewerton/)

---

## 📄 Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.
