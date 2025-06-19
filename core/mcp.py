# core/mcp.py
"""
MCP Minimalista - Memory, Controller, Planner em um arquivo
"""
from typing import Dict, List, Optional, Any
from collections import deque
import json
from datetime import datetime

class MCPSystem:
    """Sistema MCP completo e simples"""
    
    def __init__(self, memory_size: int = 50):  # Aumentado de 20 para 50
        # Memory: guarda contexto
        self.memory = deque(maxlen=memory_size)
        
    def plan(self, question: str) -> Dict[str, Any]:
        """Planner: analisa a pergunta e cria estratégia"""
        q_lower = question.lower()
        
        plan = {
            "strategy": "default",
            "enrichments": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Estratégias baseadas no tipo de pergunta
        if any(word in q_lower for word in ["comparar", "versus", "diferença"]):
            plan["strategy"] = "comparison"
            plan["enrichments"].append("buscar_multiplos_docs")
            
        elif any(word in q_lower for word in ["resumir", "resumo", "sintetizar"]):
            plan["strategy"] = "summarization"
            plan["enrichments"].append("extrair_principais_pontos")
            
        elif any(word in q_lower for word in ["cláusula", "artigo", "seção"]):
            plan["strategy"] = "extraction"
            plan["enrichments"].append("buscar_trecho_especifico")
            
        return plan
    
    def remember(self, question: str, answer: str, metadata: Dict = None):
        """Memory: salva interação"""
        # Garantir que answer é serializável
        if isinstance(answer, dict):
            answer = answer.get("answer", str(answer))
        else:
            answer = str(answer)[:500]  # Limita tamanho
            
        self.memory.append({
            "question": question[:200],  # Limita tamanho
            "answer": answer,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def get_context(self, n: int = 3) -> str:
        """Memory: recupera contexto relevante"""
        if not self.memory:
            return ""
        
        # Pega últimas N interações
        recent = list(self.memory)[-n:]
        
        context_parts = []
        for item in recent:
            context_parts.append(f"P: {item['question'][:100]}...")
            context_parts.append(f"R: {item['answer'][:100]}...")
        
        return "\n".join(context_parts)
    
    def enrich_question(self, question: str) -> str:
        """Controller: enriquece pergunta com contexto"""
        context = self.get_context()
        
        if context:
            return f"""Contexto anterior:
{context}

Pergunta atual: {question}"""
        
        return question
    
    def get_serializable_memory(self, last_n: int = 5) -> List[Dict]:
        """Retorna memória em formato serializável para JSON"""
        recent = list(self.memory)[-last_n:]
        
        # Garantir que tudo é serializável
        safe_memory = []
        for item in recent:
            safe_item = {
                "question": str(item.get("question", ""))[:200],
                "answer": str(item.get("answer", ""))[:200],
                "timestamp": item.get("timestamp", ""),
                "metadata": {
                    k: str(v) for k, v in item.get("metadata", {}).items()
                    if isinstance(k, str)
                }
            }
            safe_memory.append(safe_item)
            
        return safe_memory

# Instância global (singleton simples)
mcp_instance = MCPSystem(memory_size=50)  # Aumentado para 50