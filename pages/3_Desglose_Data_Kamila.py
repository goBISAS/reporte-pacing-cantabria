import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Desglose de Data", page_icon="🔍", layout="wide")

# ESTILOS PREMIUM GO BIG
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    
    /* Estilos para la tabla */
    .stDataFrame {
        border: 1px solid #333;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Pequeño resaltado de métricas superiores */
    .metric-container {
        background-color: #141414;
        border: 1px solid #262626;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        border-left: 3px solid #d6b58e;
    }
    .metric-title { color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .metric-value { color: #d6b58e; font-size: 24px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 Desglose Granular de Campañas")
st.caption("Filtra, analiza y explora la data diaria de Cantabria Labs (Fuente: Kamila)")

# ==========================================
# EXTRACCIÓN Y LIMPIEZA DE DATOS
# ==========================================
@st.cache_data(ttl=600)
def obtener_desglose_data():
    id_publicacion = "1TQzJuqbBqESer_nGhG5kyl4oMcGVIcWV0Q5xCnlmxFc"
    sheet_enc = urllib.parse.quote("Desglose Data")
    csv_url = f"https://docs.google.com/spreadsheets/d/{id_publicacion}/gviz/tq?tqx=out:csv&sheet={sheet_enc}"
    
    # Aquí sí leemos la primera fila como encabezado (header=0 por defecto en read_csv)
    df = pd.read_csv(csv_url, dtype=str).fillna("")
    
    # Limpiamos las columnas vacías al final que suele exportar Sheets
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # ---------------------------------------------------------
    # MAGIA DE FECHAS: Convertimos el texto a fechas reales
    # ---------------------------------------------------------
    if 'Fecha' in df.columns:
        # Reemplazamos posibles textos vacíos por None temporalmente para parsear
        df['Fecha_Temp'] = df['Fecha'].replace(["", "-", "None"], None)
        # Convertimos forzando a DateTime (asume formato Día/Mes/Año por dayfirst=True)
        df['Fecha_Date'] = pd.to_datetime(df['Fecha_Temp'], errors='coerce', dayfirst=True)
        
    return df

df_base = obtener_desglose_data()

if df_base.empty:
    st.info("No se han encontrado registros en la pestaña 'Desglose Data'.")
else:
    # ==========================================
    # FILTROS LATERALES INTERACTIVOS
    # ==========================================
    st.sidebar.markdown("### ⚙️ Filtros Dinámicos")
    
    df_filtrado = df_base.copy()
    
    # 1. FILTRO DE CALENDARIO (Rango de Fechas)
    if 'Fecha_Date' in df_filtrado.columns and not df_filtrado['Fecha_Date'].isna().all():
        min_date = df_filtrado['Fecha_Date'].min().date()
        max_date = df_filtrado['Fecha_Date'].max().date()
        
        # Componente nativo de Streamlit tipo calendario
        rango_fechas = st.sidebar.date_input(
            "📅 Filtrar por Rango de Fechas:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Aplicamos el filtro de fecha solo si el usuario seleccionó ambas (inicio y fin)
        if len(rango_fechas) == 2:
            start_date, end_date = rango_fechas
            # Filtramos el DataFrame
            mask = (df_filtrado['Fecha_Date'].dt.date >= start_date) & (df_filtrado['Fecha_Date'].dt.date <= end_date)
            df_filtrado = df_filtrado.loc[mask]
    else:
        st.sidebar.warning("⚠️ No se detectó formato de fecha válido en la columna 'Fecha'.")

    # 2. FILTROS EN CASCADA (Campaña y Objetivo)
    if 'Campaña' in df_filtrado.columns:
        campañas_disp = ["Todas"] + sorted([c for c in df_filtrado['Campaña'].unique() if str(c).strip() != ""])
        camp_sel = st.sidebar.selectbox("🎯 Filtrar por Campaña:", options=campañas_disp)
        if camp_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado['Campaña'] == camp_sel]
            
    if 'Objetivo / método de compra' in df_filtrado.columns:
        obj_disp = ["Todos"] + sorted([o for o in df_filtrado['Objetivo / método de compra'].unique() if str(o).strip() != ""])
        obj_sel = st.sidebar.selectbox("📊 Filtrar por Objetivo:", options=obj_disp)
        if obj_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Objetivo / método de compra'] == obj_sel]

    # ==========================================
    # RENDERIZADO DE LA DATA
    # ==========================================
    st.write(f"Mostrando **{len(df_filtrado)}** registros según tus filtros:")
    
    # Mostramos KPIs rápidos de volumen si existen las columnas de Impresiones o Clics
    # Limpiamos todo caracter no numérico para sumar
    try:
        if 'Impresiones' in df_filtrado.columns and 'Clics en el enlace' in df_filtrado.columns:
            tot_imp = pd.to_numeric(df_filtrado['Impresiones'].str.replace(r'[^\d]', '', regex=True), errors='coerce').sum()
            tot_clics = pd.to_numeric(df_filtrado['Clics en el enlace'].str.replace(r'[^\d]', '', regex=True), errors='coerce').sum()
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='metric-container'><div class='metric-title'>Total Impresiones</div><div class='metric-value'>{tot_imp:,.0f}</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-container'><div class='metric-title'>Total Clics</div><div class='metric-value'>{tot_clics:,.0f}</div></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    except Exception as e:
        pass # Si falla el cálculo numérico, simplemente no mostramos los KPIs y pasamos a la tabla

    # Eliminamos las columnas temporales de fecha antes de mostrar la tabla al usuario
    if 'Fecha_Temp' in df_filtrado.columns: df_filtrado = df_filtrado.drop(columns=['Fecha_Temp'])
    if 'Fecha_Date' in df_filtrado.columns: df_filtrado = df_filtrado.drop(columns=['Fecha_Date'])

    # Renderizamos la matriz de datos completa y limpia
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
