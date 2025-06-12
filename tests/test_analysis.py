import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns

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
    return df_merged[['LOJA ORIGEM', 'LOJA DESTINO', 'CODIGO_X', 'CODIGO_SEQUENCIA', 'QUANTIDADE', 'DESCRICAO', 'DATA_DESTINO']]

def plot_bar(df):
    df_grouped = df.groupby(['LOJA DESTINO', 'CODIGO_X']).agg({'QUANTIDADE':'sum'}).reset_index()
    top_items = df_grouped.groupby('CODIGO_X')['QUANTIDADE'].sum().sort_values(ascending=False).head(10).index
    df_top = df_grouped[df_grouped['CODIGO_X'].isin(top_items)]

    # Paleta de cores sem verde e vermelho para 10 itens
    palette = [
        '#1f77b4',  # azul
        '#ff7f0e',  # laranja
        '#9467bd',  # roxo
        '#17becf',  # ciano
        '#bcbd22',  # amarelo
        '#8c564b',  # marrom
        '#e377c2',  # rosa
        '#7f7f7f',  # cinza
        '#aec7e8',  # azul claro
        '#ffbb78'   # laranja claro
    ]

    color_map = dict(zip(top_items, palette))

    fig, ax = plt.subplots(figsize=(12,6))
    sns.barplot(data=df_top, x='LOJA DESTINO', y='QUANTIDADE', hue='CODIGO_X', palette=color_map, ax=ax)
    ax.set_title('Quantidade de Itens (CODIGO_X) por Loja Destino (Top 10 Itens)')
    ax.set_xlabel('Loja Destino')
    ax.set_ylabel('Quantidade Total de Itens')
    ax.legend(title='CODIGO_X', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

def plot_pie(df):
    df_grouped = df.groupby('LOJA DESTINO').agg({'QUANTIDADE':'sum'}).reset_index()

    # Ordenar lojas por quantidade para aplicar regra de cores
    df_grouped = df_grouped.sort_values('QUANTIDADE', ascending=False).reset_index(drop=True)

    n = len(df_grouped)
    colors = []
    for i in range(n):
        if i < int(n*0.6):
            colors.append('#1f77b4')  # azul dominante
        elif i < int(n*0.9):
            colors.append('#2ca02c')  # verde secundário
        else:
            colors.append('#ff7f0e')  # laranja destaque

    fig, ax = plt.subplots()
    ax.pie(df_grouped['QUANTIDADE'], labels=df_grouped['LOJA DESTINO'], autopct='%1.1f%%', startangle=140, colors=colors)
    ax.set_title('Distribuição Percentual da Quantidade de Itens por Loja Destino')
    st.pyplot(fig)

def plot_heatmap_entrada(df):
    df['MES_ANO'] = df['DATA_DESTINO'].dt.to_period('M').astype(str)
    df_grouped = df.groupby(['LOJA DESTINO', 'MES_ANO']).agg({'QUANTIDADE':'sum'}).reset_index()
    pivot = df_grouped.pivot(index='LOJA DESTINO', columns='MES_ANO', values='QUANTIDADE').fillna(0)

    # Usar paleta sem vermelho, por exemplo 'Blues'
    fig, ax = plt.subplots(figsize=(12,8))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap='Blues', ax=ax)
    ax.set_title('Mapa de Calor: Quantidade de Itens Entrando na Loja Destino por Mês/Ano')
    ax.set_xlabel('Mês/Ano')
    ax.set_ylabel('Loja Destino')
    st.pyplot(fig)

def plot_heatmap_saida(df):
    df['MES_ANO'] = df['DATA_DESTINO'].dt.to_period('M').astype(str)
    df_grouped = df.groupby(['LOJA ORIGEM', 'MES_ANO']).agg({'QUANTIDADE':'sum'}).reset_index()
    pivot = df_grouped.pivot(index='LOJA ORIGEM', columns='MES_ANO', values='QUANTIDADE').fillna(0)

    # Usar paleta sem vermelho, por exemplo 'Greens'
    fig, ax = plt.subplots(figsize=(12,8))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap='Greens', ax=ax)
    ax.set_title('Mapa de Calor: Quantidade de Itens Saindo da Loja Origem por Mês/Ano (Todas as Lojas)')
    ax.set_xlabel('Mês/Ano')
    ax.set_ylabel('Loja Origem')
    st.pyplot(fig)

def main():
    st.title("Análise de Redistribuição de Itens de Estoque por Código")

    engine = get_engine()

    situacao = st.selectbox("Situação", ['FECHADO', 'EM_ABERTO'])
    loja_origem = st.selectbox("Loja Origem", options=list(range(1,14)))
    data_inicio = st.date_input("Data Início", value=pd.to_datetime("2025-03-01"))
    data_fim = st.date_input("Data Fim", value=pd.to_datetime("2025-04-30"))

    with st.spinner("Carregando dados..."):
        df_romaneios = load_romaneios(engine, situacao, data_inicio, data_fim)
        df_itens = load_romaneios_itens(engine, data_inicio, data_fim)

    # Filtrar dados para loja origem selecionada (para tabela, barra e pizza)
    df_romaneios_filtrado = df_romaneios[df_romaneios['LOJA'] == loja_origem]
    df_itens_filtrado = df_itens[df_itens['LOJA'] == loja_origem]

    df_final_filtrado = merge_data(df_romaneios_filtrado, df_itens_filtrado)
    df_final_completo = merge_data(df_romaneios, df_itens)  # para mapas de calor com todas as lojas

    # Caixa de busca para CODIGO_X acima da tabela
    st.subheader(f"Filtro por CODIGO_X loja: {loja_origem}")
    codigo_busca = st.text_input("Digite o CODIGO_X desejado (deixe vazio para mostrar todos)")

    # Container vazio para a tabela, que será atualizado dinamicamente
    tabela_container = st.empty()

    # Função para atualizar a tabela conforme o filtro
    def atualizar_tabela(codigo):
        if codigo:
            df_tabela = df_final_filtrado[df_final_filtrado['CODIGO_X'].astype(str).str.contains(codigo)]
        else:
            df_tabela = df_final_filtrado
        tabela_container.subheader(f"Tabela: Quantidade de Itens (CODIGO_X) Saindo da Loja Origem {loja_origem} para Loja Destino")
        tabela_container.dataframe(df_tabela)

    # Atualiza a tabela inicialmente e a cada mudança no input
    atualizar_tabela(codigo_busca)

    # Gráficos usam df_final_filtrado completo, sem filtro por CODIGO_X para evitar recarga
    plot_bar(df_final_filtrado)
    plot_pie(df_final_filtrado)

    st.subheader("Mapa de Calor: Itens Entrando na Loja Destino por Mês/Ano (Todas as Lojas)")
    plot_heatmap_entrada(df_final_completo)

    st.subheader("Mapa de Calor: Itens Saindo da Loja Origem por Mês/Ano (Todas as Lojas)")
    plot_heatmap_saida(df_final_completo)

if __name__ == "__main__":
    main()