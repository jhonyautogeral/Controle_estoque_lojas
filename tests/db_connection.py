import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

# Tenta usar o estilo 'seaborn-whitegrid', senão usa 'default'
try:
    plt.style.use('seaborn-whitegrid')
except OSError:
    plt.style.use('default')

def get_engine():
    return create_engine('mysql+pymysql://erpj-ws:erpj-ws-homologacao@localhost:3309/autogeral')

def load_romaneios(engine, situacao, data_inicio, data_fim):
    query = f"""
        SELECT
            R.LOJA,
            R.ROMANEIO,
            R.CADASTRO,
            R.CADASTRO_CODIGO
        FROM
            romaneios_dbf R
        WHERE
            R.OPERACAO_CODIGO = 4
            AND R.SITUACAO = '{situacao}'
            AND R.COMPRA_PEDIDO_LOJA IS NULL
            AND R.COMPRA_PEDIDO_CODIGO IS NULL
            AND R.ORIGEM_TIPO IS NULL
            AND R.CADASTRO BETWEEN '{data_inicio}' AND '{data_fim}'
    """
    df = pd.read_sql_query(query, engine)
    df['CADASTRO'] = pd.to_datetime(df['CADASTRO'])
    return df

def load_romaneios_itens(engine, data_inicio, data_fim):
    query = f"""
        SELECT
            ri.CADASTRO AS CADASTRO,
            ri.LOJA,
            ri.CODIGO_X,
            ri.CODIGO_SEQUENCIA,
            SUM(ri.QUANTIDADE) AS QUANTIDADE_TOTAL,
            ri.ROMANEIO,
            ri.DESCRICAO
        FROM
            romaneios_itens_dbf ri
        WHERE
            ri.CADASTRO BETWEEN '{data_inicio}' AND '{data_fim}'
        GROUP BY
            ri.CADASTRO,
            ri.LOJA,
            ri.CODIGO_X,
            ri.CODIGO_SEQUENCIA,
            ri.DESCRICAO,
            ri.ROMANEIO
    """
    df = pd.read_sql_query(query, engine)
    df['CADASTRO'] = pd.to_datetime(df['CADASTRO'])
    return df

def merge_data(df_romaneios, df_itens):
    df_merged = pd.merge(
        df_itens,
        df_romaneios[['LOJA', 'ROMANEIO', 'CADASTRO_CODIGO', 'CADASTRO']],
        how='inner',
        left_on=['LOJA', 'ROMANEIO'],
        right_on=['LOJA', 'ROMANEIO'],
        suffixes=('_ORIGEM', '_DESTINO')
    )
    df_merged.rename(columns={
        'LOJA': 'LOJA ORIGEM',
        'CADASTRO_CODIGO': 'LOJA DESTINO',
        'CODIGO_X': 'CODIGO_X',
        'CODIGO_SEQUENCIA': 'CODIGO_SEQUENCIA',
        'QUANTIDADE_TOTAL': 'QUANTIDADE',
        'CADASTRO_DESTINO': 'DATA_DESTINO',
        'CADASTRO_ORIGEM': 'DATA_ORIGEM'
    }, inplace=True)
    df_merged.rename(columns={'CADASTRO': 'DATA_DESTINO'}, inplace=True)
    df_merged['DATA_DESTINO'] = pd.to_datetime(df_merged['DATA_DESTINO'], errors='coerce').dt.to_period('M')
    return df_merged[['LOJA ORIGEM', 'LOJA DESTINO', 'CODIGO_X', 'CODIGO_SEQUENCIA', 'QUANTIDADE', 'DESCRICAO', 'DATA_DESTINO']]