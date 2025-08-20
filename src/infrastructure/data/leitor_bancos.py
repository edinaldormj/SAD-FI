"""
Leitura de parâmetros de bancos a partir de CSV padronizado.
Colunas obrigatórias: nome,sistema,taxa_anual
Retorno: list[dict] com chaves 'nome','sistema','taxa_anual'.
"""
from __future__ import annotations
import csv
from typing import List, Dict

COLS_OBRIGATORIAS = ["nome", "sistema", "taxa_anual"]

def carregar_bancos_csv(caminho_csv: str) -> List[Dict]:
    bancos: List[Dict] = []
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        faltantes = [c for c in COLS_OBRIGATORIAS if c not in (reader.fieldnames or [])]
        if faltantes:
            raise ValueError(f"CSV inválido. Faltam colunas: {faltantes}")
        for row in reader:
            nome = (row.get("nome") or "").strip()
            sistema = (row.get("sistema") or "").strip().upper()
            taxa_raw = (row.get("taxa_anual") or "").strip().replace(",", ".")
            try:
                taxa_anual = float(taxa_raw)
            except Exception:
                raise ValueError(f"taxa_anual inválida para o banco '{nome}': {row.get('taxa_anual')}")
            if not nome or sistema not in {"SAC", "SAC_IPCA"}:
                raise ValueError(f"Linha inválida: {row}")
            bancos.append({"nome": nome, "sistema": sistema, "taxa_anual": taxa_anual})
    if not bancos:
        raise ValueError("Nenhum banco carregado do CSV.")
    return bancos
