import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from db_connection import get_engine, load_romaneios, load_romaneios_itens, merge_data
import pandas as pd

def criar_codigo_x_seq(df):
    df = df.copy()
    df['CODIGO_SEQUENCIA'] = df['CODIGO_SEQUENCIA'].fillna('').astype(str).str.strip()
    df['CODIGO_X_SEQ'] = df.apply(
        lambda row: f"{row['CODIGO_X']} - {row['CODIGO_SEQUENCIA']}" if row['CODIGO_SEQUENCIA'] else f"{row['CODIGO_X']} - (vazio)",
        axis=1
    )
    return df

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

def plot_bar_destino(df, codigos_x, codigos_seq):
    df = criar_codigo_x_seq(df)
    df_filtrado = filtrar_multiplos_codigos(df, codigos_x, codigos_seq)

    df_grouped = (
        df_filtrado.groupby(['LOJA DESTINO', 'CODIGO_X_SEQ'])
        .agg({'QUANTIDADE': 'sum'})
        .reset_index()
    )

    usuario_digitou_codigo = any(codigo.strip() for codigo in codigos_x)

    if not usuario_digitou_codigo:
        top_items = (
            df_grouped.groupby('CODIGO_X_SEQ')['QUANTIDADE']
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .index
        )
        df_top = df_grouped[df_grouped['CODIGO_X_SEQ'].isin(top_items)]
        pivot = df_top.pivot(index='LOJA DESTINO', columns='CODIGO_X_SEQ', values='QUANTIDADE').fillna(0)
        titulo = 'Top 10 Quantidade de itens entrando na loja destino'
    else:
        pivot = df_grouped.pivot(index='LOJA DESTINO', columns='CODIGO_X_SEQ', values='QUANTIDADE').fillna(0)
        titulo = 'Quantidade de itens entrando na loja destino'

    if pivot.empty or (pivot.sum().sum() == 0):
        st.info(f'Não há dados para exibir no gráfico "{titulo}".')
        return

    st.subheader(titulo)
    st.bar_chart(pivot)

def plot_bar_origem_recebendo(df, loja_origem, codigos_x, codigos_seq):
    df = criar_codigo_x_seq(df)
    df_filtrado = filtrar_multiplos_codigos(df, codigos_x, codigos_seq)

    df_filtrado = df_filtrado[(df_filtrado['LOJA DESTINO'] == loja_origem) & (df_filtrado['LOJA ORIGEM'] != loja_origem)]

    df_grouped = (
        df_filtrado.groupby(['LOJA ORIGEM', 'CODIGO_X_SEQ'])
        .agg({'QUANTIDADE': 'sum'})
        .reset_index()
    )

    usuario_digitou_codigo = any(codigo.strip() for codigo in codigos_x)

    if not usuario_digitou_codigo:
        top_items = (
            df_grouped.groupby('CODIGO_X_SEQ')['QUANTIDADE']
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .index
        )
        df_top = df_grouped[df_grouped['CODIGO_X_SEQ'].isin(top_items)]
        pivot = df_top.pivot(index='LOJA ORIGEM', columns='CODIGO_X_SEQ', values='QUANTIDADE').fillna(0)
        titulo = 'Top 10 Quantidade de itens que loja origem recebe das outras lojas'
    else:
        pivot = df_grouped.pivot(index='LOJA ORIGEM', columns='CODIGO_X_SEQ', values='QUANTIDADE').fillna(0)
        titulo = 'Quantidade de itens que loja origem recebe das outras lojas'

    if pivot.empty or (pivot.sum().sum() == 0):
        st.info(f'Não há dados para exibir no gráfico "{titulo}".')
        return

    st.subheader(titulo)
    st.bar_chart(pivot)

