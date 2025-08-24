from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Tuple, Dict

# suporte quando rodar este arquivo diretamente
if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # .../src

from infrastructure.data.tabela_tr import TabelaTR  # mantém import relativo

import datetime as _dt

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


SGS_TR_MENSAL = 226  


class ColetorTR:
    """Coleta TR mensal com normalização (YYYY-MM, fração).

    Modos:
      - fixture_csv_path: lê de CSV local (modo offline determinístico)
      - online=True: TODO integrar SGS (BACEN) se necessário
    """
    def __init__(self, fixture_csv_path: Optional[str] = None, online: bool = False, serie: int | None = None):
        self.fixture_csv_path = fixture_csv_path
        self.online = online
        self.serie = int(serie or SGS_TR_MENSAL)
        self._cache_df: Optional[pd.DataFrame] = None

    def coletar(self, inicio: Optional[str] = None, fim: Optional[str] = None) -> pd.DataFrame:
        if self._cache_df is not None:
            df = self._cache_df
        elif self.fixture_csv_path:
            df = pd.read_csv(self.fixture_csv_path)
        elif self.online:
            df = self._coletar_online(inicio, fim, self.serie)
        else:
            raise RuntimeError("Defina fixture_csv_path ou online=True para coletar TR")

        # Recorte opcional de período (após normalização)
        tabela = TabelaTR.from_dataframe(df)
        dfx = tabela.df
        if inicio:
            dfx = dfx[dfx["data"] >= inicio]
        if fim:
            dfx = dfx[dfx["data"] <= fim]
        self._cache_df = dfx.reset_index(drop=True)
        return self._cache_df
    
    @staticmethod
    def _make_session():
        import requests
        s = requests.Session()
        retries = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=0.8,                   # 0.8, 1.6, 2.4, ...
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        s.headers.update({
            "Accept": "application/json",
            "User-Agent": "SAD-FI/1.0 (+https://github.com/edina/SAD-FI)",
        })
        return s


    
    def _coletar_online(self, inicio: str | None, fim: str | None, serie: int) -> pd.DataFrame:
        """
        Coleta TR mensal no SGS (bcdata.sgs.{serie}) com múltiplos fallbacks:
        1) /dados?formato=...&dataInicial=...&dataFinal=...   (JSON → CSV)
        2) /dados/ultimos/{N}?formato=...                     (JSON → CSV)
        3) /dados?formato=...  (sem datas; baixa tudo e recorta localmente)
        """
        import requests
        import pandas as pd
        from datetime import datetime

        if not inicio or not fim:
            raise ValueError("Para TR online, informe 'inicio' (YYYY-MM) e 'fim' (YYYY-MM).")

        def _parse_ym(s: str) -> datetime:
            s = str(s).strip()[:7]
            return datetime.strptime(s, "%Y-%m")

        d_ini = _parse_ym(inicio)
        d_fim = _parse_ym(fim)
        if d_ini > d_fim:
            raise ValueError("Intervalo TR inválido: inicio > fim.")

        # N de meses (inclusivo)
        months = (d_fim.year - d_ini.year) * 12 + (d_fim.month - d_ini.month) + 1

        base = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{int(serie)}/dados"
        sess = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SAD-FI/1.0",
            "Accept": "*/*",
        }
        timeout = (5, 10)  # connect=5s, read=10s (fail-fast)

        def _normalize_df(raw: pd.DataFrame) -> pd.DataFrame:
            if raw is None or raw.empty:
                return pd.DataFrame()
            df = raw.rename(columns={"valor": "tr", "data": "data"}).copy()

            # "MM/YYYY" -> "YYYY-MM"
            def _ym(s: str) -> str:
                s = str(s).strip()
                if "/" in s:
                    mm, yy = s.split("/")
                    return f"{yy}-{int(mm):02d}"
                return s[:7]

            df["data"] = df["data"].map(_ym)

            # "0,00" → float
            df["tr"] = (
                df["tr"].astype(str)
                        .str.replace(",", ".", regex=False)
                        .str.replace("%", "", regex=False)
            )
            df["tr"] = pd.to_numeric(df["tr"], errors="coerce")

            # TR costuma vir em % a.m.; se mediana >1, converte para fração
            med = df["tr"].abs().median()
            if med is not None and pd.notna(med) and med > 1.0:
                df["tr"] = df["tr"] / 100.0
            return df.dropna(subset=["tr"]).reset_index(drop=True)

        def _recorte(df: pd.DataFrame) -> pd.DataFrame:
            ym_ini = f"{d_ini.year:04d}-{d_ini.month:02d}"
            ym_fim = f"{d_fim.year:04d}-{d_fim.month:02d}"
            m = (df["data"] >= ym_ini) & (df["data"] <= ym_fim)
            return df.loc[m, ["data", "tr"]].sort_values("data").reset_index(drop=True)

        # ---------- (1) Por intervalo (JSON→CSV) ----------
        try:
            params = {
                "formato": "json",
                "dataInicial": f"01/{d_ini.month:02d}/{d_ini.year}",
                "dataFinal":   f"31/{d_fim.month:02d}/{d_fim.year}",  # usa 31 para evitar 406 por dia
            }
            r = sess.get(base, params=params, headers=headers, timeout=timeout)
            r.raise_for_status()
            df = _recorte(_normalize_df(pd.DataFrame(r.json())))
            if not df.empty:
                return df
        except Exception:
            try:
                params_csv = {**params, "formato": "csv"}
                r2 = sess.get(base, params=params_csv, headers=headers, timeout=timeout)
                r2.raise_for_status()
                import io
                raw = pd.read_csv(io.StringIO(r2.text), sep=";")
                df = _recorte(_normalize_df(raw))
                if not df.empty:
                    return df
            except Exception:
                pass  # cai para ultimos

        # ---------- (2) /ultimos/{N} (JSON→CSV) ----------
        try:
            url_u = f"{base}/ultimos/{months}"
            r3 = sess.get(url_u, params={"formato": "json"}, headers=headers, timeout=timeout)
            r3.raise_for_status()
            df = _recorte(_normalize_df(pd.DataFrame(r3.json())))
            if not df.empty:
                return df
        except Exception:
            try:
                url_uc = f"{base}/ultimos/{months}"
                r4 = sess.get(url_uc, params={"formato": "csv"}, headers=headers, timeout=timeout)
                r4.raise_for_status()
                import io
                raw = pd.read_csv(io.StringIO(r4.text), sep=";")
                df = _recorte(_normalize_df(raw))
                if not df.empty:
                    return df
            except Exception:
                pass  # cai para full

        # ---------- (3) Full dump sem data (JSON→CSV) ----------
        try:
            r5 = sess.get(base, params={"formato": "json"}, headers=headers, timeout=timeout)
            r5.raise_for_status()
            df = _recorte(_normalize_df(pd.DataFrame(r5.json())))
            if not df.empty:
                return df
        except Exception:
            try:
                r6 = sess.get(base, params={"formato": "csv"}, headers=headers, timeout=timeout)
                r6.raise_for_status()
                import io
                raw = pd.read_csv(io.StringIO(r6.text), sep=";")
                df = _recorte(_normalize_df(raw))
                if not df.empty:
                    return df
            except Exception:
                pass

        raise requests.HTTPError("Falha ao obter TR (SGS): intervalos, 'ultimos' e full dump retornaram vazio/erro.")




