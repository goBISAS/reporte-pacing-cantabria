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

# Función para encontrar columnas aunque el nombre varíe un poco
def encontrar_columna(lista_cols, palabras_clave):
    for col in lista_cols:
        if all(p.lower() in str(col).lower() for p in palabras_clave):
            return col
    return None

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

    # Limpieza inicial de nombres
    df_pacing.columns = [str(c).strip() for c in df_pacing.columns]

    # --- MÉTRICAS DE CABECERA ---
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

    st.info(f"📅 Última actualización de datos: {fecha_update}")
    st.divider()

    # --- SECCIÓN VENTAS & DERMARKET ---
    st.header("🎯 Resultados: Ventas & Dermarket")
    
    mask = df_pacing['Campaign'].str.contains('Ventas|dermarket', case=False, na=False)
    df_v = df_pacing[mask].copy()

    if not df_v.empty:
        # BUSQUEDA INTELIGENTE DE LAS COLUMNAS O Y R
        col_res = encontrar_columna(df_v.columns, ['Platform', 'Conversions'])
        col_cpa = encontrar_columna(df_v.columns, ['CPA'])
        
        # Construimos la tabla con lo que encontremos
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
        st.warning("No se detectan campañas con 'Ventas' o 'Dermarket'.")

    # --- MÉTODOS DE COMPRA ---
    with st.expander("🔗 Ver Métodos de Compra"):
        col_metodo = encontrar_columna(df_pacing.columns, ['Official', 'Conversions'])
        if col_metodo:
            metodos = df_pacing[col_metodo].unique()
            st.write(", ".join([str(m) for m in metodos if pd.notna(m) and str(m).strip() != str(col_metodo)]))

    st.divider()

    # --- RESUMEN DE GESTIÓN ---
    st.header("📅 Gestión del Cliente")
    df_res_gest = df_gest[['Nombre de actividad', 'Fecha de ejecución']].dropna()
    st.table(df_res_gest)

except Exception as e:
    st.error(f"Error técnico: {e}")

st.caption("goBIG Dashboard | Automatizado 05:00 AM")
