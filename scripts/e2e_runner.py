#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import argparse
import pandas as pd

# --- bootstrap PYTHONPATH -> src ---
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
# -----------------------------------

from application.controlador import ControladorApp
from presentation.plots import plot_ranking, save_fig_png

def main():
    ap = argparse.ArgumentParser(description="E2E offline: simulação multi-bancos + export de evidências.")
    ap.add_argument("--bancos", default="dados/bancos.csv")
    ap.add_argument("--ipca", default="dados/txjuros/IPCA_BACEN.csv")
    ap.add_argument("--tr",   default="dados/txjuros/TR_mensal_compat.csv")
    ap.add_argument("--valor-total", type=float, default=300_000.0, dest="valor_total")
    ap.add_argument("--entrada",     type=float, default=60_000.0)
    ap.add_argument("--prazo-anos",  type=int,   default=30, dest="prazo_anos")
    ap.add_argument("--taxa",        type=float, default=0.11, dest="taxa_juros_anual")
    args = ap.parse_args()

    # Verifica arquivos essenciais (caminhos relativos ao ROOT)
    reqs = {
        "bancos": ROOT / args.bancos,
        "ipca":   ROOT / args.ipca,
        "tr":     ROOT / args.tr,
    }
    missing = [k for k, p in reqs.items() if not p.exists()]
    if missing:
        print(f"[E2E] ERRO: arquivos ausentes: {', '.join(missing)}", file=sys.stderr)
        for k, p in reqs.items():
            print(f"  - {k}: {p}", file=sys.stderr)
        return 2

    # Executa simulação
    resultados, ranking, msg = ControladorApp().simular_multiplos_bancos(
        caminho_bancos_csv=str(reqs["bancos"]),
        dados_financiamento={
            "valor_total": args.valor_total,
            "entrada": args.entrada,
            "prazo_anos": args.prazo_anos,
            "taxa_juros_anual": args.taxa_juros_anual,
        },
        fonte_ipca={"caminho_ipca": str(reqs["ipca"])},
        fonte_tr={"fixture_csv_path": str(reqs["tr"])},
    )

    if not ranking:
        print("[E2E] ERRO: ranking vazio.", file=sys.stderr)
        return 3

    # Exporta CSV
    out_dir = ROOT / "resultados"
    out_g   = out_dir / "graficos"
    out_g.mkdir(parents=True, exist_ok=True)

    df_rank = pd.DataFrame(ranking, columns=["Oferta", "Total Pago"])
    df_rank.to_csv(out_dir / "ranking.csv", index=False, encoding="utf-8")

    # Exporta PNG (usa o mesmo plot da UI)
    fig = plot_ranking(df_rank)
    save_fig_png(fig, out_g / "ranking.png")

    # Resumo
    menor = df_rank.loc[df_rank["Total Pago"].idxmin()]
    maior = df_rank.loc[df_rank["Total Pago"].idxmax()]
    print(f"[E2E] OK | ofertas={len(df_rank)} | menor={menor['Oferta']} ({menor['Total Pago']:.2f}) | maior={maior['Oferta']} ({maior['Total Pago']:.2f})")
    print(f"[E2E] arquivos: {out_dir/'ranking.csv'} ; {out_g/'ranking.png'}")
    if isinstance(msg, str) and msg.strip():
        print(f"[E2E] msg: {msg.strip()}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
