# -*- coding: utf-8 -*-
"""
Coletor de Taxas de Juros (BCB/Olinda - OData: taxaJuros v2)

Recursos:
- TaxasJurosMensalPorMes          (médias mensais por instituição)
- TaxasJurosDiariaPorInicioPeriodo (médias dos últimos 5 dias úteis por instituição a partir de uma data)

Saídas (DataFrame harmonizado):
    instituicao (str)
    codigo_modalidade (int)
    codigo_segmento  (int)
    periodo          (str)  -> "YYYY-MM" (mensal) ou "YYYY-MM-DD" (diário/início)
    taxa_anual       (float)-> fração a.a. (ex.: 0.1234 = 12,34% a.a.)

Heurísticas:
- Autodetecta nomes de campos usando padrões (case-insensitive) p/ funcionar mesmo com pequenas variações.
- Tenta JSON, se falhar tenta CSV. Requisições com retries + backoff.
- Se não conseguir aplicar $filter, traz página(s) e filtra do lado do cliente.

Obs:
- Os códigos de modalidade mencionados no projeto (ex.: 903101, 905101, 903201, 905201, 903203, 905203)
  são aceitos em `codigo_modalidade`.
- Segmento PF = 1 (default).
"""

from __future__ import annotations

import io
import math
import time
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd


# ---------------------------- Configuração base ---------------------------- #

OLINDA_BASE = "https://olinda.bcb.gov.br/olinda/servico/taxaJuros/versao/v2/odata"
RECURSO_MENSAL = "TaxasJurosMensalPorMes"
RECURSO_DIARIO = "TaxasJurosDiariaPorInicioPeriodo"


# ------------------------------ HTTP / Retries ----------------------------- #