if __name__ == "__main__":
    import argparse, os
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--inicio", default="2010-01")
    parser.add_argument("--fim", default="2025-07")
    parser.add_argument("--serie", type=int, default=226)
    parser.add_argument("--fixture", default=None, help="Caminho CSV de fallback para TR")
    args = parser.parse_args()

    def _first_existing(cands):
        for p in cands:
            if Path(p).exists():
                return str(Path(p))
        return None

    try:
        c = ColetorTR(online=True, serie=args.serie)
        df = c.coletar(args.inicio, args.fim)
        print(df.head(), "\n...\n", df.tail())
        print("linhas:", len(df))
    except Exception as e:
        print("⚠️ Online TR falhou:", e)

        # candidates para fixture local
        here = Path(__file__).resolve()
        cand = [
            args.fixture,  # se o usuário passou --fixture
            here.parent.parent.parent / "tests" / "fixtures" / "tr_fixture.csv",  # <root>/tests/fixtures
            Path.cwd() / "tests" / "fixtures" / "tr_fixture.csv",
            Path.cwd() / "fixtures" / "tr_fixture.csv",
        ]
        fixture = _first_existing([str(p) for p in cand if p is not None])

        if fixture:
            print("→ usando fallback local:", fixture)
            c = ColetorTR(online=False, fixture_csv_path=fixture)
            df = c.coletar(args.inicio, args.fim)
            print(df.head(), "\n...\n", df.tail())
            print("linhas:", len(df))
        else:
            print("Sem fixture local para fallback. Informe com:  python -m infrastructure.data.coletor_tr --fixture <caminho.csv>")
            raise


