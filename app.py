# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 15:11:22 2026

@author: AEPIT/MTE
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import json
import plotly.graph_objects as go

# FORÇAR ABERTURA NO NAVEGADOR (Configuração para o Spyder)
pio.renderers.default = 'browser' 

# %% configurando a pagina web
st.set_page_config(page_title="Meu Dashboard", layout="wide")

st.title("Áreas de Influência - Ponte Salvador Ilha de Itaparica")
st.write("---")



# %% Importando arquivo

tabela = pd.read_csv("dados/dados_tabelados_pescadores_2.csv",
                     encoding="latin-1",
                     sep=",")

# Carregar a base de dados de coordenadas do Brasil
cod_municipios = pd.read_csv("dados/municipios.csv",
                     encoding="latin-1",
                     sep = ";")

## Filtrar apenas o estado da Bahia (Código IBGE do estado da Bahia é 29)
df_bahia = cod_municipios[cod_municipios['codigo_uf'] == 29].copy()


# Carregar o arquivo GeoJSON baixado localmente ---
with open("dados/geojs-29-mun.json", "r", encoding="utf-8") as f:
    geojson_bahia = json.load(f)


# %% Ajustes nos dataframes

## organizando df tabela
tabela = tabela.dropna(subset = ["area_influencia"])
tabela["INDUSTRIAL"] = tabela["INDUSTRIAL"].fillna(0)

# Converter o ID do IBGE para Texto (String) para conversar com o GeoJSON
df_bahia['codigo_ibge'] = df_bahia['codigo_ibge'].astype(str)
tabela['cod_ibge'] = tabela['cod_ibge'].astype(str)

# %% Unindo as bases de dados

# Mesclar os DataFrames (Merge)
df = pd.merge(
    tabela, 
    df_bahia[['codigo_ibge', 'latitude', 'longitude']], 
    left_on='cod_ibge', 
    right_on='codigo_ibge', 
    how='left'
)

# Remove nulos, converte para inteiro e depois para texto de forma segura
df['Pescadores'] = df['Pescadores'].fillna(0).astype(int)
df['Quilombos'] = df['Quilombos'].fillna(0).astype(int)
#df['texto_mapa'] = df['municipio'] + '<br>' + df['total'].astype(str)

# %%  1. MAPEAMENTO DE CORES CATEGÓRICAS (UNIFICAÇÃO)

categorias_unicas = sorted(df['area_influencia'].unique())
cores = ['#e15759', '#59a14f', '#4e79a7']
# Cria o dicionário amarrando cada categoria a uma cor da lista
mapa_de_cores = {cat: cores[i % len(cores)] for i, cat in enumerate(categorias_unicas)}
# %% 2. CONSTRUÇÃO DO MAPA INTERATIVO

fig =  px.choropleth_map(
    df, 
   geojson=geojson_bahia,
    locations="codigo_ibge",       # Coluna que serve de chave no seu DataFrame
    featureidkey="properties.id",  # Chave correspondente dentro da estrutura do GeoJSON
    color="area_influencia",                # Coluna numérica que define a intensidade da cor
    color_discrete_map = mapa_de_cores , # Escala degradê de cores para a área
    labels = {'area_influencia':'Área de influência'},
    hover_name="municipio",
    hover_data = {"Pescadores": True,
                  "area_influencia": False,
                  "codigo_ibge": False,
                  "Quilombos": True,
                  "localidades_indigenas": True
        },
    zoom=5.5,
    center={"lat": -12.97, "lon": -38.50},
    map_style="open-street-map",   # Motor livre atualizado do Plotly
    opacity=0.7                    # Transparência para ver ruas e nomes sob as cores
)



fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

# %% 3. GRÁFICO 1: QUANTIDADE DE PESCADORES

df_pescadores = df.groupby('area_influencia', as_index = False)['Pescadores'].sum()


fig_pescadores = px.bar( 
    df_pescadores, 
    x = 'Pescadores', # Passamos a lista de colunas diretamente no eixo Y
    y='area_influencia',
    title= 'Total de pescadores: 74.668',
    orientation='h',
    color = 'area_influencia',
    color_discrete_map= mapa_de_cores,
    labels = {'area_influencia':'Área de influência'},
    barmode='group',       # 'group' deixa lado a lado. Use 'stack' se quiser empilhadas.
    text_auto=True,        # Adiciona os valores automaticamente no topo de cada barra
    opacity=0.7  
)

# Oculta a barra de cores lateral (color_bar) no gráfico de barras para o visual ficar mais limpo
fig_pescadores.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 0}, 
                             height=300,
                             bargap=0.0)

# %% 4. GRÁFICO 2: QUANTIDADE DE COM. QUILOMBOLAS
df_quilombos = df.groupby('area_influencia', as_index=False)['Quilombos'].sum()

