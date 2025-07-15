import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Controle de Estoque ETL", layout="wide")
st.title("📊 Controle de Estoque ETL")


def conectar_banco():
    return create_engine('mysql+pymysql://user:senha@10.50.1.252:3306/banco')

# Carregar dados uma vez
@st.cache_data
def carregar_dados(data_inicio, data_fim, situacao):
    engine = conectar_banco()
    query = f"""
    SELECT 
        LOJA_ORIGEM, LOJA_DESTINO, CODIGO_X, CODIGO_SEQUENCIA,
        SUM(QUANTIDADE) AS TOTAL_QUANTIDADE, DATA_DESTINO
    FROM ETL_CONTROLE_ESTOQUE
    WHERE DATA_DESTINO BETWEEN '{data_inicio}' AND '{data_fim}'
    AND SITUACAO = '{situacao}'
    GROUP BY LOJA_ORIGEM, LOJA_DESTINO, CODIGO_X, CODIGO_SEQUENCIA, DATA_DESTINO
    """
    df = pd.read_sql(query, engine)
    engine.dispose()  # Fechar conexão
    return df

# Interface
col1, col2 = st.columns(2)

with col1:
    data_inicio = st.date_input("Data Início")
    data_fim = st.date_input("Data Fim")
    situacao = st.selectbox("Situação", ["FECHADO", "EM_ABERTO"])
    
with col2:
    loja_origem = st.selectbox("Loja Origem", [""] + list(range(1, 13)))
    formato_data = st.radio("Formato Data", ["Ano-Mês", "Ano-Mês-Dia"])

# Quantidade de filtros
qtd_filtros = st.number_input("Quantos código x Vai querer comparar?", 1, 5, 1)

# Criar campos dinamicamente
codigos_x = []
codigos_seq = []

cols = st.columns(qtd_filtros)
for i, col in enumerate(cols):
    with col:
        cod_x = st.text_input(f"Código X {i+1}")
        cod_seq = st.text_input(f"Sequência {i+1}").upper()
        codigos_x.append(cod_x)
        codigos_seq.append(cod_seq)

