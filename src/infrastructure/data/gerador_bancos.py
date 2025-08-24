# -*- coding: utf-8 -*-
"""
Geração de dados/dados/bancos.csv

- REAL (por banco) via Olinda/BCB -> serviço taxaJuros v2 (OData):
  Usa o coletor `ColetorTxJuros` para obter as taxas por instituição nas modalidades:
    * SAC      -> pré-fixado (903101 mercado / 905101 reguladas)
    * SAC_TR   -> pós-fixado TR (903201 mercado / 905201 reguladas)
    * SAC_IPCA -> pós-fixado IPCA (903203 mercado / 905203 reguladas)
  Saída: CSV com colunas 'nome,sistema,taxa_anual' (taxa em fração a.a.)

- FAKE (fallback) -> mantém o gerador simples anterior.

Obs:
  * Se a modalidade escolhida não retornar dados (ex.: mercado), o gerador tenta
    automaticamente a alternativa (reguladas) para aquela modalidade.
  * Se nada vier da API, cai num fallback “realista” de nomes + taxas padrão.
"""

from __future__ import annotations
from typing import Dict, Iterable, List, Optional, Tuple
from dataclasses import dataclass
import os
import sys
import math
import unicodedata
import re
from pathlib import Path
from datetime import date, timedelta

import pandas as pd

# ---- compat quando executado diretamente (python src/.../gerador_bancos.py) ----
try:
    from .leitor_bancos import SISTEMAS_VALIDOS
except ImportError:  # sem pacote (executado direto)
    sys.path.insert(0, str(Path(__file__).resolve()).split('src')[0] + 'src')
    from infrastructure.data.leitor_bancos import SISTEMAS_VALIDOS  # type: ignore

# coletor oficial de taxas
try:
    from .coletor_txjuros import ColetorTxJuros
except ImportError:
    # idem compat
    from infrastructure.data.coletor_txjuros import ColetorTxJuros  # type: ignore


# -------------------------- Fallbacks e defaults -------------------------- #

DEFAULT_BANCOS_FAKE = [
    {"nome": "Banco Alfa", "sistema": "SAC",      "taxa_anual": 0.115},
    {"nome": "Banco Beta", "sistema": "SAC_IPCA", "taxa_anual": 0.085},
    {"nome": "Banco Gama", "sistema": "SAC_TR",   "taxa_anual": 0.105},
]

DEFAULT_TAXAS_REAL = {
    "SAC":      0.115,  # fração a.a.
    "SAC_IPCA": 0.085,
    "SAC_TR":   0.105,
}

REAL_NAMES_FALLBACK = [
    "BANCO DO BRASIL S.A.",
    "CAIXA ECONÔMICA FEDERAL",
    "ITAÚ UNIBANCO S.A.",
    "BANCO BRADESCO S.A.",
    "BANCO SANTANDER (BRASIL) S.A.",
    "BANCO SAFRA S.A.",
    "BANCO INTER S.A.",
    "BANCO BTG PACTUAL S.A.",
    "BANCO ORIGINAL S.A.",
    "BANCO VOTORANTIM S.A.",
]

# ----------------------------- Utils locais ------------------------------ #

def _normalize_name(s: str) -> str:
    """Upper, sem acento, collapse espaços e pontuação redundante."""
    if not isinstance(s, str):
        s = str(s or "")
    s = s.strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^\w\s\.\-&/()]", " ", s)   # mantém ., -, &, /, ()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _last_closed_month_yyyy_mm() -> str:
    today = date.today().replace(day=1)
    end_prev = (today - timedelta(days=1))
    return f"{end_prev.year:04d}-{end_prev.month:02d}"


def _carregar_txjuros_csv_local(path_csv: str) -> pd.DataFrame:
    import pandas as pd, io
    df = pd.read_csv(path_csv)
    cols = [c.strip() for c in df.columns]
    # heurísticas de cabeçalho (o relatório pode vir com nomes diferentes)
    def _pick(*alts):
        for a in alts:
            for c in cols:
                if a.lower() in c.lower():
                    return c
        return None
    k_inst = _pick("Instituicao", "Instituição", "InstituicaoFinanceira", "Nome")
    k_ano  = _pick("TaxaJurosAoAno", "ao ano", "ano")
    if not k_inst or not k_ano:
        raise ValueError(f"CSV {path_csv} não tem colunas reconhecíveis; cabeçalhos: {cols}")
    out = pd.DataFrame({
        "instituicao": df[k_inst].astype(str).str.strip(),
        "taxa_anual": pd.to_numeric(
            df[k_ano].astype(str).str.replace(",", ".", regex=False), errors="coerce"
        )
    }).dropna(subset=["taxa_anual"]).reset_index(drop=True)
    # converte % → fração se necessário
    med = out["taxa_anual"].abs().median()
    if med is not None and med > 1.0:
        out["taxa_anual"] = out["taxa_anual"] / 100.0
    return out