fig_quilombos = px.bar( 
    df_quilombos, 
    x='Quilombos', 
    y='area_influencia', 
    title= 'Total de comunidades quilombolas: 283',
    orientation='h',
    color='area_influencia',
    color_discrete_map=mapa_de_cores,
    labels={'area_influencia': 'Área de influência', 'Quilombos': 'Total de Quilombos'},
    barmode='group',       
    text_auto=True,        
    opacity=0.7  
)

fig_quilombos.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 0}, 
                            height=300,
                            bargap=0.0)

# %% ==============================================================================
# RENDERIZAÇÃO NO STREAMLIT (DISPOSIÇÃO DAS LINHAS)
# ==============================================================================

# LINHA 1: MAPA EM LARGURA TOTAL
st.subheader(" Mapa de Distribuição das Áreas de Influência")
st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True) # Espaçamento suave entre linhas

# LINHA 2: GRÁFICOS DE BARRAS LADO A LADO
col_barras_1, col_barras_2 = st.columns(2)

with col_barras_1:
    st.subheader("🚣 Pescadores por Área de Influência")
    st.plotly_chart(fig_pescadores, width='stretch')

with col_barras_2:
    st.subheader("🏘️ Comunidades Quilombolas por Área de Influência")
    st.plotly_chart(fig_quilombos, width='stretch')
    
    
# LINHA 3: ESTATÍSTICAS
st.divider()

# Título adicionado após a linha de separação
st.subheader("📊 Notas  Estatísticas")
# st.subheader("📋 Detalhes do Projeto e Fontes de Dados") # Opção alternativa de tamanho

st.markdown("<br>", unsafe_allow_html=True) # Espaçamento suave (opcional)

# Oganização em 3 colunas para notas explicativas e resumo
info_col1, info_col2, info_col3 = st.columns(3)


with info_col1:
    st.markdown("#### 🚣 Pescadores")
    st.markdown(
        """
        Total de pescadores (74.668) representa **42,2%** do total do estado da Bahia, sendo:  
            * **ADA:** 11%  
            * **AID:** 8%  
            * **AII:** 23,2%
        """
        )
        
with info_col2:
    st.markdown("##### ⛺ Comunidades Indígenas")
    st.markdown(
        """
        * Total de aldeias indígenas = 4 (2 em Camaçari e 2 em Camamú).  
        * Representa  **1,1%** do total do estado da Bahia.
        """
    )
    
with info_col3:
    st.markdown("##### 🏘️ Comunidades Quilombolas")
    st.markdown(
        """
        Total de comunidades (283) representa **15,6%** do total do estado da Bahia, sendo:  
            * **ADA:** 2,5%  
            * **AID:** 1,2%  
            * **AII:** 11,9%
        """
    )
        

  
# LINHA 4: NOTAS DE RODAPÉ
st.divider()

# Organização em 2 colunas para notas explicativas e resumo
info_col4, info_col5 = st.columns(2)



with info_col4:
    st.markdown("### 🌍 Recorte Geográfico")
    st.markdown(
        """
        Municípios do Estado da Bahia impactados pelo empreendimento.  
        Áreas de Influência classificadas de acordo com Relatório de Impacto Ambiental - RIMA.  
        **Nomenclatura:** 
        * **ADA:** Área diretamente afetada. Área necessária para implantação das obras e passível de intervenção física direta.
        * **AID:** Área de influência direta. Áreas contíguas à ADA,compreende uma faixa de 3.000 m, centrada na diretriz da ponte/rodovia (1.500 de cada lado). Apesar de não conterem as obras de infraestrutura, apresentam risco de serem afetadas em função de suas características físicas, bióticas, sociais e econômicas. 
        * **AII:** Área de influência indireta. Área geográfica onde poderão se refletir as eventuais consequências, impactos ou efeitos induzidos pelo projeto.
        """
    )

with info_col5:
    st.markdown("### 📌 Notas Metodológicas")
    st.markdown(
        """
        * **Fonte de Dados - Comunidades quilombolas e aldeias indígenas:** Censo Demográfico IBGE 2022.
        * **Fonte de Dados - Pescadores:** BRASIL. Ministério da Pesca e Aquicultura. Painel Unificado do RGP. Brasília: MPA, [202-]. Disponível em: <https://www.gov.br/mpa/pt-br/assuntos/cadastro-registro-e-monitoramento/painel-unificado-do-registro-geral-da-atividade-pesqueira>. Acesso em: 17 jul. 2026.
        """
    )



# %% Rodar no Anaconda Prompt:
## cd C:\Users\camila.escobar\OneDrive - mtegovbr\Documentos\AEPIT\ponte Salvador-Itaparica\Informações MTE subsídio Ministro
## streamlit run app_2.py



