# Projeto de Análise de Dados com Streamlit
# Análise de Redistribuição de Itens de Estoque

Este projeto consiste em uma aplicação Streamlit para analisar a redistribuição de itens de estoque entre lojas, com o objetivo de identificar padrões de demanda e otimizar a distribuição de estoque.

## Visão Geral

A aplicação extrai dados de um banco de dados MySQL, utilizando as tabelas `romaneios_dbf` e `romaneios_itens_dbf`, e apresenta visualizações interativas para auxiliar na análise.

## Componentes da Análise

1.  **Tabela: Quantidade de Itens (CODIGO\_X) Saindo da Loja Origem para Loja Destino**
    *   Exibe a quantidade de cada item transferida da loja de origem selecionada para as lojas de destino.
2.  **Gráfico de Barras: Quantidade de Itens (CODIGO\_X) por Loja Destino (Top 10 Itens)**
    *   Mostra a quantidade total dos 10 itens mais transferidos para cada loja de destino.
3.  **Gráfico de Pizza: Distribuição Percentual da Quantidade de Itens por Loja Destino**
    *   Exibe a distribuição percentual da quantidade total de itens transferidos para cada loja de destino.
4.  **Mapa de Calor: Quantidade de Itens Entrando na Loja Destino por Mês/Ano (Todas as Lojas)**
    *   Mostra a quantidade de itens que entraram em cada loja de destino ao longo do tempo.
5.  **Mapa de Calor: Quantidade de Itens Saindo da Loja Origem por Mês/Ano (Todas as Lojas)**
    *   Mostra a quantidade de itens que saíram de cada loja de origem ao longo do tempo.

## Explicação do Código

O código é estruturado em várias funções para facilitar a manutenção e a reutilização:

*   `get_engine()`: Cria e retorna um objeto de conexão com o banco de dados MySQL.
*   `load_romaneios(engine, situacao, data_inicio, data_fim)`: Carrega os dados da tabela `romaneios_dbf` com base nos filtros de situação e período de datas.
*   `load_romaneios_itens(engine, data_inicio, data_fim)`: Carrega os dados da tabela `romaneios_itens_dbf` com base no período de datas.
*   `merge_data(df_romaneios, df_itens)`: Une os dados das duas tabelas com base nas colunas `LOJA` e `ROMANEIO`, renomeando as colunas para melhor clareza.
*   `plot_bar(df)`: Plota o gráfico de barras da quantidade de itens por loja destino.
*   `plot_pie(df)`: Plota o gráfico de pizza da distribuição dos itens por loja destino.
*   `plot_heatmap_entrada(df)`: Plota o mapa de calor da quantidade de itens entrando na loja destino por mês/ano.
*   `plot_heatmap_saida(df)`: Plota o mapa de calor da quantidade de itens saindo da loja origem por mês/ano.
*   `main()`: Função principal que executa a aplicação Streamlit, carrega os dados, aplica os filtros, gera os gráficos e exibe os resultados.

## Como o Código Funciona

1.  **Conexão com o Banco de Dados:**
    *   A função `get_engine()` é utilizada para criar uma conexão com o banco de dados MySQL.
2.  **Extração de Dados:**
    *   As funções `load_romaneios()` e `load_romaneios_itens()` executam queries SQL e carregam os resultados em DataFrames do pandas.
3.  **Transformação e União de Dados:**
    *   A função `merge_data()` une os DataFrames resultantes das extrações.
4.  **Filtragem de Dados:**
    *   A função `main()` utiliza um selectbox do Streamlit para permitir que o usuário selecione uma loja de origem específica.
5.  **Geração de Visualizações:**
    *   As funções `plot_bar()`, `plot_pie()`, `plot_heatmap_entrada()` e `plot_heatmap_saida()` são responsáveis por gerar as visualizações dos dados.
6.  **Exibição dos Resultados:**
    *   A função `main()` utiliza as funções do Streamlit para exibir os resultados da análise na interface web.

## Como Usar

1.  **Configuração do Ambiente:**
    *   Certifique-se de ter o Python instalado em seu sistema.
    *   Instale as bibliotecas necessárias: `pip install streamlit pandas sqlalchemy matplotlib seaborn`.
2.  **Configuração do Banco de Dados:**
    *   Configure a conexão com o banco de dados MySQL, inserindo as credenciais corretas no código.
    *   Certifique-se de que as tabelas `romaneios_dbf` e `romaneios_itens_dbf` existam no banco de dados.
3.  **Execução da Aplicação:**
    *   Salve o código em um arquivo Python (por exemplo, `analise_estoque.py`).
    *   Execute a aplicação Streamlit: `streamlit run analise_estoque.py`.
4.  **Interação com a Aplicação:**
    *   Acesse a aplicação no navegador web através do endereço fornecido pelo Streamlit.
    *   Utilize os filtros na barra lateral para selecionar a situação, a loja de origem e o período de datas desejado.
    *   Analise a tabela e os gráficos exibidos na tela.

## Conclusão

Esta documentação fornece uma visão geral da análise de redistribuição de itens de estoque, explicando os componentes da análise, o funcionamento do código e como utilizar a aplicação Streamlit para obter insights sobre a movimentação de itens entre lojas.