# -*- coding: utf-8 -*-
"""
Expande dados/ipca.csv para N meses (default=360),
repetindo o último valor quando faltar dado.
Gera dados/ipca_360.csv.

Requisitos: pandas (já usado no projeto).
"""
import os
import sys
import pandas as pd


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DADOS = os.path.join(ROOT, 'dados')
SRC   = os.path.join(ROOT, 'src')

if SRC not in sys.path:
    sys.path.insert(0, SRC)

ALVO_MESES = 360  # ajuste se quiser outro prazo

from infrastructure.data.leitor_csv import ler_csv  # usa o mesmo parser do projeto

def main():
    origem = os.path.join(DADOS, 'ipca.csv')
    saida  = os.path.join(DADOS, f'ipca_{ALVO_MESES}.csv')

    print(f"📄 Lendo: {origem}")
    df = ler_csv(origem)  # normaliza colunas para 'data' e 'ipca' (float), remove lixo

    # Tenta inferir datas mensais
    # Aceita 'YYYY-MM' ou 'MM/YYYY'
    d1 = pd.to_datetime(df['data'].astype(str), format='%Y-%m', errors='coerce')
    d2 = pd.to_datetime(df['data'].astype(str), format='%m/%Y', errors='coerce')
    data = d1.fillna(d2)
    data = data.fillna(pd.to_datetime(df['data'].astype(str), errors='coerce'))
    if data.isna().any():
        raise ValueError("Não foi possível interpretar algumas datas do ipca.csv")

    df = df.copy()
    df['_data'] = data
    df = df.sort_values('_data').reset_index(drop=True)

    if len(df) >= ALVO_MESES:
        print(f"✅ Já há {len(df)} meses (>= {ALVO_MESES}). Nada a expandir.")
        df[['data','ipca']].to_csv(saida, index=False, encoding='utf-8')
        print(f"💾 Salvo: {saida}")
        return

    # Gera grade mensal contínua
    inicio = df.loc[0, '_data'].to_period('M').to_timestamp()
    grade  = pd.date_range(start=inicio, periods=ALVO_MESES, freq='MS')  # mês-início
    grade_df = pd.DataFrame({'_data': grade})

    # Merge e forward-fill do último IPCA
    out = grade_df.merge(df[['_data','ipca']], on='_data', how='left')
    out['ipca'] = out['ipca'].ffill()  # repete último valor quando faltar
    if out['ipca'].isna().any():
        raise ValueError("Falha ao preencher IPCA: existem NaN após ffill()")

    # Formata 'data' como YYYY-MM, mantém ipca como float com ponto
    out['data'] = out['_data'].dt.strftime('%Y-%m')
    out = out[['data','ipca']]

    print(f"📈 Linhas originais: {len(df)}  →  Linhas finais: {len(out)} (meta={ALVO_MESES})")
    out.to_csv(saida, index=False, encoding='utf-8')
    print(f"💾 Salvo: {saida}")

if __name__ == '__main__':
    main()
