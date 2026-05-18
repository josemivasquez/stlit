import streamlit as st
import pandas as pd

import os
import subprocess
import sys


import plotly.graph_objects as go
import plotly.express as px # Ahora ya debería funcionar
import streamlit as st

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="AirMajoro Dashboard", layout="wide")

# 3. CARGA DE DATOS
@st.cache_data
def load_data():
    try:
        df_cli = pd.read_csv('Fact_DetalleCliente.csv')
        df_viaje = pd.read_csv('Fact_Viaje.csv')
        df_costos = pd.read_csv('Fact_DetalleCostos.csv')
        df_cal = pd.read_csv('Dim_Calendario.csv')
        df_vend = pd.read_csv('Dim_Vendedor.csv')
        df_aero = pd.read_csv('Dim_Aeronave.csv')
        df_zona = pd.read_csv('Dim_Zona.csv')

        df = df_cli.merge(df_viaje, on='id_viaje')
        df = df.merge(df_cal, on='id_fecha')
        df = df.merge(df_vend, on='id_vendedor')
        df = df.merge(df_aero, on='id_aeronave')
        df = df.merge(df_zona, on='id_zona')
        
        c_viaje = df_costos.groupby('id_viaje')['monto_costo'].sum().reset_index()
        df = df.merge(c_viaje, on='id_viaje', how='left').fillna(0)
        df['utilidad'] = df['ingreso_bruto'] - df['monto_costo']
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df_master = load_data()


col_t, col_l = st.columns([1, 1])
with col_t:
    st.markdown(
        '''
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <h1 style="color:#2570bb; font-family: Poppins, 'Poppins Fallback', sans-serif;">Dashboard de ingresos</h1>
        ''',
        unsafe_allow_html=True,
    )

with col_l:
    a, b, c = st.columns([1, 1, 1])
    with b:
        st.image("logo.png", width=400)



# FILA DE INDICADORES
k1, k2, g1, g2, k3 = st.columns([1, 1, 1, 1, 1])

with g2:
    years = sorted(df_master['anio'].unique(), reverse=True)
    selected_year = st.selectbox("Year", years)

df_filtered = df_master[df_master['anio'] == selected_year]

ing_total = df_filtered['ingreso_bruto'].sum()
tix_total = df_filtered['unidades_vendidas'].sum()
util_total = df_filtered['utilidad'].sum()
tkt_prom = ing_total / tix_total if tix_total > 0 else 0
rentab = (util_total / ing_total) * 100 if ing_total > 0 else 0

st.markdown("""
    <style>
    /* Estilo para el título (Label) */
    [data-testid="stMetricLabel"] p {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #555555 !important;
    }
    /* Estilo para el número (Value) */
    [data-testid="stMetricValue"] div {
        font-size: 32px !important;
        color: #555555 !important;
    }
    """, unsafe_allow_html=True)


with k1:
    st.metric("Ingreso Total", f"{ing_total/1e6:.2f}M")

with k2:
    st.metric("Unidades Tickets", f"{tix_total/1e3:.0f}K")


with g1:
    st.metric("Ticket promedio", f"{tkt_prom:.2f}")


g1, g2 = st.columns([1, 1])
ALTURA_GRAFICOS = 350 

df_pie = df_filtered.groupby('modelo')['ingreso_bruto'].sum().reset_index()

# 2. Crear el gráfico
fig_pie = px.pie(
    df_pie, 
    values='ingreso_bruto', 
    names='modelo',
    hole=0.5, # Esto lo hace "Donut", se ve más moderno que la tarta completa
    color_discrete_sequence=px.colors.qualitative.Prism # Colores profesionales
)

# 3. Estilizar etiquetas y bordes
fig_pie.update_traces(
    textposition='inside', 
    textinfo='percent+label',
    marker=dict(line=dict(color='#0e1117', width=2)) # Borde del color del fondo
)

