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
st.title("Relatório de Impacto nas Áreas de Influência")
st.subheader("Sistema Rodoviário Ponte Salvador - Ilha de Itaparica")
st.write("---")


# %% Importando arquivo

tabela = pd.read_csv("dados/dados_tabelados_pescadores_3.csv",
                     encoding="latin-1",
                     sep=";")

# Remove possíveis espaços extras no nome das colunas
tabela.columns = tabela.columns.str.strip()

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
df['comunidades_quilombolas'] = df['comunidades_quilombolas'].fillna(0).astype(int)
#df['texto_mapa'] = df['municipio'] + '<br>' + df['total'].astype(str)
df['urbanizacao_perc'] = df['urbanizacao_perc'].str.replace(',', '.').astype(float)
df['quilombolas_perc'] = df['quilombolas_perc'].str.replace(',', '.').astype(float)
df['indigenas_perc'] = df['indigenas_perc'].str.replace(',', '.').astype(float)
df['analfabetismo_perc'] = df['analfabetismo_perc'].str.replace(',', '.').astype(float)
df['IDH_2010_valor'] = df['IDH_2010_valor'].str.replace(',', '.').astype(float)
df['beneficiados_PBF_perc'] = df['beneficiados_PBF_perc'].str.replace(',', '.').astype(float)
df['PIB_per_capita_valor'] = df['PIB_per_capita_valor'].str.replace(',', '.').astype(float)
df['VAB_com_serv_2021'] = df['VAB_com_serv_2021'].str.replace(',', '.').astype(float)
df['VAB_agro_2021'] = df['VAB_agro_2021'].str.replace(',', '.').astype(float)
df['VAB_ind_2021'] = df['VAB_ind_2021'].str.replace(',', '.').astype(float)

# %% BARRA LATERAL COM FILTROS
st.sidebar.header("🔍 Filtros de Consulta")

# Filtro 1: Área de Influência
opcoes_area = sorted(df['area_influencia'].dropna().unique())
filtro_area = st.sidebar.multiselect(
    "Área de Influência:",
    options=opcoes_area,
    default=opcoes_area
)

# Filtro 2: Território de Identidade (atualiza de acordo com a área se desejar)
opcoes_territorio = sorted(df[df['area_influencia'].isin(filtro_area)]['territorio_identidade'].dropna().unique())
filtro_territorio = st.sidebar.multiselect(
    "Território de Identidade:",
    options=opcoes_territorio,
    default=opcoes_territorio
)

# Filtro 3: Municípios
opcoes_municipios = sorted(
    df[(df['area_influencia'].isin(filtro_area)) & 
       (df['territorio_identidade'].isin(filtro_territorio))]['municipio'].dropna().unique()
)
filtro_municipios = st.sidebar.multiselect(
    "Municípios:",
    options=opcoes_municipios,
    default=opcoes_municipios
)

# %% APLICAÇÃO DOS FILTROS
df_filtrado = df[
    (df['area_influencia'].isin(filtro_area)) &
    (df['territorio_identidade'].isin(filtro_territorio)) &
    (df['municipio'].isin(filtro_municipios))
].copy()

# Validação para não quebrar gráficos se todos os filtros forem desmarcados
if df_filtrado.empty:
    st.warning("⚠️ Nenhum município corresponde aos filtros selecionados. Por favor, revise a seleção na barra lateral.")
    st.stop()


# %% 1. MAPEAMENTO DE CORES CATEGÓRICAS 
categorias_unicas = sorted(df['area_influencia'].unique())
cores = ['#e15759', '#59a14f', '#4e79a7']
mapa_de_cores = {cat: cores[i % len(cores)] for i, cat in enumerate(categorias_unicas)}

categorias_unicas_terrtorio = sorted(df['territorio_identidade'].unique())
cores_territorio = ['#5B2260', '#384B43', '#B85723', '#FDBD59']
mapa_cores_territorio = {cat: cores_territorio[i % len(cores_territorio)] for i, cat in enumerate(categorias_unicas_terrtorio)}


# %% 2. CONSTRUÇÃO DO MAPA INTERATIVO 
fig = px.choropleth_map(
    df_filtrado, 
    geojson=geojson_bahia,
    locations="codigo_ibge",
    featureidkey="properties.id",
    color="area_influencia",
    color_discrete_map=mapa_de_cores,
    labels={'area_influencia': 'Área de influência'},
    hover_name="municipio",
    hover_data={
        "Pescadores": True,
        "area_influencia": False,
        "codigo_ibge": False,
        "comunidades_quilombolas": True,
        "localidades_indigenas": True,
        "territorio_identidade": True
    },
    zoom=7,
    center={"lat": -12.97, "lon": -38.50},
    map_style="open-street-map",
    opacity=0.7
)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})


# %% 3. GRÁFICO DA QUANTIDADE DE PESCADORES
df_pescadores = df_filtrado.groupby('area_influencia', as_index=False)['Pescadores'].sum()
total_pescadores_filtrado = df_filtrado['Pescadores'].sum()

