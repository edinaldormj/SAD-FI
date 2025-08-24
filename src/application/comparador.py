"""
comparador.py

Comparador de múltiplos resultados de simulação.

Contratos:
- Entrada de comparar_varios: dict[str, resultado_like]
  onde resultado_like expõe `total_pago` como atributo ou como chave em dict.
- Saída de comparar_varios: List[Tuple[str, float]] (rótulo, total_pago) ordenada por custo crescente.
  Em caso de empate no total_pago, ordena por rótulo para garantir estabilidade.
- recomendar recebe ranking (retorno de comparar_varios) e um mapeamento opcional
  `modalidades: Dict[str, str]` para formatar a recomendação com a modalidade do rótulo.
- recomendar também aceita parâmetro `tol` (tolerância absoluta) para considerar empates técnicos.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

def inferir_modalidade(rotulo: str) -> str:
    """
    Retorna a modalidade a partir do rótulo:
      - contém 'IPCA' -> 'SAC IPCA+'
      - contém 'TR'   -> 'SAC TR'
      - caso contrário -> 'SAC'
    """
    up = rotulo.upper()
    if "IPCA" in up:
        return "SAC IPCA+"
    if "TR" in up:
        return "SAC TR"
    return "SAC"


def mapear_modalidades(rotulos: List[str]) -> Dict[str, str]:
    return {r: inferir_modalidade(r) for r in rotulos}


def comparar_varios(resultados: Dict[str, Any]) -> List[Tuple[str, float]]:
    """
    Converte o dicionário de resultados em uma lista ordenada por total_pago (crescente).

    Aceita:
      - objetos com atributo `.total_pago`
      - dicionários com chave 'total_pago'

    Lança:
      - ValueError se não for possível extrair total_pago de algum resultado.

    Ordenação:
      - (total_pago, rotulo) para garantir estabilidade em empates.
    """
    pares: List[Tuple[str, float]] = []
    for nome, obj in resultados.items():
        # Tentativa robusta: atributo primeiro, depois chave em dict
        total = None
        try:
            total = getattr(obj, "total_pago")
        except Exception:
            total = None

        if total is None and isinstance(obj, dict):
            total = obj.get("total_pago")

        if total is None:
            # Mensagem clara para o usuário/dev: contrato de objeto inválido
            raise ValueError(f"Objeto resultado de '{nome}' não possui 'total_pago' (atributo ou chave).")

        try:
            total_f = float(total)
        except Exception as e:
            raise ValueError(f"Não foi possível converter total_pago do resultado '{nome}' para float: {e}")

        pares.append((nome, total_f))

    # Ordena por total_pago ascendente e, em caso de empate, por rótulo (estabilidade)
    pares.sort(key=lambda t: (t[1], t[0]))
    return pares


def recomendar(
    ranking: List[Tuple[str, float]],
    modalidades: Optional[Dict[str, str]] = None,
    tol: float = 1e-6
) -> str:
    """
    Gera mensagem de recomendação a partir do ranking.

    Regras:
      - Se ranking vazio -> mensagem informativa.
      - Se apenas um item -> retorna recomendação para ele (inclui modalidade se fornecida).
      - Se há empate técnico (diferença absoluta <= tol entre o menor e outros), retorna mensagem
        de empate técnico listando os empatados (limitado a 3 para legibilidade).
      - Caso contrário -> retorna recomendação com o vencedor (inclui modalidade se disponível).

    Parâmetros:
      - ranking: lista de (rotulo, total_pago) ordenada ascendentemente (retorno de comparar_varios).
      - modalidades: opcional, mapeia rotulo -> string com o nome da modalidade (ex.: "SAC IPCA+").
      - tol: tolerância absoluta para considerar empate técnico.
    """
    if not ranking:
        return "Recomendação: não há resultados para comparar."

    # único candidato: recomendo direto (com modalidade se disponível)
    if len(ranking) == 1:
        rotulo, _ = ranking[0]
        if modalidades and rotulo in modalidades:
            return f"Recomendação: {rotulo} – {modalidades[rotulo]} com menor custo total."
        return f"Recomendação: {rotulo} com menor custo total."

    # menor total
    vencedor, menor_total = ranking[0]

    # coleta todos os rótulos cujo total está dentro da tolerância do menor
    empatados = [rot for rot, total in ranking if abs(total - menor_total) <= tol]

    if len(empatados) > 1:
        # Mensagem de empate técnico — lista curta para legibilidade
        lista = ", ".join(empatados[:3])
        if len(empatados) > 3:
            lista += f", e mais {len(empatados) - 3}..."
        return f"Empate técnico entre: {lista}. Considere regras adicionais (taxas/serviços) para desempate."

    # único vencedor (sem empate técnico)
    if modalidades and vencedor in modalidades:
        return f"Recomendação: {vencedor} – {modalidades[vencedor]} com menor custo total."
    return f"Recomendação: {vencedor} com menor custo total."
