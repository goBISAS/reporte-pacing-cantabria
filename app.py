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
    .stAlert { border-radius: 10px; }
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
    df_header = pd.read_csv(get_csv_url(url_pacing), nrows=5, header=None)
    presupuesto_mensual = df_header.iloc[1, 2] 

    df_pacing = pd.read_csv(get_csv_url(url_pacing), skiprows=5)
    df_gest = pd.read_csv(get_csv_url(url_gestion))

    # --- LIMPIEZA AGRESIVA DE COLUMNAS ---
    # Eliminamos espacios, saltos de línea y convertimos a texto limpio
    df_pacing.columns = [str(c).strip().replace('\n', ' ') for c in df_pacing.columns]
    df_gest.columns = [str(c).strip().replace('\n', ' ') for c in df_gest.columns]

    # --- MÉTRICAS DE CABECERA ---
    # Buscamos la fila TOTAL (Columna B / Campaign)
    fila_total = df_pacing[df_pacing['Campaign'].str.contains('TOTAL', na=False)].iloc[0]
    gasto_total = fila_total['Spend (COP)']
    
    # Buscamos columna de fecha (con o sin tilde)
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
    
    # Filtramos campañas
    mask = df_pacing['Campaign'].str.contains('Ventas|dermarket', case=False, na=False)
    df_v = df_pacing[mask].copy()

    if not df_v.empty:
        # Usamos una forma segura de seleccionar columnas por si el nombre varía mínimamente
        col_resultado = 'Platform Conversions'
        col_cpa = 'CPA'
        
        # Verificamos si existen antes de mostrar
        columnas_a_mostrar = ['Campaign']
        if col_resultado in df_v.columns: columnas_a_mostrar.append(col_resultado)
        if col_cpa in df_v.columns: columnas_a_mostrar.append(col_cpa)
        
        df_v_display = df_v[columnas_a_mostrar]
        
        # Nombres amigables para el cliente
        nombres_columnas = {'Campaign': 'Campaña', 'Platform Conversions': 'Ventas / Resultado', 'CPA': 'Costo x Resultado'}
        df_v_display = df_v_display.rename(columns=nombres_columnas)
        
        st.dataframe(df_v_display, use_container_width=True, hide_index=True)
    else:
        st.warning("No se detectan campañas con 'Ventas' o 'Dermarket' actualmente.")

    # --- MÉTODOS DE COMPRA ---
    with st.expander("🔗 Ver Métodos de Compra"):
        col_metodo = 'Official Conversions'
        if col_metodo in df_pacing.columns:
            metodos = df_pacing[col_metodo].unique()
            st.write(", ".join([str(m) for m in metodos if pd.notna(m) and str(m).strip() != 'Official Conversions']))

    st.divider()

    # --- RESUMEN DE GESTIÓN ---
    st.header("📅 Gestión del Cliente")
    # Aseguramos que los nombres coincidan con el Excel de gestión
    df_res_gest = df_gest[['Nombre de actividad', 'Fecha de ejecución']].dropna()
    st.table(df_res_gest)

except Exception as e:
    st.error(f"Nota técnica: {e}")
    # Si falla, mostramos las columnas reales para diagnosticar
    if 'df_pacing' in locals():
        with st.expander("Ayuda técnica: Columnas detectadas"):
            st.write(list(df_pacing.columns))

st.caption("goBIG Dashboard | Automatizado 05:00 AM")