def validar_bancos(linhas: List[Dict]) -> None:
    if not linhas:
        raise ValueError("Lista de bancos vazia.")
    df = pd.DataFrame(linhas)
    for col in ["nome", "sistema", "taxa_anual"]:
        if col not in df.columns:
            raise KeyError(f"Coluna obrigatória ausente: {col}")
    invalidos = set(df["sistema"].astype(str).str.upper()) - set(SISTEMAS_VALIDOS)
    if invalidos:
        raise ValueError(f"Sistemas inválidos: {sorted(invalidos)}")
    

# ---------------------- Coleta de taxas por modalidade -------------------- #

@dataclass
class MapeamentoModalidade:
    sistemas: Tuple[str, ...]                   # ("SAC", "SAC_TR", "SAC_IPCA")
    codigos_mercado: Dict[str, int]             # por sistema → código
    codigos_reguladas: Dict[str, int]           # idem

MAPA = MapeamentoModalidade(
    sistemas=("SAC", "SAC_TR", "SAC_IPCA"),
    codigos_mercado={
        "SAC": 903101,      # PF - Imob. - Pré - Mercado
        "SAC_TR": 903201,   # PF - Imob. - Pós TR - Mercado
        "SAC_IPCA": 903203, # PF - Imob. - Pós IPCA - Mercado
    },
    codigos_reguladas={
        "SAC": 905101,      # PF - Imob. - Pré - Reguladas
        "SAC_TR": 905201,   # PF - Imob. - Pós TR - Reguladas
        "SAC_IPCA": 905203, # PF - Imob. - Pós IPCA - Reguladas
    },
)

def _coletar_taxas_por_sistema(
    coletor: ColetorTxJuros,
    sistema: str,
    prefer: str,         # "mercado" | "reguladas"
    tipo: str,           # "mensal" | "diario"
    mes: Optional[str],  # YYYY-MM (mensal)
    inicio: Optional[str], # YYYY-MM-DD (diario)
    segmento: int = 1,   # 1 = PF
) -> pd.DataFrame:
    """
    Tenta coletar taxas para um sistema (SAC, SAC_TR, SAC_IPCA) usando o código preferido;
    se vier vazio, tenta a alternativa. Retorna DF com colunas ['instituicao','taxa_anual'].
    """
    assert tipo in ("mensal", "diario")
    cod_pref = (MAPA.codigos_mercado if prefer == "mercado" else MAPA.codigos_reguladas)[sistema]
    cod_alt  = (MAPA.codigos_reguladas if prefer == "mercado" else MAPA.codigos_mercado)[sistema]

    def _harmonizar(df) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(columns=["instituicao", "taxa_anual"])
        out = df[["instituicao", "taxa_anual"]].copy()
        out = out.dropna(subset=["instituicao", "taxa_anual"])
        # colapsa duplicatas por instituição: usa a menor taxa do período
        out["_k"] = out["instituicao"].map(_normalize_name)
        out = (out.groupby("_k", as_index=False)
                  .agg(taxa_anual=("taxa_anual", "min"),
                       instituicao=("instituicao", "first")))
        return out[["instituicao", "taxa_anual"]].reset_index(drop=True)

    # 1) preferido
    if tipo == "mensal":
        mes = mes or _last_closed_month_yyyy_mm()
        r = coletor.coletar_mensal(mes=mes, codigo_modalidade=cod_pref, codigo_segmento=segmento)
        df = _harmonizar(r.df)
    else:
        if not inicio:
            # padrão: primeiro dia do mês fechado
            m = _last_closed_month_yyyy_mm()
            inicio = f"{m}-01"
        r = coletor.coletar_diaria_por_inicio(inicio_periodo=inicio, codigo_modalidade=cod_pref, codigo_segmento=segmento)
        df = _harmonizar(r.df)

    if df.empty:
        # 2) alternativa
        if tipo == "mensal":
            r2 = coletor.coletar_mensal(mes=mes or _last_closed_month_yyyy_mm(), codigo_modalidade=cod_alt, codigo_segmento=segmento)
            df = _harmonizar(r2.df)
        else:
            r2 = coletor.coletar_diaria_por_inicio(inicio_periodo=inicio, codigo_modalidade=cod_alt, codigo_segmento=segmento)
            df = _harmonizar(r2.df)

    return df

# ---------------------------- Geração REAL -------------------------------- #

