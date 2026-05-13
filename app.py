import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="goBIG - Cantabria Labs", layout="wide")

# ESTILOS MÓVIL/PWA
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1d3557; }
    h1, h2 { color: #457b9d; }
    </style>
    """, unsafe_allow_html=True)

def get_csv_url(url):
    return url.replace('/edit?gid=', '/export?format=csv&gid=').split('#')[0]

url_pacing = "https://docs.google.com/spreadsheets/d/18DGFtWV_BAOLjxBlmImhZ_8Xuilc4CKK_bNZIHQnCcU/edit?gid=1210187329"
url_gestion = "https://docs.google.com/spreadsheets/d/15eeJ2GBPR5XnB71crLoBd4JVYrj5NBVkrexgSBBtf2M/edit?gid=0"

st.title("🚀 Reporte de Paid Media")
st.subheader("Cliente: Cantabria Labs")

try:
    # 1. CARGA DE DATOS
    # Presupuesto desde el Header (Fila 2, Celda C)
    df_header = pd.read_csv(get_csv_url(url_pacing), nrows=5, header=None)
    presupuesto_mensual = df_header.iloc[1, 2] 

    # Datos principales desde la fila 6
    df_pacing = pd.read_csv(get_csv_url(url_pacing), skiprows=5)
    df_gest = pd.read_csv(get_csv_url(url_gestion))

    # --- LIMPIEZA DE COLUMNAS ---
    # Esto elimina espacios invisibles que suelen causar errores
    df_pacing.columns = df_pacing.columns.str.strip()

    # --- MÉTRICAS DE CABECERA ---
    # Gasto acumulado (Fila TOTAL)
    fila_total = df_pacing[df_pacing['Campaign'] == 'TOTAL'].iloc[0]
    gasto_total = fila_total['Spend (COP)']
    
    # BUSCAR FECHA DE ACTUALIZACIÓN (Columna S)
    # Probamos con y sin tilde para estar seguros
    col_fecha = 'Actualizacion Pacing' if 'Actualizacion Pacing' in df_pacing.columns else 'Actualización Pacing'
    fecha_update = df_pacing[col_fecha].dropna().iloc[-1]

    dias_hoy = datetime.now().day

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Presupuesto Mes", f"{presupuesto_mensual}")
    with c2:
        st.metric("Gasto al Día", f"{gasto_total}")
    with c3:
        st.metric("Días del Mes", f"{dias_hoy}")

    st.info(f"📅 Última actualización de datos: {fecha_update}")
    st.divider()

    # --- SECCIÓN VENTAS & DERMARKET ---
    st.header("🎯 Resultados: Ventas & Dermarket")
    
    mask = df_pacing['Campaign'].str.contains('Ventas|dermarket', case=False, na=False)
    df_v = df_pacing[mask].copy()

    if not df_v.empty:
        # Columna O = Platform Conversions, Columna R = CPA
        df_v_display = df_v[['Campaign', 'Platform Conversions', 'CPA']]
        df_v_display.columns = ['Campaña', 'Ventas / Resultado', 'Costo x Resultado']
        st.dataframe(df_v_display, use_container_width=True, hide_index=True)
    else:
        st.warning("No se detectan campañas con 'Ventas' o 'Dermarket' actualmente.")

    # --- MÉTODOS DE COMPRA ---
    with st.expander("🔗 Ver Métodos de Compra"):
        metodos = df_pacing['Official Conversions'].unique()
        st.write(", ".join([str(m) for m in metodos if pd.notna(m) and m != 'Official Conversions']))

    st.divider()

    # --- RESUMEN DE GESTIÓN ---
    st.header("📅 Gestión del Cliente")
    df_res_gest = df_gest[['Nombre de actividad', 'Fecha de ejecución']].dropna()
    st.table(df_res_gest)

except Exception as e:
    st.error(f"Error técnico: {e}")
    st.info("Nota: Revisa si el nombre de la columna en el Excel es 'Actualizacion Pacing' o 'Actualización Pacing'.")

st.caption("goBIG Dashboard | Automatizado 05:00 AM")
