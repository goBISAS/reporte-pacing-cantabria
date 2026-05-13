import streamlit as st
import pandas as pd

# CONFIGURACIÓN DE PÁGINA (Optimizado para visualización móvil/PWA) [cite: 27, 28]
st.set_page_config(page_title="goBIG - Cantabria Labs", layout="wide", initial_sidebar_state="collapsed")

# ESTILOS PARA SIMULAR APP MÓVIL
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 26px; font-weight: bold; color: #1d3557; }
    .stTable { font-size: 14px; }
    h1, h2, h3 { color: #457b9d; }
    </style>
    """, unsafe_allow_html=True)

# FUNCIÓN PARA TRANSFORMAR LINKS DE GOOGLE SHEETS A CSV
def get_csv_url(url):
    return url.replace('/edit?gid=', '/export?format=csv&gid=')

# LINKS DE LOS DOCUMENTOS PROPORCIONADOS [cite: 13, 24]
url_pacing = "https://docs.google.com/spreadsheets/d/18DGFtWVNZlHQnCcU/edit?gid=1210187329"
url_gestion = "https://docs.google.com/spreadsheets/d/15eeJ2GBPR5XnB71crLoBd4JVYrj5NBVkrexgSBBtf2M/edit?gid=0"

st.title("🚀 Reporte de Paid Media")
st.subheader("Cliente: Cantabria Labs")

try:
    # 1. CARGA DE DATOS DEL PACING [cite: 13]
    # Extraemos el presupuesto del header (Fila 2, Celda C) [cite: 6, 7]
    df_header = pd.read_csv(get_csv_url(url_pacing), nrows=5, header=None)
    presupuesto_mensual = df_header.iloc[1, 2] 

    # Cargamos la data real desde la fila 6 [cite: 8, 11]
    df_pacing = pd.read_csv(get_csv_url(url_pacing), skiprows=5)
    
    # 2. CARGA DE DATOS DE GESTIÓN [cite: 24]
    df_gest = pd.read_csv(get_csv_url(url_gestion))

    # --- MÉTRICAS PRINCIPALES --- [cite: 18]
    # Gasto acumulado (Buscamos la fila TOTAL en la columna Campaign) [cite: 10]
    fila_total = df_pacing[df_pacing['Campaign'] == 'TOTAL'].iloc[0]
    gasto_total = fila_total['Spend (COP)']
    
    # Fecha de actualización (Columna S)
    fecha_actualizacion = df_pacing['Actualización Pacing'].dropna().iloc[-1]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Presupuesto del Mes", f"{presupuesto_mensual}")
    with col2:
        st.metric("Gasto Acumulado", f"{gasto_total}")
    
    st.info(f"📅 Última actualización del reporte: {fecha_actualizacion}")
    st.divider()

    # --- SECCIÓN VENTAS & DERMARKET --- [cite: 19]
    st.header("🎯 Resultados: Ventas & Dermarket")
    
    # Filtramos por palabras clave en el nombre de la campaña [cite: 19]
    filtro_campañas = df_pacing['Campaign'].str.contains('Ventas|dermarket', case=False, na=False)
    df_ventas_dermarket = df_pacing[filtro_campañas].copy()

    # Mostramos únicamente Ventas (Resultado de Columna O) y Costo por Resultado (Columna R) [cite: 19]
    if not df_ventas_dermarket.empty:
        resumen_v = df_ventas_dermarket[['Campaign', 'Platform Conversions', 'CPA']]
        resumen_v.columns = ['Campaña', 'Ventas (Resultado)', 'Costo por Resultado']
        st.dataframe(resumen_v, use_container_width=True, hide_index=True)
    else:
        st.warning("No se encontraron campañas activas con las palabras clave 'Ventas' o 'Dermarket'.")

    # --- MÉTODOS DE COMPRA --- [cite: 18]
    with st.expander("🔍 Ver Métodos de Compra (Official Conversions)"):
        metodos = df_pacing['Official Conversions'].unique()
        st.write(", ".join([str(m) for m in metodos if pd.notna(m) and m != 'Official Conversions']))

    st.divider()

    # --- RESUMEN DE GESTIÓN --- [cite: 20]
    st.header("📅 Resumen de Gestión")
    # Nombre de actividad (Col A) y Fecha de ejecución (Col B) [cite: 21, 26]
    df_resumen_gest = df_gest[['Nombre de actividad', 'Fecha de ejecución']].dropna()
    st.table(df_resumen_gest)

except Exception as e:
    st.error(f"Error al conectar con los datos: {e}")
    st.info("Asegúrate de que los archivos de Google Sheets tengan el acceso compartido como 'Cualquier persona con el enlace'.")

st.caption("Dashboard generado por goBIG - Actualización diaria 05:00 AM")
