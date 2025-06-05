
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

![Layout do sistema](assets/layout_sistema.png)

---

## 🌐 Demonstração em Vídeo do Rag Jurídico

🔗 [Veja o projeto em ação no LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7326319147112402945/)

---

## 🧠 Tecnologias Utilizadas

- **Python 3.10+**
- **Streamlit** (Interface)
- **LangChain** (Orquestração RAG)
- **Claude Sonnet 4** (via API da Anthropic)
- **Pinecone** (Vectorstore vetorial com embeddings integrados)
- **Docling** (Processamento semântico de PDFs)
- **HuggingFace Embeddings** (`multilingual-e5-large`)
- **Pytest** (testes automatizados)

---

## 📁 Estrutura do Projeto

```
legalmentor/
│
├── config.py             # 
├── layout_ocr.py         # 
├── app.py                # Interface principal (Streamlit)
├── rag_pipeline.py       # Pipeline RAG com vetorização e cadeia de resposta
├── utils.py              # Funções auxiliares (metadados, logs, sanitização)
├── requirements.txt      # Bibliotecas e versões
├── README.md             # Documentação principal
├── setup_langsmith.py    # 
├── LICENSE               # 
│
├── assets/
│   └── layout_sistema.png
│
├── .streamlit/
│   ├── secrets.toml      # Configurações de API (Claude, Pinecone)
│   └── config.toml       # Configs de tema/execução
│
├── data/
│   ├── documentos/       # PDFs e arquivos enviados
│   └── indexes/          # Índices locais (caso FAISS seja usado em testes)
│
├── tests/
│   ├── test_pipeline.py  # Testes de fluxo principal
│   └── test_utils.py     # Testes de funções auxiliares
```

---

## ▶️ Como Executar Localmente

1. Crie e ative o ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute o sistema:
```bash
streamlit run app.py
```

---

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
- 🚧 Dockerizar 
- 🚧 Simulação de MCP-like com LangChain (Planner, Controller, Memory)  

### 🔜 Etapas Futuras:

#### 1. Dockerizar 
- Garantir reprodutibilidade, portabilidade e isolar dependências.
- Docker te dá uma base estável, local e no CI/CD.
- Também é um pré-requisito para rodar localmente o mesmo código que irá para SageMaker.

#### 2. Deploy no AWS SageMaker com Streamlit ou FastAPI
- Testar o projeto na nuvem, sob demanda, com escalabilidade.
- Com o container pronto, o deploy no SageMaker é direto.
- medir desempenho real (OCR, embeddings, consulta), adiciona observabilidade operacional e de custo, essencial para produção real.
- configurar Auto Scaling, monitoramento, etc.
- MVP rodando em ambiente de produção cloud.

#### 3. Aplicar arquitetura MCP-like (Memory, Controller, Planner)
- Modularizar a inteligência do agente e preparar para evoluir para LangGraph.
- Transforma o pipeline RAG em um agente inteligente.
- Separa o controle de fluxo (Controller), decisões (Planner) e memória (Memory).
- Passa a entender o que fazer (ex: “gerar resposta”, “buscar cláusulas”, “resumir”), não só responder.

#### 3.5. Integração com APIs e Microsserviços
- REST para microsserviços individuais
- Implementar REST APIs para cada módulo do MCP (Planner, Controller, Memory), garantindo isolamento, versionamento e testes independentes.
- Criar serviços REST para módulos essenciais: OCR, RAG, Reranker, Feedback, Sessões de usuário, etc.

- GraphQL como API gateway
- Adicionar GraphQL como camada de orquestração, permitindo consultas agregadas entre múltiplos microsserviços.
- Facilitar otimização de consultas, evitando múltiplas chamadas REST quando o frontend precisar compor respostas (exemplo: plano + histórico + resposta em uma única query).

#### 4. Evoluir para LangGraph
- Com o MCP modularizado, posso criar fluxos complexos e autônomos.
- LangGraph permite múltiplos nós, ciclos, dependências entre etapas (ex: “buscar → validar → executar ferramenta → gerar explicação final”).
- Ideal para construir agentes reais, com persistência e automação de tarefas.
- Agente jurídico inteligente, com múltiplos comportamentos e decisões encadeadas.

#### 5. Enriquecimento de contexto com reranking
- Re-ranking via Cohere ou bge-reranker
- Filtros semânticos por seção legal (cláusula, título, artigo)

#### 6. Autoavaliação e feedback loop
- Modelo avalia qualidade das respostas
- Ajuste dinâmico com RHF-like

#### 7. SaaS Multiusuário
- Sessões independentes por usuário
- Histórico, preferências e permissões
- Dashboards de uso e relatórios

#### 8. Multimodalidade
- Leitura de contratos escaneados (OCR)  (já entregue)
- Upload de áudio jurídico para transcrição
- Integrações com automações (e-mails, geração de minutas, etc.)

#### 9. Orquestração com Kubernetes
- Containerizar todos os microsserviços e configurar seus deployments
- Usar Kubernetes para escalabilidade, balanceamento de carga, observabilidade e tolerância a falhas
- Ideal para ambientes de produção com múltiplos usuários simultâneos e workloads variáveis

---

## 👨‍💼 Desenvolvido por

**Mewerton de Melo Silva**  
🔗 [LinkedIn](https://www.linkedin.com/in/mewerton/)

---

## 📄 Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.
