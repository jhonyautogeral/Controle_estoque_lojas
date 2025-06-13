import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from db_connection import get_engine, load_romaneios, load_romaneios_itens, merge_data
import pandas as pd


def plot_bar(df):
    df = df.copy()
    df['CODIGO_SEQUENCIA'] = df['CODIGO_SEQUENCIA'].fillna('').astype(str).str.strip()
    df['CODIGO_X_SEQ'] = df.apply(
        lambda row: f"{row['CODIGO_X']} - {row['CODIGO_SEQUENCIA']}" if row['CODIGO_SEQUENCIA'] else f"{row['CODIGO_X']} - (vazio)",
        axis=1
    )

    df_grouped = (
        df.groupby(['LOJA DESTINO', 'CODIGO_X_SEQ'])
        .agg({'QUANTIDADE': 'sum'})
        .reset_index()
    )

    # Selecionar top 10 itens por soma total para limitar colunas
    top_items = (
        df_grouped.groupby('CODIGO_X_SEQ')['QUANTIDADE']
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .index
    )
    df_top = df_grouped[df_grouped['CODIGO_X_SEQ'].isin(top_items)]

    # Vega-Lite expects data in long format
    # Vamos criar um gráfico de barras agrupadas (grouped bar chart)
    # com LOJA DESTINO no eixo X, QUANTIDADE no eixo Y e CODIGO_X_SEQ como cor

    # Paleta de cores sem vermelho e verde
    palette = [
        "#1f77b4",  # azul
        "#ff7f0e",  # laranja
        "#9467bd",  # roxo
        "#17becf",  # ciano
        "#bcbd22",  # amarelo
        "#8c564b",  # marrom
        "#e377c2",  # rosa
        "#7f7f7f",  # cinza
        "#aec7e8",  # azul claro
        "#ffbb78"   # laranja claro
    ]

    # Mapear cores para os top_items
    color_map = {item: palette[i] for i, item in enumerate(top_items)}

    # Construir o spec do Vega-Lite
    spec = {
        "width": 800,
        "height": 400,
        "data": {
            "values": df_top.to_dict(orient="records")
        },
        "mark": "bar",
        "encoding": {
            "x": {
                "field": "LOJA DESTINO",
                "type": "nominal",
                "axis": {"labelAngle": -45},
                "title": "Loja Destino"
            },
            "y": {
                "field": "QUANTIDADE",
                "type": "quantitative",
                "title": "Quantidade Total de Itens"
            },
            "color": {
                "field": "CODIGO_X_SEQ",
                "type": "nominal",
                "scale": {
                    "domain": list(color_map.keys()),
                    "range": list(color_map.values())
                },
                "legend": {"title": "CODIGO_X - CODIGO_SEQUENCIA"}
            },
            "tooltip": [
                {"field": "LOJA DESTINO", "type": "nominal"},
                {"field": "CODIGO_X_SEQ", "type": "nominal"},
                {"field": "QUANTIDADE", "type": "quantitative"}
            ]
        }
    }

    st.subheader('Quantidade de Itens (CODIGO_X - CODIGO_SEQUENCIA) por Loja Destino (Top 10 Itens)')
    st.vega_lite_chart(spec, use_container_width=True)


def plot_pie(df):
    df_grouped = (
        df.groupby('LOJA DESTINO')
        .agg({'QUANTIDADE': 'sum'})
        .reset_index()
        .sort_values('QUANTIDADE', ascending=False)
        .reset_index(drop=True)
    )

    n = len(df_grouped)
    colors = []
    for i in range(n):
        if i < int(n * 0.6):
            colors.append('#1f77b4')
        elif i < int(n * 0.9):
            colors.append('#9467bd')  # roxo em vez de verde
        else:
            colors.append('#ff7f0e')

    fig, ax = plt.subplots()
    ax.pie(
        df_grouped['QUANTIDADE'],
        labels=df_grouped['LOJA DESTINO'],
        autopct='%1.1f%%',
        startangle=140,
        colors=colors
    )
    ax.set_title('Distribuição Percentual da Quantidade de Itens por Loja Destino')
    st.pyplot(fig)