def plot_pie(df, codigos_x, codigos_seq):
    df = criar_codigo_x_seq(df)
    df_filtrado = filtrar_multiplos_codigos(df, codigos_x, codigos_seq)

    df_grouped = (
        df_filtrado.groupby('LOJA DESTINO')
        .agg({'QUANTIDADE': 'sum'})
        .reset_index()
        .sort_values('QUANTIDADE', ascending=False)
        .reset_index(drop=True)
    )

    df_top = df_grouped.head(7)

    if df_top.empty or (df_top['QUANTIDADE'].sum() == 0):
        st.info('Não há dados para exibir no gráfico de pizza.')
        return

    n = len(df_top)
    colors = []
    for i in range(n):
        if i < int(n * 0.6):
            colors.append('#1f77b4')
        elif i < int(n * 0.9):
            colors.append('#2ca02c')
        else:
            colors.append('#ff7f0e')

    fig, ax = plt.subplots()
    ax.pie(
        df_top['QUANTIDADE'],
        labels=df_top['LOJA DESTINO'],
        autopct='%1.1f%%',
        startangle=140,
        colors=colors
    )
    ax.set_title('Top 7 Lojas Destino que mais pedem o(s) item(ns) selecionado(s)')
    st.pyplot(fig)

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
            codigo_seq = st.text_input(f'Letra inicial CODIGO_SEQUENCIA #{i + 1}', key=f'codigo_seq_{i}')
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

    codigos_x, codigos_seq = input_multiplos_codigos()

    limite_busca_str = st.text_input("Quantidade limite para busca no banco (deixe vazio para ilimitado)", value="")

    # Inicializar session_state se não existir
    if 'dados_carregados' not in st.session_state:
        st.session_state.dados_carregados = False
        st.session_state.df_filtrado = None
        st.session_state.df_final_completo = None
        st.session_state.codigos_x_busca = None
        st.session_state.codigos_seq_busca = None
        st.session_state.loja_origem_busca = None

    if st.button("BUSCAR"):
        if limite_busca_str.strip() == "":
            limite_busca = None
        else:
            try:
                limite_busca = int(limite_busca_str)
                if limite_busca <= 0:
                    limite_busca = None
            except ValueError:
                st.warning("Por favor, insira um número inteiro válido para o limite ou deixe vazio.")
                limite_busca = None

        with st.spinner("Carregando dados..."):
            df_romaneios = load_romaneios(engine, situacao, data_inicio, data_fim)
            df_itens = load_romaneios_itens(engine, data_inicio, data_fim)

        df_romaneios_filtrado = df_romaneios[df_romaneios['LOJA'] == loja_origem]
        df_itens_filtrado = df_itens[df_itens['LOJA'] == loja_origem]

        df_final_filtrado = merge_data(df_romaneios_filtrado, df_itens_filtrado)
        df_final_completo = merge_data(df_romaneios, df_itens)

        df_filtrado = filtrar_multiplos_codigos(df_final_filtrado, codigos_x, codigos_seq)

        # Armazenar dados no session_state
        st.session_state.dados_carregados = True
        st.session_state.df_filtrado = df_filtrado
        st.session_state.df_final_completo = df_final_completo
        st.session_state.codigos_x_busca = codigos_x
        st.session_state.codigos_seq_busca = codigos_seq
        st.session_state.loja_origem_busca = loja_origem

    # Exibir resultados se dados foram carregados
    if st.session_state.dados_carregados:
        st.subheader(f"Tabela: Quantidade de Itens (CODIGO_X) Saindo da Loja Origem {st.session_state.loja_origem_busca} para Loja Destino")
        st.dataframe(st.session_state.df_filtrado)

        plot_bar_destino(st.session_state.df_filtrado, st.session_state.codigos_x_busca, st.session_state.codigos_seq_busca)
        plot_bar_origem_recebendo(st.session_state.df_final_completo, st.session_state.loja_origem_busca, st.session_state.codigos_x_busca, st.session_state.codigos_seq_busca)

        # Só mostra opção de pizza se usuário digitou pelo menos 1 CODIGO_X
        if st.session_state.codigos_x_busca and any(codigo.strip() for codigo in st.session_state.codigos_x_busca):
            if st.checkbox("Exibir gráfico de pizza das lojas destino que mais pedem o(s) item(ns) selecionado(s)?"):
                plot_pie(st.session_state.df_filtrado, st.session_state.codigos_x_busca, st.session_state.codigos_seq_busca)

if __name__ == "__main__":
    main()