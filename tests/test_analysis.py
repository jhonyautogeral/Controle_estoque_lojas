import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from db_connection import get_engine, load_romaneios, load_romaneios_itens, merge_data
import pandas as pd

def plot_bar(df):
    df_grouped = df.groupby(['LOJA DESTINO', 'CODIGO_X']).agg({'QUANTIDADE':'sum'}).reset_index()
    top_items = df_grouped.groupby('CODIGO_X')['QUANTIDADE'].sum().sort_values(ascending=False).head(10).index
    df_top = df_grouped[df_grouped['CODIGO_X'].isin(top_items)]

    palette = [
        '#1f77b4', '#ff7f0e', '#9467bd', '#17becf', '#bcbd22',
        '#8c564b', '#e377c2', '#7f7f7f', '#aec7e8', '#ffbb78'
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
    df_grouped = df_grouped.sort_values('QUANTIDADE', ascending=False).reset_index(drop=True)

    n = len(df_grouped)
    colors = []
    for i in range(n):
        if i < int(n*0.6):
            colors.append('#1f77b4')
        elif i < int(n*0.9):
            colors.append('#2ca02c')
        else:
            colors.append('#ff7f0e')

    fig, ax = plt.subplots()
    ax.pie(df_grouped['QUANTIDADE'], labels=df_grouped['LOJA DESTINO'], autopct='%1.1f%%', startangle=140, colors=colors)
    ax.set_title('Distribuição Percentual da Quantidade de Itens por Loja Destino')
    st.pyplot(fig)

def plot_heatmap_entrada(df):
    if not isinstance(df['DATA_DESTINO'].iloc[0], pd.Period):
        df['MES_ANO'] = pd.to_datetime(df['DATA_DESTINO']).dt.to_period('M').astype(str)
    else:
        df['MES_ANO'] = df['DATA_DESTINO'].astype(str)
    
    df_grouped = df.groupby(['LOJA DESTINO', 'MES_ANO']).agg({'QUANTIDADE':'sum'}).reset_index()
    pivot = df_grouped.pivot(index='LOJA DESTINO', columns='MES_ANO', values='QUANTIDADE').fillna(0)

    fig, ax = plt.subplots(figsize=(12,8))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap='Blues', ax=ax)
    ax.set_title('Mapa de Calor: Quantidade de Itens Entrando na Loja Destino por Mês/Ano')
    ax.set_xlabel('Mês/Ano')
    ax.set_ylabel('Loja Destino')
    st.pyplot(fig)

def plot_heatmap_saida(df):
    if not isinstance(df['DATA_DESTINO'].iloc[0], pd.Period):
        df['MES_ANO'] = pd.to_datetime(df['DATA_DESTINO']).dt.to_period('M').astype(str)
    else:
        df['MES_ANO'] = df['DATA_DESTINO'].astype(str)
    
    df_grouped = df.groupby(['LOJA ORIGEM', 'MES_ANO']).agg({'QUANTIDADE':'sum'}).reset_index()
    pivot = df_grouped.pivot(index='LOJA ORIGEM', columns='MES_ANO', values='QUANTIDADE').fillna(0)

    fig, ax = plt.subplots(figsize=(12,8))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap='Greens', ax=ax)
    ax.set_title('Mapa de Calor: Quantidade de Itens Saindo da Loja Origem por Mês/Ano (Todas as Lojas)')
    ax.set_xlabel('Mês/Ano')
    ax.set_ylabel('Loja Origem')
    st.pyplot(fig)

def filtrar_por_codigo(df, codigo_x, codigo_sequencia):
    # Filtra pelo CODIGO_X se informado
    if codigo_x:
        df = df[df['CODIGO_X'].astype(str).str.contains(codigo_x, case=False, na=False)]
    # Filtra pelo CODIGO_SEQUENCIA se informado, senão filtra onde CODIGO_SEQUENCIA está vazio ou NaN
    if codigo_sequencia:
        df = df[df['CODIGO_SEQUENCIA'].astype(str).str.startswith(codigo_sequencia, na=False)]
    else:
        df = df[df['CODIGO_SEQUENCIA'].isna() | (df['CODIGO_SEQUENCIA'].astype(str).str.strip() == '')]
    return df

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

    df_romaneios_filtrado = df_romaneios[df_romaneios['LOJA'] == loja_origem]
    df_itens_filtrado = df_itens[df_itens['LOJA'] == loja_origem]

    df_final_filtrado = merge_data(df_romaneios_filtrado, df_itens_filtrado)
    df_final_completo = merge_data(df_romaneios, df_itens)

    st.subheader(f"Filtro por CODIGO_X e CODIGO_SEQUENCIA na loja: {loja_origem}")

    col1, col2 = st.columns([2,1])
    with col1:
        codigo_busca = st.text_input("Digite o CODIGO_X desejado (deixe vazio para mostrar todos)")
    with col2:
        codigo_seq_busca = st.text_input("Digite a letra inicial do CODIGO_SEQUENCIA (opcional)")

    tabela_container = st.empty()

    def atualizar_tabela(codigo_x, codigo_seq):
        df_tabela = filtrar_por_codigo(df_final_filtrado, codigo_x, codigo_seq)
        tabela_container.subheader(f"Tabela: Quantidade de Itens (CODIGO_X) Saindo da Loja Origem {loja_origem} para Loja Destino")
        tabela_container.dataframe(df_tabela)

    atualizar_tabela(codigo_busca, codigo_seq_busca)

    plot_bar(df_final_filtrado)
    plot_pie(df_final_filtrado)

    st.subheader("Mapa de Calor: Itens Entrando na Loja Destino por Mês/Ano")
    plot_heatmap_entrada(df_final_completo)

    st.subheader("Mapa de Calor: Itens Saindo da Loja Origem por Mês/Ano")
    plot_heatmap_saida(df_final_completo)

if __name__ == "__main__":
    main()