def _make_session():
    import requests
    from urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter

    s = requests.Session()
    retries = Retry(
        total=5, connect=5, read=5,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.headers.update({
        "Accept": "application/json",
        "User-Agent": "SAD-FI/1.0 (coletor_txjuros)",
    })
    return s


def _sleep_backoff(attempt: int, base: float = 0.7):
    time.sleep(base * (2 ** (attempt - 1)) * (1 + random.random() * 0.4))


# ------------------------------ Utilidades --------------------------------- #

def _first_key_like(keys: Iterable[str], *patterns: str) -> Optional[str]:
    """Retorna a primeira chave que contenha TODOS os padrões (case-insensitive)."""
    keys_list = list(keys)
    for k in keys_list:
        low = k.lower()
        if all(pat.lower() in low for pat in patterns):
            return k
    return None


def _coerce_percent_to_fraction(x: pd.Series) -> pd.Series:
    """
    Converte série de taxas (strings/nums) para float fração a.a.
    - Se estiver em string com vírgula → troca por ponto.
    - Se a mediana > 1 → assume % a.a. e divide por 100.
    """
    s = pd.to_numeric(
        x.astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )
    med = s.dropna().abs().median() if s.notna().any() else 0.0
    if med is not None and med > 1.0:
        s = s / 100.0
    return s


@dataclass
class ResultadoColeta:
    df: pd.DataFrame
    meta: Dict


# ------------------------------- Coletor ----------------------------------- #

class ColetorTxJuros:
    """
    Coleta taxas de juros por instituição financeira via Olinda/BCB (OData).
    """

    def __init__(self, base_url: str = OLINDA_BASE):
        self.base_url = base_url
        self.sess = _make_session()

    # -------------------------- Núcleo OData genérico -------------------------- #

    def _odata_get(self, recurso: str, params: Dict[str, str], timeout=(5, 45)) -> pd.DataFrame:
        """Tenta JSON; se falhar, tenta CSV; retorna DataFrame bruto."""
        import requests

        url = f"{self.base_url}/{recurso}"
        # 1) JSON
        try:
            r = self.sess.get(url, params={**params, "$format": "json"}, timeout=timeout)
            if r.status_code == 200 and r.content:
                data = r.json()
                values = data.get("value", []) if isinstance(data, dict) else []
                return pd.DataFrame(values)
        except (requests.RequestException, ValueError):
            pass

        # 2) CSV (se disponível)
        try:
            r2 = self.sess.get(url, params={**params, "$format": "csv"}, timeout=(5, 60))
            if r2.status_code == 200 and r2.text.strip():
                buf = io.StringIO(r2.text)
                # CSV do Olinda costuma ser ; com cabeçalhos em PT
                try:
                    raw = pd.read_csv(buf, sep=";")
                except Exception:
                    buf.seek(0)
                    raw = pd.read_csv(buf)  # tenta padrão
                return raw
            # Se ainda assim falhar, levanta o erro HTTP original (se houver)
            if 'r' in locals():
                r.raise_for_status()
            r2.raise_for_status()
        except Exception as e:
            raise

        # Se nada deu certo, retorna vazio
        return pd.DataFrame()

    def _paged_collect(
        self,
        recurso: str,
        base_params: Dict[str, str],
        page_size: int = 1000,
        max_pages: int = 50,
        retries_per_page: int = 3,
    ) -> pd.DataFrame:
        """Coleta paginado via $top/$skip; concatena e retorna."""
        frames: List[pd.DataFrame] = []
        for i in range(max_pages):
            skip = i * page_size
            last_err = None
            for attempt in range(1, retries_per_page + 1):
                try:
                    raw = self._odata_get(
                        recurso,
                        params={**base_params, "$top": str(page_size), "$skip": str(skip)},
                    )
                    if raw is not None and not raw.empty:
                        frames.append(raw)
                        break
                    else:
                        # página vazia → acabou
                        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
                except Exception as e:
                    last_err = e
                _sleep_backoff(attempt)
            if last_err:
                # se a página falhou após N tentativas, encerra com o que tem
                break
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # ------------------------ Autodetecção de colunas ------------------------- #

    @staticmethod
    def _detect_columns(df: pd.DataFrame, is_mensal: bool) -> Dict[str, str]:
        """
        Detecta colunas relevantes no DataFrame bruto (case-insensitive):
            - instituicao: algo como 'Instituicao', 'InstituicaoFinanceira', 'Nome'
            - cod_modalidade: 'codigoModalidade' / 'CodigoModalidade'
            - cod_segmento : 'codigoSegmento' / 'CodigoSegmento'
            - periodo     : 'Mes' (mensal: 'YYYY-MM') ou 'InicioPeriodo' (diário: 'YYYY-MM-DD')
            - taxa_anual  : algo contendo 'Taxa' e 'Ano' (ex.: 'TaxaJurosAoAno')
        """
        cols = list(df.columns)

        k_inst = (_first_key_like(cols, "institu")
                  or _first_key_like(cols, "nome")
                  or _first_key_like(cols, "denomina"))
        k_mod  = (_first_key_like(cols, "cod", "modal")
                  or _first_key_like(cols, "modalidade",))
        k_seg  = (_first_key_like(cols, "cod", "segmen")
                  or _first_key_like(cols, "segmento",))
        if is_mensal:
            k_per  = (_first_key_like(cols, "mes") or _first_key_like(cols, "compet"))
        else:
            k_per  = (_first_key_like(cols, "inicio", "period")
                      or _first_key_like(cols, "data"))
        # taxa: prioriza "ao ano"
        k_taxa = (_first_key_like(cols, "taxa", "ano")
                  or _first_key_like(cols, "taxa"))

        return {
            "instituicao": k_inst or "",
            "cod_modalidade": k_mod or "",
            "cod_segmento": k_seg or "",
            "periodo": k_per or "",
            "taxa": k_taxa or "",
        }

    @staticmethod
    def _normalize_period(value: pd.Series, is_mensal: bool) -> pd.Series:
        s = value.astype(str).str.strip()
        if is_mensal:
            # tenta normalizar para YYYY-MM
            s = (s.str.replace("/", "-", regex=False)
                   .str.slice(0, 7))
        else:
            # diário: YYYY-MM-DD (quando vier data completa)
            s = s.str.replace("/", "-", regex=False)
        return s

    # -------------------------- API de alto nível ---------------------------- #

    def coletar_mensal(
        self,
        mes: str,                         # "YYYY-MM" ou "YYYY-MM-01"
        codigo_modalidade: int,           # 903101, 905101, 903201, 905201, 903203, 905203
        codigo_segmento: int = 1,         # 1 = PF
        page_size: int = 5000,            # ↑ maior para varrer mais rápido
        max_pages: int = 100,             # ↑
    ) -> ResultadoColeta:
        """
        Coleta MENSAL por instituição. Tenta várias formas:
          1) $filter com Mes == 'YYYY-MM'
          2) $filter com Mes == 'YYYY-MM-01'
          3) $filter com MesReferencia (alguns recursos mudam cabeçalho)
          4) Baixa páginas e filtra no cliente
        """
        base_params = {}
        base = RECURSO_MENSAL

        # normalizações de mês aceitas
        mes = str(mes).strip()
        cand_mes = {mes[:7], mes[:10]}
        cand_mes = {m if len(m) == 7 else (m[:7]) for m in cand_mes} | {f"{m[:7]}-01" for m in cand_mes}

        tries = []
        for m in sorted(cand_mes):
            tries.append(f"Mes eq '{m}' and CodigoModalidade eq {int(codigo_modalidade)} and CodigoSegmento eq {int(codigo_segmento)}")
            # alguns datasets usam MesReferencia
            tries.append(f"MesReferencia eq '{m}' and CodigoModalidade eq {int(codigo_modalidade)} and CodigoSegmento eq {int(codigo_segmento)}")

        raw = pd.DataFrame()
        # 1) tenta filtros no servidor
        for fexpr in tries:
            try:
                raw = self._odata_get(base, params={"$filter": fexpr, "$top": str(page_size)})
                if raw is not None and not raw.empty:
                    break
            except Exception:
                pass

        # 2) se ainda vazio, pagina e filtra no cliente
        if raw is None or raw.empty:
            raw = self._paged_collect(base, {"$top": str(page_size)}, page_size=page_size, max_pages=max_pages)

        if raw is None or raw.empty:
            return ResultadoColeta(pd.DataFrame(), meta={"recurso": base, "mes": list(cand_mes), "etapa": "sem_dados"})

        cols = self._detect_columns(raw, is_mensal=True)

        def _ci_get(col: str, default=None):
            return raw[col] if col in raw.columns else pd.Series([default] * len(raw))

        per = self._normalize_period(_ci_get(cols["periodo"], ""), is_mensal=True)
        mod = pd.to_numeric(_ci_get(cols["cod_modalidade"], pd.NA), errors="coerce").astype("Int64")
        seg = pd.to_numeric(_ci_get(cols["cod_segmento"],  pd.NA), errors="coerce").astype("Int64")
        taxa = _coerce_percent_to_fraction(_ci_get(cols["taxa"], pd.NA))
        inst = _ci_get(cols["instituicao"], "").astype(str).str.strip()

        # filtra no cliente (forte)
        alvo_mes7 = next(iter(sorted({m[:7] for m in cand_mes})))  # escolhe o alvo YYYY-MM
        sel = pd.Series([True] * len(raw))
        if per.notna().any(): sel &= (per.str[:7] == alvo_mes7)
        if mod.notna().any(): sel &= (mod == int(codigo_modalidade))
        if seg.notna().any(): sel &= (seg == int(codigo_segmento))

        out = pd.DataFrame({
            "instituicao": inst[sel].reset_index(drop=True),
            "codigo_modalidade": int(codigo_modalidade),
            "codigo_segmento": int(codigo_segmento),
            "periodo": per[sel].reset_index(drop=True).fillna(alvo_mes7),
            "taxa_anual": taxa[sel].reset_index(drop=True),
        }).dropna(subset=["taxa_anual"]).reset_index(drop=True)

        return ResultadoColeta(out, meta={"recurso": base, "mes": alvo_mes7})

    def coletar_diaria_por_inicio(
        self,
        inicio_periodo: str,              # "YYYY-MM-DD" (aceita "YYYY-MM")
        codigo_modalidade: int,
        codigo_segmento: int = 1,
        page_size: int = 5000,
        max_pages: int = 50,
    ) -> ResultadoColeta:
        """
        Coleta DIÁRIA (média de 5 dias úteis a partir de 'inicio_periodo').
        Tenta:
          1) $filter com InicioPeriodo == 'YYYY-MM-DD'
          2) $filter com Data == 'YYYY-MM-DD' (alterna cabeçalho)
          3) pagina e filtra no cliente
        """
        base = RECURSO_DIARIO

        ini = str(inicio_periodo).strip()
        if len(ini) == 7:
            ini = f"{ini}-01"
        tries = [
            f"InicioPeriodo eq '{ini}' and CodigoModalidade eq {int(codigo_modalidade)} and CodigoSegmento eq {int(codigo_segmento)}",
            f"Data eq '{ini}' and CodigoModalidade eq {int(codigo_modalidade)} and CodigoSegmento eq {int(codigo_segmento)}",
        ]

        raw = pd.DataFrame()
        for fexpr in tries:
            try:
                raw = self._odata_get(base, params={"$filter": fexpr, "$top": str(page_size)})
                if raw is not None and not raw.empty:
                    break
            except Exception:
                pass

        if raw is None or raw.empty:
            raw = self._paged_collect(base, {"$top": str(page_size)}, page_size=page_size, max_pages=max_pages)

        if raw is None or raw.empty:
            return ResultadoColeta(pd.DataFrame(), meta={"recurso": base, "inicio": ini, "etapa": "sem_dados"})

        cols = self._detect_columns(raw, is_mensal=False)

        def _ci_get(col: str, default=None):
            return raw[col] if col in raw.columns else pd.Series([default] * len(raw))

        per = self._normalize_period(_ci_get(cols["periodo"], ""), is_mensal=False)
        mod = pd.to_numeric(_ci_get(cols["cod_modalidade"], pd.NA), errors="coerce").astype("Int64")
        seg = pd.to_numeric(_ci_get(cols["cod_segmento"],  pd.NA), errors="coerce").astype("Int64")
        taxa = _coerce_percent_to_fraction(_ci_get(cols["taxa"], pd.NA))
        inst = _ci_get(cols["instituicao"], "").astype(str).str.strip()

        sel = pd.Series([True] * len(raw))
        if per.notna().any(): sel &= (per.str[:10] == ini)
        if mod.notna().any(): sel &= (mod == int(codigo_modalidade))
        if seg.notna().any(): sel &= (seg == int(codigo_segmento))

        out = pd.DataFrame({
            "instituicao": inst[sel].reset_index(drop=True),
            "codigo_modalidade": int(codigo_modalidade),
            "codigo_segmento": int(codigo_segmento),
            "periodo": per[sel].reset_index(drop=True).fillna(ini),
            "taxa_anual": taxa[sel].reset_index(drop=True),
        }).dropna(subset=["taxa_anual"]).reset_index(drop=True)

        return ResultadoColeta(out, meta={"recurso": base, "inicio": ini})




# ------------------------------- __main__ ---------------------------------- #

if __name__ == "__main__":
    """
    Smoke rápido (rode a partir da raiz com PYTHONPATH=src):
        python -m infrastructure.data.coletor_txjuros
    """
    import sys, os
    # tenta detectar mês
    from datetime import date
    mes_ref = f"{date.today().year:04d}-{date.today().month:02d}"

    coletor = ColetorTxJuros()

    # Exemplos de modalidades (PF=1):
    MOD_PRE_MERCADO = 903101   # PF - financiamento imobiliário - pré - mercado
    MOD_TR_MERCADO  = 903201   # PF - pós TR - mercado
    MOD_IPCA_MERC   = 903203   # PF - pós IPCA - mercado

    print(">>> Coleta mensal (mes, modalidade=903101, segmento=1)")
    res_m = coletor.coletar_mensal(mes=mes_ref, codigo_modalidade=MOD_PRE_MERCADO, codigo_segmento=1)
    print(res_m.df.head().to_string(index=False) if not res_m.df.empty else "sem dados")
    print("linhas:", len(res_m.df))

    print("\n>>> Coleta diária (início=YYYY-MM-01, modalidade=903201, segmento=1)")
    inicio = f"{mes_ref}-01"
    res_d = coletor.coletar_diaria_por_inicio(inicio_periodo=inicio, codigo_modalidade=MOD_TR_MERCADO, codigo_segmento=1)
    print(res_d.df.head().to_string(index=False) if not res_d.df.empty else "sem dados")
    print("linhas:", len(res_d.df))
