import pytest
import re
from datetime import datetime
from core.mcp import MCPSystem, mcp_instance

class DummyDateTime:
    @classmethod
    def now(cls):
        return datetime(2025, 6, 20, 12, 0, 0)

@pytest.fixture(autouse=True)
def freeze_datetime(monkeypatch):
    # Freeze datetime.now() to a fixed timestamp
    monkeypatch.setattr('core.mcp.datetime', DummyDateTime)

def test_plan_default_and_strategies():
    mcp = MCPSystem(memory_size=10)
    # Default strategy
    plan = mcp.plan("Qualquer pergunta sem keywords.")
    assert plan['strategy'] == 'default'
    assert plan['enrichments'] == []
    assert 'timestamp' in plan and re.match(r"2025-06-20T12:00:00", plan['timestamp'])

    # Comparison strategy
    plan_cmp = mcp.plan("Me ajude a comparar A versus B")
    assert plan_cmp['strategy'] == 'comparison'
    assert 'buscar_multiplos_docs' in plan_cmp['enrichments']

    # Summarization strategy
    plan_sum = mcp.plan("Preciso resumir este texto")
    assert plan_sum['strategy'] == 'summarization'
    assert 'extrair_principais_pontos' in plan_sum['enrichments']

    # Extraction strategy
    plan_ext = mcp.plan("Mostre a cláusula ou artigo específico")
    assert plan_ext['strategy'] == 'extraction'
    assert 'buscar_trecho_especifico' in plan_ext['enrichments']

def test_memory_and_context_trimming():
    mcp = MCPSystem(memory_size=2)
    # No context initially
    assert mcp.get_context() == ""

    # Add interactions
    mcp.remember("Q1", "A1")
    mcp.remember("Q2", {"answer": "A2", "extra": 123})
    # Memory size limited to 2
    assert len(mcp.memory) == 2

    context = mcp.get_context(n=2)
    # Should include last two Q/R pairs
    assert "P: Q1" in context
    assert "R: A1" in context
    assert "P: Q2" in context
    assert "R: A2" in context

    # Test trimming of long question and answer
    long_q = "Q" * 300
    long_a = "A" * 600
    mcp.remember(long_q, long_a)
    entry = mcp.memory[-1]
    assert len(entry['question']) <= 200
    assert len(entry['answer']) <= 500

def test_enrich_question():
    mcp = MCPSystem(memory_size=5)
    # Without context
    assert mcp.enrich_question("Teste") == "Teste"
    # With context
    mcp.remember("Q1", "A1")
    enriched = mcp.enrich_question("Nova pergunta")
    assert enriched.startswith("Contexto anterior:")
    assert "Pergunta atual: Nova pergunta" in enriched

def test_get_serializable_memory():
    mcp = MCPSystem(memory_size=5)
    mcp.remember("Q1", "A1", metadata={"k1": "v1"})
    mcp.remember("Q2", "A2", metadata={"k2": 2, 3: "x"})
    serial = mcp.get_serializable_memory(last_n=2)
    assert isinstance(serial, list) and len(serial) == 2
    for item in serial:
        assert 'question' in item and isinstance(item['question'], str)
        assert 'answer' in item and isinstance(item['answer'], str)
        assert 'timestamp' in item
        # metadata should serialize only string keys
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in item['metadata'].items())

def test_global_singleton():
    # The global mcp_instance should be a MCPSystem with memory_size 50
    assert isinstance(mcp_instance, MCPSystem)
    # Should have deque attribute with maxlen 50
    assert hasattr(mcp_instance, 'memory') and mcp_instance.memory.maxlen == 50