def plot_heatmap_entrada(df):
    if not isinstance(df['DATA_DESTINO'].iloc[0], pd.Period):
        df['MES_ANO'] = pd.to_datetime(df['DATA_DESTINO']).dt.to_period('M').astype(str)
    else:
        df['MES_ANO'] = df['DATA_DESTINO'].astype(str)

    df_grouped = (
        df.groupby(['LOJA DESTINO', 'MES_ANO'])
        .agg({'QUANTIDADE': 'sum'})
        .reset_index()
    )

    todas_lojas = list(range(1, 14))
    todas_lojas_str = [str(loja) for loja in todas_lojas]

    meses = sorted(df_grouped['MES_ANO'].unique())
    idx = pd.MultiIndex.from_product([todas_lojas_str, meses], names=['LOJA DESTINO', 'MES_ANO'])

    df_grouped['LOJA DESTINO'] = df_grouped['LOJA DESTINO'].astype(str)
    df_grouped = df_grouped.set_index(['LOJA DESTINO', 'MES_ANO']).reindex(idx, fill_value=0).reset_index()

    pivot = df_grouped.pivot(index='LOJA DESTINO', columns='MES_ANO', values='QUANTIDADE')

    fig, ax = plt.subplots(figsize=(12, 8))
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

    df_grouped = (
        df.groupby(['LOJA ORIGEM', 'MES_ANO'])
        .agg({'QUANTIDADE': 'sum'})
        .reset_index()
    )

    todas_lojas = list(range(1, 14))
    todas_lojas_str = [str(loja) for loja in todas_lojas]

    meses = sorted(df_grouped['MES_ANO'].unique())
    idx = pd.MultiIndex.from_product([todas_lojas_str, meses], names=['LOJA ORIGEM', 'MES_ANO'])

    df_grouped['LOJA ORIGEM'] = df_grouped['LOJA ORIGEM'].astype(str)
    df_grouped = df_grouped.set_index(['LOJA ORIGEM', 'MES_ANO']).reindex(idx, fill_value=0).reset_index()

    pivot = df_grouped.pivot(index='LOJA ORIGEM', columns='MES_ANO', values='QUANTIDADE')

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap='Greens', ax=ax)
    ax.set_title('Mapa de Calor: Quantidade de Itens Saindo da Loja Origem por Mês/Ano (Todas as Lojas)')
    ax.set_xlabel('Mês/Ano')
    ax.set_ylabel('Loja Origem')
    st.pyplot(fig)


def filtrar_multiplos_codigos(df, codigos_x, codigos_seq):
    codigos_x_limpos = [codigo.strip() for codigo in codigos_x]
    if not any(codigos_x_limpos):
        return df

    filtro_total = pd.Series([False] * len(df))

    for codigo_x, codigo_seq in zip(codigos_x_limpos, codigos_seq):
        if not codigo_x:
            continue
        cond_codigo_x = df['CODIGO_X'].astype(str).str.contains(codigo_x, case=False, na=False)
        codigo_seq_limpo = codigo_seq.strip() if codigo_seq else ''
        if codigo_seq_limpo:
            cond_codigo_seq = df['CODIGO_SEQUENCIA'].astype(str).str.startswith(codigo_seq_limpo, na=False)
        else:
            cond_codigo_seq = df['CODIGO_SEQUENCIA'].isna() | (df['CODIGO_SEQUENCIA'].astype(str).str.strip() == '')
        filtro_total = filtro_total | (cond_codigo_x & cond_codigo_seq)

    return df[filtro_total]


def input_multiplos_codigos():
    qtd = st.number_input(
        'Quantos CODIGO_X deseja pesquisar? (1 a 10)',
        min_value=1,
        max_value=10,
        value=1,
        step=1
    )
    codigos_x = []
    codigos_seq = []

    for i in range(qtd):
        col1, col2 = st.columns([2, 1])
        with col1:
            codigo_x = st.text_input(f'CODIGO_X #{i + 1}', key=f'codigo_x_{i}')
        with col2:
            codigo_seq = st.text_input(f'Letra inicial CODIGO_SEQUENCIA #{i + 1} (opcional)', key=f'codigo_seq_{i}')
        codigos_x.append(codigo_x)
        codigos_seq.append(codigo_seq)

    return codigos_x, codigos_seq


def main():
    st.title("Análise de Redistribuição de Itens de Estoque por Código")

    engine = get_engine()

    situacao = st.selectbox("Situação", ['FECHADO', 'EM_ABERTO'])
    loja_origem = st.selectbox("Loja Origem", options=list(range(1, 14)))
    data_inicio = st.date_input("Data Início", value=pd.to_datetime("2025-03-01"))
    data_fim = st.date_input("Data Fim", value=pd.to_datetime("2025-04-30"))

    with st.spinner("Carregando dados..."):
        df_romaneios = load_romaneios(engine, situacao, data_inicio, data_fim)
        df_itens = load_romaneios_itens(engine, data_inicio, data_fim)

    df_romaneios_filtrado = df_romaneios[df_romaneios['LOJA'] == loja_origem]
    df_itens_filtrado = df_itens[df_itens['LOJA'] == loja_origem]

    df_final_filtrado = merge_data(df_romaneios_filtrado, df_itens_filtrado)
    df_final_completo = merge_data(df_romaneios, df_itens)

    st.subheader(f"Filtro dinâmico por múltiplos CODIGO_X e CODIGO_SEQUENCIA na loja: {loja_origem}")

    codigos_x, codigos_seq = input_multiplos_codigos()

    df_filtrado = filtrar_multiplos_codigos(df_final_filtrado, codigos_x, codigos_seq)

    st.subheader(f"Tabela: Quantidade de Itens (CODIGO_X) Saindo da Loja Origem {loja_origem} para Loja Destino")
    st.dataframe(df_filtrado)

    plot_bar(df_filtrado)
    plot_pie(df_filtrado)

    st.subheader("Mapa de Calor: Itens Entrando na Loja Destino por Mês/Ano")
    plot_heatmap_entrada(df_final_completo)

    st.subheader("Mapa de Calor: Itens Saindo da Loja Origem por Mês/Ano")
    plot_heatmap_saida(df_final_completo)


if __name__ == "__main__":
    main()