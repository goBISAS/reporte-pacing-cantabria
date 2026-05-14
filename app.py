import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Medivelius - Reporte Corporativo",
    page_icon="medivelius_logo.jpg",
    layout="wide"
)

# ESTILOS PERSONALIZADOS (Identidad Medivelius)
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #004b49; } /* Verde oscuro profesional */
    h1, h2 { color: #004b49; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stSidebar { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE AYUDA ---
def get_csv_url(url):
    return url.replace('/edit?gid=', '/export?format=csv&gid=').split('#')[0]

def encontrar_columna(lista_cols, palabras_clave):
    for col in lista_cols:
        if all(p.lower() in str(col).lower() for p in palabras_clave):
            return col
    return None

# --- CONFIGURACIÓN DE DATOS (4 Marcas) ---
diccionario_marcas = {
    "Cantabria Labs": "https://docs.google.com/spreadsheets/d/18DGFtWV_BAOLjxBlmImhZ_8Xuilc4CKK_bNZIHQnCcU/edit?gid=1210187329",
    "Uriage": "https://docs.google.com/spreadsheets/d/1XnkC6ONKaJm03k2qAtQmcwuoRrBSh6uXYsdewrlwjK0/edit?gid=1220251411",
    "Sensilis": "https://docs.google.com/spreadsheets/d/1e8ZkA61crydoXKdA3lQtMkMMYDHutSR7t6PK-8GvPo0/edit?gid=1519706032",
    "Apivita": "https://docs.google.com/spreadsheets/d/1r4KycpStMWvpF1fOzMgmLBjgVQ8dX8WTpgtKWgNm2lM/edit?gid=0"
}
url_gestion = "https://docs.google.com/spreadsheets/d/15eeJ2GBPR5XnB71crLoBd4JVYrj5NBVkrexgSBBtf2M/edit?gid=0"

# --- MENÚ LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("medivelius_logo.jpg", use_column_width=True)
    st.markdown("---")
    st.header("Control de Marcas")
    marca_seleccionada = st.selectbox(
        "Seleccione la marca para ver el reporte:",
        options=list(diccionario_marcas.keys())
    )
    st.markdown("---")
    st.info(f"Visualizando: **{marca_seleccionada}**")

# --- CUERPO DEL REPORTE ---
st.title(f"📈 Dashboard de Rendimiento: {marca_seleccionada}")
url_pacing_activa = diccionario_marcas[marca_seleccionada]

try:
    # 1. CARGA DE DATOS DE LA MARCA SELECCIONADA
    df_header = pd.read_csv(get_csv_url(url_pacing_activa), nrows=5, header=None)
    presupuesto_mensual = df_header.iloc[1, 2] 

    df_pacing = pd.read_csv(get_csv_url(url_pacing_activa), skiprows=5)
    df_pacing.columns = [str(c).strip() for c in df_pacing.columns]

    # 2. MÉTRICAS DE CABECERA
    fila_total = df_pacing[df_pacing['Campaign'].str.contains('TOTAL', na=False)].iloc[0]
    gasto_total = fila_total['Spend (COP)']
    
    col_fecha = encontrar_columna(df_pacing.columns, ['Actualizacion', 'Pacing']) or 'Actualización Pacing'
    fecha_update = df_pacing[col_fecha].dropna().iloc[-1]
    dias_hoy = datetime.now().day

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Presupuesto Mes", f"{presupuesto_mensual}")
    with c2:
        st.metric("Gasto al Día", f"{gasto_total}")
    with c3:
        st.metric("Días del Mes", f"{dias_hoy}")

    st.success(f"📅 Última actualización de datos de {marca_seleccionada}: {fecha_update}")
    st.divider()

    # 3. SECCIÓN VENTAS & DERMARKET
    st.header(f"🎯 Resultados: Ventas & Dermarket ({marca_seleccionada})")
    mask = df_pacing['Campaign'].str.contains('Ventas|dermarket', case=False, na=False)
    df_v = df_pacing[mask].copy()

    if not df_v.empty:
        col_res = encontrar_columna(df_v.columns, ['Platform', 'Conversions'])
        col_cpa = encontrar_columna(df_v.columns, ['CPA'])
        
        cols_finales = ['Campaign']
        nombres_renombrar = {'Campaign': 'Campaña'}
        
        if col_res:
            cols_finales.append(col_res)
            nombres_renombrar[col_res] = 'Ventas / Resultado'
        if col_cpa:
            cols_finales.append(col_cpa)
            nombres_renombrar[col_cpa] = 'Costo x Resultado'
            
        df_display = df_v[cols_finales].rename(columns=nombres_renombrar)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No se detectan campañas con palabras clave para {marca_seleccionada}.")

    # 4. TABLA DE GESTIÓN (General para el grupo)
    st.divider()
    st.header("📅 Gestión General Medivelius")
    df_gest = pd.read_csv(get_csv_url(url_gestion))
    df_res_gest = df_gest[['Nombre de actividad', 'Fecha de ejecución']].dropna()
    st.table(df_res_gest)

except Exception as e:
    st.error(f"Error al cargar datos de {marca_seleccionada}: {e}")

st.caption(f"Medivelius Group Dashboard | Desarrollado por goBIG | {datetime.now().strftime('%Y')}")