def gerar_bancos_csv_real(
    destino_csv: str,
    *,
    tipo: str = "mensal",             # "mensal" | "diario"
    mes: Optional[str] = None,        # YYYY-MM   (para tipo="mensal")
    inicio: Optional[str] = None,     # YYYY-MM-DD (para tipo="diario")
    prefer: str = "mercado",          # "mercado" | "reguladas" | "ambos"   <- atualizei
    top_n_bancos: Optional[int] = None,
    modalidades: Iterable[str] = ("SAC", "SAC_TR", "SAC_IPCA"),
    on_error: str = "fallback",       # "fallback" | "raise"
    verbose: bool = True,
    offline_csv: dict | None = None,
) -> str:
    """
    Gera `bancos.csv` com **taxas reais por banco** (fração a.a.) vindas do BCB.

    Estratégia:
      - Se `offline_csv` for informado, carrega CSVs exportados do ReportTxJuros
        (chaves: {"pre": ..., "tr": ..., "ipca": ...}) e gera o arquivo.
      - Caso contrário, coleta na Olinda (taxaJuros v2) para cada modalidade.
        `prefer` pode ser "mercado", "reguladas" ou "ambos" (une as duas e usa a **menor** taxa por banco).
      - Remove duplicatas por instituição (normalizando nome) e ordena alfabeticamente.
    """
    try:
        if prefer not in {"mercado", "reguladas", "ambos"}:
            raise ValueError(f"prefer inválido: {prefer!r}")

        linhas: List[Dict] = []
        stats: Dict[str, Dict[str, int]] = {}

        # ---- (A) OFFLINE PRIMEIRO (se informado) -----------------
        if offline_csv:
            mapa = {
                "SAC":      offline_csv.get("pre"),   # ex.: dados/txjuros/2025-07_pre.csv
                "SAC_TR":   offline_csv.get("tr"),    # ex.: dados/txjuros/2025-07_tr.csv
                "SAC_IPCA": offline_csv.get("ipca"),  # ex.: dados/txjuros/2025-07_ipca.csv
            }
            for sistema in modalidades:
                p = mapa.get(sistema.upper())
                if not p:
                    if verbose:
                        print(f"[offline] sem arquivo para {sistema}")
                    continue
                try:
                    df = _carregar_txjuros_csv_local(p)
                except FileNotFoundError:
                    if verbose:
                        print(f"[offline] arquivo não encontrado: {p}")
                    continue
                df = df.sort_values("instituicao")
                if top_n_bancos:
                    df = df.head(int(top_n_bancos))
                for _, row in df.iterrows():
                    linhas.append({
                        "nome": str(row["instituicao"]).strip(),
                        "sistema": sistema,
                        "taxa_anual": float(row["taxa_anual"]),
                    })
            if linhas:
                validar_bancos(linhas)
                os.makedirs(os.path.dirname(destino_csv), exist_ok=True)
                pd.DataFrame(linhas).to_csv(destino_csv, index=False, encoding="utf-8")
                if verbose:
                    print("✓ bancos.csv gerado via OFFLINE CSV (ReportTxJuros export).")
                return destino_csv

        # ---- (B) ONLINE (Olinda) ---------------------------------
        coletor = ColetorTxJuros()

        def _coleta(sistema: str, tipo_local: str) -> pd.DataFrame:
            if prefer == "ambos":
                df_merc = _coletar_taxas_por_sistema(coletor, sistema, "mercado",  tipo_local, mes, inicio, 1)
                df_reg  = _coletar_taxas_por_sistema(coletor, sistema, "reguladas",tipo_local, mes, inicio, 1)
                df = pd.concat([df_merc, df_reg], ignore_index=True)
                if not df.empty:
                    df["_k"] = df["instituicao"].map(_normalize_name)
                    df = (df.groupby("_k", as_index=False)
                            .agg(taxa_anual=("taxa_anual","min"),
                                 instituicao=("instituicao","first")))
                    df = df.drop(columns=["_k"])
                stats.setdefault(sistema, {})[f"{tipo_local}_mercado"]   = len(df_merc)
                stats.setdefault(sistema, {})[f"{tipo_local}_reguladas"] = len(df_reg)
                stats.setdefault(sistema, {})[f"{tipo_local}_unidos"]    = len(df)
                return df
            else:
                df1 = _coletar_taxas_por_sistema(coletor, sistema, prefer, tipo_local, mes, inicio, 1)
                stats.setdefault(sistema, {})[f"{tipo_local}_{prefer}"] = len(df1)
                return df1

        # alvo padrão de mês/início
        if tipo == "mensal" and not mes:
            mes = _last_closed_month_yyyy_mm()
        if tipo == "diario" and not inicio:
            m = mes or _last_closed_month_yyyy_mm()
            inicio = f"{m}-01"

        for sistema in modalidades:
            sis = sistema.upper()
            if sis not in MAPA.sistemas:
                raise ValueError(f"Sistema '{sistema}' não suportado.")
            df = _coleta(sis, tipo)
            if df.empty and tipo == "mensal":
                # fallback: diário do mesmo mês
                df = _coleta(sis, "diario")
            if df.empty:
                continue
            df = df.sort_values("instituicao")
            if top_n_bancos:
                df = df.head(int(top_n_bancos))
            for _, row in df.iterrows():
                linhas.append({
                    "nome": str(row["instituicao"]).strip(),
                    "sistema": sis,
                    "taxa_anual": float(row["taxa_anual"]),
                })

        if verbose:
            print("🧪 Coleta por modalidade (linhas):")
            for sis in modalidades:
                d = stats.get(sis.upper(), {})
                parts = ", ".join(f"{k}={v}" for k, v in d.items()) if d else "0"
                print(f"  - {sis}: {parts}")

        if not linhas:
            if on_error == "raise":
                raise RuntimeError("taxaJuros/Olinda não retornou dados (mensal e diário).")
            if verbose:
                print("⚠️  Fallback acionado: nomes padrão + taxas base.")
            for nome in REAL_NAMES_FALLBACK[: (top_n_bancos or len(REAL_NAMES_FALLBACK))]:
                for sis in modalidades:
                    linhas.append({
                        "nome": nome,
                        "sistema": sis,
                        "taxa_anual": float(DEFAULT_TAXAS_REAL.get(sis, 0.10)),
                    })

        validar_bancos(linhas)
        os.makedirs(os.path.dirname(destino_csv), exist_ok=True)
        pd.DataFrame(linhas).to_csv(destino_csv, index=False, encoding="utf-8")
        return destino_csv

    except Exception:
        if on_error == "raise":
            raise
        if verbose:
            print("⚠️  Exceção durante a coleta. Fallback acionado.")
        linhas = []
        for nome in REAL_NAMES_FALLBACK[: (top_n_bancos or len(REAL_NAMES_FALLBACK))]:
            for sis in modalidades:
                linhas.append({
                    "nome": nome,
                    "sistema": sis,
                    "taxa_anual": float(DEFAULT_TAXAS_REAL.get(sis, 0.10)),
                })
        validar_bancos(linhas)
        os.makedirs(os.path.dirname(destino_csv), exist_ok=True)
        pd.DataFrame(linhas).to_csv(destino_csv, index=False, encoding="utf-8")
        return destino_csv