fig_pescadores = px.bar( 
    df_pescadores, 
    x='Pescadores',
    y='area_influencia',
    title=f'Total de pescadores: {total_pescadores_filtrado:,.0f}'.replace(',', '.'),
    orientation='h',
    color='area_influencia',
    color_discrete_map=mapa_de_cores,
    labels={'area_influencia': 'Área de influência'},
    barmode='group',
    text_auto=True,
    opacity=0.7  
)
fig_pescadores.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 0}, 
                             height=300,
                             bargap=0.0)


# %% 4. GRÁFICO DA QUANTIDADE DE COM. QUILOMBOLAS 
df_quilombos = df_filtrado.groupby('area_influencia', as_index=False)['comunidades_quilombolas'].sum()
total_quilombos_filtrado = df_filtrado['comunidades_quilombolas'].sum()

fig_quilombos = px.bar( 
    df_quilombos, 
    x='comunidades_quilombolas', 
    y='area_influencia', 
    title=f'Total de comunidades quilombolas: {total_quilombos_filtrado:,.0f}'.replace(',', '.'),
    orientation='h',
    color='area_influencia',
    color_discrete_map=mapa_de_cores,
    labels={'area_influencia': 'Área de influência', 'comunidades_quilombolas': 'Total de Comunidades Quilombolas'},
    barmode='group',       
    text_auto=True,        
    opacity=0.7  
)
fig_quilombos.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 0}, 
                            height=300,
                            bargap=0.0)


# %% 5. MAPA INTERATIVO COM AS REGIÕES SOCIOECONOMICAS 
fig_mapa_reg = px.choropleth_map(
    df_filtrado, 
    geojson=geojson_bahia,
    locations="codigo_ibge",
    featureidkey="properties.id",
    color="territorio_identidade",
    color_discrete_map=mapa_cores_territorio,
    labels={'territorio_identidade': 'Território de Identidade'},
    hover_name="municipio",
    hover_data={
        "Pescadores": False,
        "area_influencia": True,
        "codigo_ibge": False,
        "comunidades_quilombolas": False,
        "localidades_indigenas": False,
        "territorio_identidade": True,
        "populacao": True,
        "urbanizacao": True,
        "IDH_2010": True,
        "indice_gini": True,
        "beneficiados_PBF": True,
        "PIB": True,
        "PIB_per_capita": True
    },
    zoom=7,
    center={"lat": -12.97, "lon": -38.50},
    map_style="open-street-map",
    opacity=0.7
)
fig_mapa_reg.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})


# %% 6. TREEMAP com PIB 
fig_tm_PIB_ai = px.treemap(
    df_filtrado,
    path=['municipio', 'PIB'],
    values='PIB_valor', 
    color='area_influencia',
    color_discrete_map=mapa_de_cores,
    hover_data={'PIB': False, 'area_influencia': True}
)
fig_tm_PIB_ai.update_layout(margin=dict(t=50, l=25, r=25, b=25))


# %% 7. TREEMAP POPULAÇÃO [ALTERADO: df -> df_filtrado e título dinâmico]
total_pop_filtrada = df_filtrado['populacao_valor'].sum() if 'populacao_valor' in df_filtrado.columns else 0

fig_pop = px.treemap(
    df_filtrado,
    path=['municipio', 'populacao'],
    values='populacao_valor', 
    color='area_influencia',
    color_discrete_map=mapa_de_cores,
    title=f'População Selecionada: {total_pop_filtrada:,.0f}'.replace(',', '.'),
    hover_data={'area_influencia': True}
)
fig_pop.update_layout(margin=dict(t=50, l=25, r=25, b=25))


# %% 8. GRÁFICO SUNBURST ESTOQUE EMPREGOS FORMAIS [ALTERADO: df -> df_filtrado]
fig_emp = px.sunburst(
    df_filtrado, 
    path=['area_influencia', 'municipio'],
    values='estoque_emprego_formal_valor',
    color='area_influencia',
    color_discrete_map=mapa_de_cores,
    hover_data={
        'area_influencia': False,
        'estoque_emprego_formal': True,
        'saldo_emp_formal': True,
        'estoque_servicos': True,
        'estoque_comercio': True,
        'estoque_industria_2025': True,
        'estoque_agro': True,
        'estoque_const.civil': True
    }
)
fig_emp.update_layout(
    height=500,
    width=700,
    margin=dict(t=10, l=10, r=10, b=10)
)


# %% 9. MAPA DA TX ANALFABETISMO [ALTERADO: df -> df_filtrado]
fig_mapa_edu = px.choropleth_map(
    df_filtrado, 
    geojson=geojson_bahia,
    locations="codigo_ibge",
    featureidkey="properties.id",
    color="analfabetismo_perc",     
    color_continuous_scale='Plasma',
    labels={'territorio_identidade': 'Território de Identidade'},
    hover_name="municipio",
    hover_data={"area_influencia": True, "codigo_ibge": False},
    zoom=7,
    center={"lat": -12.97, "lon": -38.50},
    map_style="open-street-map",
    opacity=0.7
)