# 4. Diseño transparente y sin márgenes desperdiciados
fig_pie.update_layout(
    showlegend=False, # Ocultamos leyenda porque ya está la etiqueta dentro
    margin=dict(t=10, b=10, l=10, r=10),
    paper_bgcolor='rgba(0,0,0,0)', # Fondo transparente
    template="plotly_dark",
    height=ALTURA_GRAFICOS
)



with g1:
    st.markdown("### Ingreso por aeronave")
    st.plotly_chart(fig_pie, width='stretch', config={'displayModeBar': False})

df_line = df_filtered.groupby(['trimestre', 'zona'])['utilidad'].sum().reset_index()
df_line['Quarter'] = df_line['trimestre'].apply(lambda x: f"Qtr {x}")

color_map = {
    "Asia": "#5A9E53", 
    "Europa": "#3E3B6D", 
    "Latam": "#9B924A", 
    "Norteamérica": "#5E2116"
}

# 2. Crear el gráfico
fig_line = px.line(
    df_line, 
    x='Quarter', 
    y='utilidad', 
    color='zona',
    markers=True, # Añade los puntitos en cada trimestre
    color_discrete_map=color_map,
    template="plotly_dark"
)

# 3. Limpiar el diseño (Layout)
fig_line.update_layout(
    height=300, # Altura compacta
    margin=dict(t=10, b=40, l=40, r=10),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.4,
        xanchor="center",
        x=0.5,
        title=None,
        font=dict(color="#1a1a1a", size=12) 
    )
)

# 4. Arreglar los Ejes (Lo más importante para la estética)
fig_line.update_xaxes(
    tickangle=0,        # Etiquetas horizontales (Qtr 1, Qtr 2...)
    showgrid=False,     # Sin líneas verticales para que sea más limpio
    title=None          # Quitamos el título "Quarter" que ya se entiende
)

fig_line.update_yaxes(
    tickformat=".1s",   # Convierte -2,500,000 en -2.5M
    gridcolor='rgba(255,255,255,0.1)', # Rejilla muy sutil
    title=None          # Quitamos el título "utilidad"
)

with g2:
    st.markdown("### Utilidad por zona")
    st.plotly_chart(fig_line, width='stretch', config={'displayModeBar': False})

# 7. VENDEDORES
df_v = df_filtered.groupby('nombre_vendedor')['ingreso_bruto'].sum().reset_index().sort_values('ingreso_bruto', ascending=False)
fig_bar = px.bar(df_v, x='nombre_vendedor', y='ingreso_bruto', template="plotly_dark")
fig_bar.update_traces(marker_color='#a52a2a')

# Configuración de tipografía Open Sans, tamaño 20 para los ejes
fig_bar.update_layout(
    title={
        'text': "Ingreso Bruto por Vendedor",
        'font': {
            'family': "Open Sans, sans-serif",
            'size': 20
        }
    },
    # Configuración del Eje X (Nombres de vendedores)
    xaxis={
        'title': None,  # Mantiene tu configuración de omitir el título del eje
        'tickfont': {
            'family': "Open Sans, sans-serif",
            'size': 20
        }
    },
    # Configuración del Eje Y (Valores numéricos)
    yaxis={
        'title': None,  # Mantiene tu configuración de omitir el título del eje
        'tickfont': {
            'family': "Open Sans, sans-serif",
            'size': 20
        }
    },
    paper_bgcolor='rgba(0,0,0,0)',
    height=ALTURA_GRAFICOS
)

st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
st.markdown(
    """
    <style>
    /* Ocultar el menú de tres puntos (MainMenu) */
    #MainMenu {visibility: hidden;}
    
    /* Ocultar el pie de página (footer) */
    footer {visibility: hidden;}
    
    /* Ocultar el botón de "Deploy" si también se requiere */
    .stDeployButton {display: none;}
    
    /* Ocultar la barra de encabezado superior por completo (opcional) */
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)
st.set_page_config(layout="wide")