# ----------------------------- Geração FAKE ------------------------------- #

def gerar_bancos_csv_fake(destino_csv: str, bancos: Optional[List[Dict]] = None) -> str:
    bancos = bancos or DEFAULT_BANCOS_FAKE
    validar_bancos(bancos)
    os.makedirs(os.path.dirname(destino_csv), exist_ok=True)
    pd.DataFrame(bancos).to_csv(destino_csv, index=False, encoding="utf-8")
    return destino_csv


def garantir_bancos_csv(destino_csv: str, bancos: Optional[List[Dict]] = None) -> str:
    """Se `destino_csv` não existir, gera com bancos fake (compat antiga)."""
    if not os.path.exists(destino_csv):
        return gerar_bancos_csv_fake(destino_csv, bancos=bancos)
    return destino_csv

# ------------------------------ __main__ --------------------------------- #

if __name__ == "__main__":
    """
    Exemplos (rodar a partir da raiz, com PYTHONPATH=src):
      - Real mensal (mês fechado preferindo 'mercado'):
            python -m infrastructure.data.gerador_bancos real
      - Real diário por início (preferindo reguladas):
            python -m infrastructure.data.gerador_bancos real_diario
      - Fake/offline:
            python -m infrastructure.data.gerador_bancos fake
    """
    modo = (sys.argv[1].lower() if len(sys.argv) > 1 else "real")
    root = Path.cwd()
    for _ in range(6):
        if (root / "src").is_dir() and (root / "dados").is_dir():
            break
        root = root.parent
    destino = str(root / "dados" / "bancos.csv")

    if modo == "real":
        mes = _last_closed_month_yyyy_mm()
        print(f"Gerando bancos.csv REAL (mensal={mes}, prefer='mercado')…")
        out = gerar_bancos_csv_real(destino, tipo="mensal", mes=mes, prefer="mercado", top_n_bancos=30, on_error="fallback")
        print("OK:", out)

    elif modo == "real_diario":
        m = _last_closed_month_yyyy_mm()
        inicio = f"{m}-01"
        print(f"Gerando bancos.csv REAL (diário início={inicio}, prefer='reguladas')…")
        out = gerar_bancos_csv_real(destino, tipo="diario", inicio=inicio, prefer="reguladas", top_n_bancos=30, on_error="fallback")
        print("OK:", out)

    elif modo in ("fake", "offline"):
        print("Gerando bancos.csv FAKE…")
        out = gerar_bancos_csv_fake(destino)
        print("OK:", out)

    else:
        print("Modo inválido. Use: real | real_diario | fake")
