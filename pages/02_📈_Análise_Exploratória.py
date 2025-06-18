import streamlit as st
import pandas as pd
from datetime import datetime
import pymysql
from sqlalchemy import create_engine

# Configuração da página
st.set_page_config(page_title="ETL Controle Estoque", layout="wide")
st.title("Consulta ETL Controle Estoque")

# Conexão com banco
DATABASE_URL = 'mysql+pymysql://erpj-ws:erpj-ws-homologacao@10.50.1.252:3306/autogeral'

# Criar colunas para os filtros
col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)

# Filtros
with col1:
    data_inicio = st.date_input("Data Início", datetime.now())
    
with col2:
    data_fim = st.date_input("Data Fim", datetime.now())
    
with col3:
    loja_origem = st.selectbox(
        "Loja Origem", 
        ["Todas"] + list(range(1, 13))
    )
    
with col4:
    codigo_x = st.text_input("Código X (opcional)")
    
with col5:
    codigo_sequencia = st.text_input("Código Sequência (opcional)").upper()

# Selectbox para situação
situacao = st.selectbox("Situação", ["FECHADO", "EM_ABERTO"])

# Botão de buscar
if st.button("Buscar", type="primary"):
    
    # Montar query SQL base
    query = """
    SELECT
        ETL.LOJA_ORIGEM,
        ETL.LOJA_DESTINO,
        ETL.CODIGO_X,
        ETL.CODIGO_SEQUENCIA,
        SUM(ETL.QUANTIDADE) AS TOTAL_QUANTIDADE,
        ETL.DATA_DESTINO
    FROM
        ETL_CONTROLE_ESTOQUE ETL
    WHERE
        ETL.DATA_DESTINO BETWEEN '{}' AND '{}'
        AND ETL.SITUACAO = '{}'
    """.format(data_inicio, data_fim, situacao)
    
    # Adicionar filtros opcionais
    if loja_origem != "Todas":
        query += f" AND ETL.LOJA_ORIGEM = {loja_origem}"
    
    if codigo_x:
        query += f" AND ETL.CODIGO_X = '{codigo_x}'"
    
    if codigo_sequencia:
        query += f" AND ETL.CODIGO_SEQUENCIA = '{codigo_sequencia}'"
    
    query += """
    GROUP BY
        ETL.LOJA_ORIGEM,
        ETL.LOJA_DESTINO,
        ETL.CODIGO_X,
        ETL.CODIGO_SEQUENCIA,
        ETL.DATA_DESTINO
    ORDER BY
        ETL.DATA_DESTINO DESC
    """
    
    # Executar query
    try:
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql_query(query, engine)
        engine.dispose()
        
        # Mostrar resultados
        if not df.empty:
            st.success(f"Encontrados {len(df)} registros")
            
            # Exibir métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Quantidade", f"{df['TOTAL_QUANTIDADE'].sum():,.0f}")
            with col2:
                st.metric("Total Registros", len(df))
            with col3:
                st.metric("Lojas Únicas", df['LOJA_ORIGEM'].nunique())
            
            # Tabela interativa
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "LOJA_ORIGEM": st.column_config.NumberColumn("Loja Origem", format="%d"),
                    "LOJA_DESTINO": st.column_config.NumberColumn("Loja Destino", format="%d"),
                    "CODIGO_X": "Código X",
                    "CODIGO_SEQUENCIA": "Código Seq.",
                    "TOTAL_QUANTIDADE": st.column_config.NumberColumn(
                        "Total Qtd",
                        format="%d"
                    ),
                    "DATA_DESTINO": st.column_config.DateColumn("Data Destino", format="DD/MM/YYYY")
                }
            )
            
            # Criar coluna CODI_X_SEQ
            df['CODI_X_SEQ'] = df['CODIGO_X'].astype(str) + ' - ' + df['CODIGO_SEQUENCIA'].astype(str)
            
            # Lógica de gráficos baseada na seleção
            if loja_origem != "Todas":
                # Se uma loja específica foi selecionada
                st.subheader(f"Fluxo de Produtos - Loja {loja_origem}")
                
                # Gráfico 1: Top 10 produtos saindo da loja origem
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Produtos Saindo (Por Destino)**")
                    saidas = df.groupby(['LOJA_DESTINO', 'CODI_X_SEQ'])['TOTAL_QUANTIDADE'].sum().reset_index()
                    saidas_pivot = saidas.pivot(index='CODI_X_SEQ', columns='LOJA_DESTINO', values='TOTAL_QUANTIDADE').fillna(0)
                    top_produtos = saidas_pivot.sum(axis=1).nlargest(10).index
                    st.bar_chart(saidas_pivot.loc[top_produtos])
                
                with col2:
                    st.write("**Total por Produto (CODI_X_SEQ)**")
                    produtos_total = df.groupby('CODI_X_SEQ')['TOTAL_QUANTIDADE'].sum().nlargest(10)
                    st.bar_chart(produtos_total)
                
                # Gráfico 3: Fluxo detalhado origem->destino
                st.write("**Fluxo Detalhado: Origem → Destino**")
                fluxo_data = df.groupby(['LOJA_DESTINO'])['TOTAL_QUANTIDADE'].sum().sort_values(ascending=False)
                st.bar_chart(fluxo_data)
                
            else:
                # Se "Todas" as lojas foram selecionadas
                st.subheader("Quantidade por Loja Origem")
                chart_data = df.groupby('LOJA_ORIGEM')['TOTAL_QUANTIDADE'].sum().reset_index()
                st.bar_chart(chart_data.set_index('LOJA_ORIGEM'))
            
            # Download dos dados
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name=f"etl_estoque_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("Nenhum registro encontrado com os filtros selecionados")
            
    except Exception as e:
        st.error(f"Erro ao executar consulta: {str(e)}")
        st.info("Verifique a conexão com o banco de dados")

# Mostrar query executada (para debug)
with st.expander("Ver Query SQL"):
    if 'query' in locals():
        st.code(query, language='sql')

# Editor de Query SQL Customizada
st.markdown("---")
st.subheader("🔧 Se quiser criar sua Query SQL ")

query_customizada = st.text_area(
    "Digite sua query SQL:", 
    height=200,
    placeholder="SELECT * FROM ETL_CONTROLE_ESTOQUE WHERE ...",
    help="Digite uma query SQL válida para executar no banco de dados"
)

if st.button("Executar sua Query ", type="secondary"):
    if query_customizada.strip():
        try:
            engine = create_engine(DATABASE_URL)
            df_custom = pd.read_sql_query(query_customizada, engine)
            engine.dispose()
            
            st.success(f"Query executada! {len(df_custom)} registros encontrados")
            
            # Mostrar tabela
            st.dataframe(df_custom, use_container_width=True)
            
            
        except Exception as e:
            st.error(f"Erro ao executar query customizada: {str(e)}")


    
st.sidebar.header("⚙️ Configuração")
st.sidebar.write(f"Banco Host: 252")