# Botão gerar
if st.button("Gerar Análise"):
    try:
        # Carregar dados
        df = carregar_dados(data_inicio, data_fim, situacao)
        
        if df.empty:
            st.warning("Nenhum dado encontrado para o período selecionado.")
        else:
            # Filtrar por loja se selecionado
            if loja_origem:
                df = df[df['LOJA_ORIGEM'] == int(loja_origem)]
            
            # Filtrar por códigos
            df_filtrado = pd.DataFrame()
            for cod_x, cod_seq in zip(codigos_x, codigos_seq):
                temp = df.copy()
                if cod_x:
                    temp = temp[temp['CODIGO_X'] == int(cod_x)]
                if cod_seq:
                    temp = temp[temp['CODIGO_SEQUENCIA'] == cod_seq]
                df_filtrado = pd.concat([df_filtrado, temp])
            
            # Se nenhum filtro, usar todos
            if df_filtrado.empty:
                df_filtrado = df
            
            # Converter data
            if formato_data == "Ano-Mês":
                # Converte para período mensal para agrupamento
                df_filtrado['DATA_DESTINO'] = pd.to_datetime(df_filtrado['DATA_DESTINO']).dt.to_period('M')
            else:
                # Mantém a data original sem conversão
                df_filtrado['DATA_DESTINO'] = pd.to_datetime(df_filtrado['DATA_DESTINO']).dt.strftime('%Y-%m-%d')
            
            # Criar label para visualização
            df_filtrado['LABEL'] = df_filtrado['CODIGO_X'].astype(str) + ' - ' + df_filtrado['CODIGO_SEQUENCIA'].fillna('')
            
            # Se não digitou código X, pegar top 7
            if not any(codigos_x):
                df_agrupado = df_filtrado.groupby(['LOJA_ORIGEM', 'CODIGO_X', 'DATA_DESTINO'])['TOTAL_QUANTIDADE'].sum()
                top7 = df_agrupado.nlargest(7)
                indices = top7.index
                df_filtrado = df_filtrado[
                    df_filtrado.set_index(['LOJA_ORIGEM', 'CODIGO_X', 'DATA_DESTINO']).index.isin(indices)
                ]
            
            # Exibir tabela
            st.subheader("📋 Tabela de Dados")
            st.dataframe(df_filtrado)
            
            # Verifica se algum código_x foi digitado
            tem_codigo_x = any(cod for cod in codigos_x if cod)
            
            # Gráfico de barras
            st.subheader("📊 Gráfico de Barras")
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if tem_codigo_x:
                # Se digitou código_x, mostra transferências entre lojas
                df_plot = df_filtrado.groupby(['LOJA_ORIGEM', 'LOJA_DESTINO'])['TOTAL_QUANTIDADE'].sum().reset_index()
                df_plot['ROTA'] = df_plot['LOJA_ORIGEM'].astype(str) + ' → ' + df_plot['LOJA_DESTINO'].astype(str)
                df_plot = df_plot.sort_values('TOTAL_QUANTIDADE')
                bars = ax.barh(df_plot['ROTA'], df_plot['TOTAL_QUANTIDADE'], color='skyblue')
                ax.set_xlabel('Quantidade Total')
                ax.set_ylabel('Origem → Destino')
                ax.set_title('Transferências entre Lojas')
                
                # Adicionar valores nas barras
                for i, (bar, valor) in enumerate(zip(bars, df_plot['TOTAL_QUANTIDADE'])):
                    ax.text(bar.get_width() / 2, bar.get_y() + bar.get_height() / 2, 
                            f'{valor:,.0f}', ha='center', va='center', fontweight='bold')
            else:
                # Se não digitou código_x, mostra por código
                df_plot = df_filtrado.groupby('LABEL')['TOTAL_QUANTIDADE'].sum().sort_values(ascending=True)
                bars = ax.barh(df_plot.index, df_plot.values, color='skyblue')
                ax.set_xlabel('Quantidade Total')
                ax.set_title('Quantidade por Código')
                
                # Adicionar valores nas barras
                for bar, valor in zip(bars, df_plot.values):
                    ax.text(bar.get_width() / 2, bar.get_y() + bar.get_height() / 2, 
                            f'{valor:,.0f}', ha='center', va='center', fontweight='bold')
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Mapa de calor
            st.subheader("Mapa de Calor")
            fig, ax = plt.subplots(figsize=(12, 8))
            
            if tem_codigo_x:
                # Se digitou código_x, mostra mapa de calor loja origem x loja destino com data
                df_filtrado['ROTA'] = df_filtrado['LOJA_ORIGEM'].astype(str) + ' → ' + df_filtrado['LOJA_DESTINO'].astype(str)
                pivot = df_filtrado.pivot_table(
                    values='TOTAL_QUANTIDADE', 
                    index='ROTA', 
                    columns='DATA_DESTINO', 
                    aggfunc='sum', 
                    fill_value=0
                )
                titulo = 'Transferências entre Lojas por Período'
            else:
                # Se não digitou código_x, mostra por código e período
                pivot = df_filtrado.pivot_table(
                    values='TOTAL_QUANTIDADE', 
                    index='LABEL', 
                    columns='DATA_DESTINO', 
                    aggfunc='sum', 
                    fill_value=0
                )
                titulo = 'Quantidade por Código e Período'
            
            if not pivot.empty:
                sns.heatmap(pivot, annot=True, fmt='g', cmap='Blues', ax=ax)
                ax.set_title(titulo)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("Sem dados para o mapa de calor")
            
            # Estatísticas
            st.subheader("Resumo")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Geral", f"{df_filtrado['TOTAL_QUANTIDADE'].sum():,.0f}")
            with col2:
                st.metric("Média por Item", f"{df_filtrado['TOTAL_QUANTIDADE'].mean():,.0f}")
            with col3:
                st.metric("Items Únicos", len(df_filtrado['LABEL'].unique()))
                
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        st.info("Verifique a conexão com o banco de dados e os parâmetros informados.")
