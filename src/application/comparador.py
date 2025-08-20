"""
Comparador de múltiplos resultados de simulação.
Entrada: dict[str, SimulacaoResultado-like] com atributo `total_pago`.
Saída: ranking list[(nome_banco, total_pago)] crescente e recomendação textual.
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional

def comparar_varios(resultados: Dict[str, object]) -> List[Tuple[str, float]]:
    pares: List[Tuple[str, float]] = []
    for nome, obj in resultados.items():
        total = getattr(obj, "total_pago", None)
        if total is None:
            raise AttributeError(f"Objeto resultado de '{nome}' não possui 'total_pago'.")
        pares.append((nome, float(total)))
    pares.sort(key=lambda t: t[1])
    return pares

def recomendar(ranking: List[Tuple[str, float]], modalidades: Optional[Dict[str, str]] = None) -> str:
    if not ranking:
        return "Recomendação: não há resultados para comparar."
    banco_top, _ = ranking[0]
    if modalidades and banco_top in modalidades:
        return f"Recomendação: {banco_top} – {modalidades[banco_top]} com menor custo total."
    return f"Recomendação: {banco_top} com menor custo total."