# %% 10. MAPA DA TX PESSOAS QUE RECEBEM BPC [ALTERADO: df -> df_filtrado]
fig_mapa_bpc = px.choropleth_map(
    df_filtrado, 
    geojson=geojson_bahia,
    locations="codigo_ibge",
    featureidkey="properties.id",
    color="beneficiados_PBF_perc",     
    color_continuous_scale='Plasma',
    labels={'territorio_identidade': 'Território de Identidade'},
    hover_name="municipio",
    hover_data={"area_influencia": True, "codigo_ibge": False},
    zoom=7,
    center={"lat": -12.97, "lon": -38.50},
    map_style="open-street-map",
    opacity=0.7
)
fig_mapa_bpc.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})


# %% ==============================================================================
# CRIAÇÃO DAS ABAS DO STREAMLIT
# ==============================================================================

aba_principal, aba_socioeconomica = st.tabs(["🗺️ Visão Geral e Comunidades", "📈 Indicadores Socioeconômicos"])

# ==============================================================================
# CONTEÚDO DA ABA 1: VISÃO GERAL
# ==============================================================================
with aba_principal:
    st.subheader("Mapa de Distribuição das Áreas de Influência")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_barras_1, col_barras_2 = st.columns(2)
      
    with col_barras_1:
        st.subheader("🚣 Pescadores por Área de Influência")
        st.plotly_chart(fig_pescadores, use_container_width=True)
    
    with col_barras_2:
        st.subheader("🏘️ Comunidades Quilombolas por Área de Influência")
        st.plotly_chart(fig_quilombos, use_container_width=True)
      
    st.divider()
    
    st.subheader("📊 Notas Estatísticas (Base Geral)")
    st.markdown("<br>", unsafe_allow_html=True)
    
    info_col1, info_col2, info_col3 = st.columns(3)
    
    with info_col1:
        st.markdown("#### 🚣 Pescadores")
        st.markdown(
            f"""
            * **Total no Filtro:** {total_pescadores_filtrado:,.0f}
            * Total geral da base (74.668) representa **42,2%** da Bahia.
            """
        )
            
    with info_col2:
        st.markdown("##### ⛺ Comunidades Indígenas")
        st.markdown(
            """
            * Total de aldeias indígenas = 4 (2 em Camaçari e 2 em Camamú).  
            * Representa **1,1%** do total do estado da Bahia.
            """
        )
        
    with info_col3:
        st.markdown("##### 🏘️ Comunidades Quilombolas")
        st.markdown(
            f"""
            * **Total no Filtro:** {total_quilombos_filtrado:,.0f}
            * Total geral da base (283) representa **15,6%** da Bahia.
            """
        )


# ==============================================================================
# CONTEÚDO DA ABA 2: ANÁLISE SOCIOECONÔMICA
# ==============================================================================
with aba_socioeconomica:
    st.subheader("Territórios de Identidade e Cidades impactadas")
    qtd_municipios_filtrados = df_filtrado['municipio'].nunique()
    st.markdown(f"**{qtd_municipios_filtrados} Cidades selecionadas no filtro atual**")
    st.plotly_chart(fig_mapa_reg, use_container_width=True)
      
    st.subheader("População (2025)")
    st.plotly_chart(fig_pop, use_container_width=True)
    
    st.subheader("Produto Interno Bruto - PIB (2023)")
    st.plotly_chart(fig_tm_PIB_ai, use_container_width=True)
    
    col_mapa_1, col_mapa_2 = st.columns(2)
    
    with col_mapa_1:
        st.subheader("Taxa de Analfabetismo (%)")
        st.plotly_chart(fig_mapa_edu, use_container_width=True)
        
    with col_mapa_2:
        st.subheader("Estoque de Empregos formais - RAIS 2025")
        st.plotly_chart(fig_emp, use_container_width=True)
        
    st.divider()
    
    info_col4, info_col5 = st.columns(2)
    
    with info_col4:
        st.markdown("### 🌍 Recorte Geográfico")
        st.markdown(
            """
            Municípios do Estado da Bahia impactados pelo empreendimento.  
            Áreas de Influência classificadas de acordo com Relatório de Impacto Ambiental - RIMA.  
            **Nomenclatura:** 
            * **ADA:** Área diretamente afetada.
            * **AID:** Área de influência direta.
            * **AII:** Área de influência indireta.
            """
        )
    with info_col5:
        st.markdown("### 📌 Notas Metodológicas")
        st.markdown(
            """
            * **Fonte de Dados - Comunidades quilombolas e aldeias indígenas:** Censo Demográfico IBGE 2022.
            * **Fonte de Dados - Pescadores:** Ministério da Pesca e Aquicultura (Painel Unificado do RGP).
            * **Indicadores socioeconômicos:** SEI Bahia.
            """
        )



