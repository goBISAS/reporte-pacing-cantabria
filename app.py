import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import urllib.parse
import re

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Cantabria - Multibrand Paid Media Dashboard",
    page_icon="⚡",
    layout="wide"
)

# ESTILOS PREMIUM OSCURO
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    [data-testid="stMetricValue"] { font-size: 32px; color: #d6b58e !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #f5f5f5 !important; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    .stSidebar { background-color: #1a1a1a; border-right: 1px solid #333; }
    .stPlotlyChart { border: 1px solid #333; border-radius: 8px; background-color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# --- MAPEO DE MARCAS CON LAS URLS CONFIRMADAS ---
DICCIONARIO_MARCAS = {
    "Uriage": "https://docs.google.com/spreadsheets/d/1XnkC6ONKaJm03k2qAtQmcwuoRrBSh6uXYsdewrlwjK0/",
    "Sensilis": "https://docs.google.com/spreadsheets/d/1e8ZkA61crydoXKdA3lQtMkMMYDHutSR7t6PK-8GvPo0/",
    "Apivita": "https://docs.google.com/spreadsheets/d/1r4KycpStMWvpF1fOzMgmLBjgVQ8dX8WTpgtKWgNm2lM/",
    "Cantabria Labs": "https://docs.google.com/spreadsheets/d/18DGFtWV_BAOLjxBlmImhZ_8Xuilc4CKK_bNZIHQnCcU/"
}

# --- LÓGICA HISTÓRICA DE MESES ---
def obtener_meses_disponibles():
    meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    start_year, start_month = 2026, 5
    now = datetime.now()
    lista = []
    ano, mes = start_year, start_month
    while (ano < now.year) or (ano == now.year and mes <= now.month):
        lista.append(f"{meses_es[mes-1]} {ano}")
        if mes == 12:
            mes = 1
            ano += 1
        else:
            mes += 1
    return list(reversed(lista))

def query_sheet_data(url, mes_str):
    # Tolera variantes como "Mayo 2026" y "1 Mayo 2026" de Uriage
    variantes_pestaña = [mes_str, f"1 {mes_str}", mes_str.title(), mes_str.lower()]
    id_publicacion = url.split("/d/")[1].split("/")[0]
    
    for pestaña in variantes_pestaña:
        try:
            sheet_enc = urllib.parse.quote(pestaña)
            csv_url = f"https://docs.google.com/spreadsheets/d/{id_publicacion}/gviz/tq?tqx=out:csv&sheet={sheet_enc}"
            df = pd.read_csv(csv_url, header=None, dtype=str)
            if not df.empty:
                return df, pestaña
        except:
            continue
    return None, None

def limpiar_monto_numerico(valor_str):
    try:
        limpio = re.sub(r'[^\d.-]', '', str(valor_str))
        return float(limpio) if limpio else 0.0
    except:
        return 0.0

# --- SIDEBAR CONTROL ---
meses_disponibles = obtener_meses_disponibles()
with st.sidebar:
    st.markdown("## 📊 Control de Paid Media")
    st.write("Grupo: **Cantabria**")
    st.markdown("---")
    mes_seleccionado = st.selectbox("📅 Seleccione el Mes de Reporte:", options=meses_disponibles)
    st.markdown("---")
    marcas_disponibles = ["Todas las Marcas"] + list(DICCIONARIO_MARCAS.keys())
    marca_seleccionada = st.selectbox("🧴 Filtrar por Marca:", options=marcas_disponibles)

# --- PROCESAMIENTO MULTI-DOCUMENTO ---
campañas_consolidadas = []
totales_presupuesto = {}
fechas_actualizacion = {}
errores_reportados = []

for marca, url_base in DICCIONARIO_MARCAS.items():
    if marca_seleccionada != "Todas las Marcas" and marca != marca_seleccionada:
        continue
        
    df_raw, pestaña_detectada = query_sheet_data(url_base, mes_seleccionado)
    
    if df_raw is None:
        errores_reportados.append(f"No se encontró la pestaña de **{mes_seleccionado}** en el documento de **{marca}**.")
        continue
        
    df_raw = df_raw.fillna('')
    
    try:
        # 1. RADAR FLEXIBLE EN COLUMNA A: Buscar fila de inicio de tabla
        idx_header = None
        for i, row in df_raw.iterrows():
            valores_fila = [str(x).lower() for x in row.tolist()]
            if any(k in val for val in valores_fila for k in ['campaign', 'campaña', 'canal', 'ppto mensual']):
                idx_header = i
                break
        
        if idx_header is None:
            errores_reportados.append(f"Estructura de tabla no identificada en **{marca}** ({pestaña_detectada}).")
            continue

        # 2. LECTURA LINEAL DEL PRESUPUESTO
        presupuesto_marca = 0.0
        for i in range(idx_header):
            fila = df_raw.iloc[i].astype(str).tolist()
            for j, celda in enumerate(fila):
                celda_limpia = celda.lower().strip()
                if 'approved' in celda_limpia or 'aprobado' in celda_limpia:
                    if j + 1 < len(fila) and fila[j+1].strip() not in ['', 'nan', '<na>']:
                        presupuesto_marca = limpiar_monto_numerico(fila[j+1])
                    break
            if presupuesto_marca > 0:
                break
        
        totales_presupuesto[marca] = presupuesto_marca

        # 3. Construir la tabla limpia de campañas
        df_pacing = df_raw.iloc[idx_header + 1:].copy()
        nombres_seguros = []
        for i, c in enumerate(df_raw.iloc[idx_header].tolist()):
            nombre = re.sub(r'\s+', ' ', str(c)).strip()
            if nombre == '': nombre = f"Columna_{i}"
            nombres_seguros.append(nombre)
        df_pacing.columns = nombres_seguros

        # Mapeado dinámico por aproximación de nombres
        col_camp = next((c for c in df_pacing.columns if 'campaign' in c.lower() or 'campaña' in c.lower()), df_pacing.columns[1])
        col_medio = next((c for c in df_pacing.columns if 'channel' in c.lower() or 'platform' in c.lower() or 'canal' in c.lower()), df_pacing.columns[0])
        col_spend = next((c for c in df_pacing.columns if 'spend' in c.lower() or 'gasto' in c.lower() or 'cop' in c.lower() or 'invers' in c.lower()), None)
        col_tipo = next((c for c in df_pacing.columns if 'official' in c.lower() or 'conversions' in c.lower() or 'objetivo' in c.lower()), None)
        col_res = next((c for c in df_pacing.columns if 'resultados' in c.lower() or 'results' in c.lower()), None)
        col_cpa = next((c for c in df_pacing.columns if 'cpa' in c.lower()), None)
        col_fecha = next((c for c in df_pacing.columns if 'actualizaci' in c.lower() or 'pacing' in c.lower() or 'fecha' in c.lower()), df_pacing.columns[-1])

        if not col_spend:
            col_spend = df_pacing.columns[7] if len(df_pacing.columns) > 7 else df_pacing.columns[-1]

        # Limpieza y filtrado estructural de las filas
        df_limpio = df_pacing.copy()
        df_limpio = df_limpio[df_limpio[col_camp].str.strip() != '']
        df_limpio = df_limpio[~df_limpio[col_camp].str.upper().str.contains('TOTAL')]
        df_limpio = df_limpio[df_limpio[col_camp].str.lower() != 'campaign']

        df_limpio[col_medio] = df_limpio[col_medio].replace('', pd.NA).ffill().fillna('Sin Medio')
        df_limpio[col_spend] = df_limpio[col_spend].str.replace(r'[^\d.-]', '', regex=True)
        df_limpio[col_spend] = pd.to_numeric(df_limpio[col_spend], errors='coerce').fillna(0)

        if col_tipo: df_limpio['Objetivo_Final'] = df_limpio[col_tipo].replace('', 'Sin Objetivo')
        else: df_limpio['Objetivo_Final'] = 'General'

        df_limpio['Resultados_Final'] = df_limpio[col_res] if col_res else 'N/D'
        df_limpio['CPA_Final'] = df_limpio[col_cpa] if col_cpa else 'N/D'

        # Extracción segura de la última fecha registrada en la columna detectada
        fechas_validas = df_limpio[col_fecha].astype(str).str.strip()
        fechas_validas = fechas_validas[(fechas_validas != '') & (~fechas_validas.str.lower().str.contains('pacing|actualiz|fecha'))]
        fechas_actualizacion[marca] = fechas_validas.iloc[-1] if not fechas_validas.empty else "N/D"

        # Guardar marca y consolidar
        df_limpio['Marca'] = marca
        df_limpio = df_limpio.rename(columns={col_medio: 'Medio', col_camp: 'Campaña', col_spend: 'Gasto'})
        campañas_consolidadas.append(df_limpio[['Marca', 'Medio', 'Campaña', 'Gasto', 'Objetivo_Final', 'Resultados_Final', 'CPA_Final']])

    except Exception as e:
        errores_reportados.append(f"Error procesando los datos de **{marca}**: {str(e)}")

# --- RENDERIZADO ---
if campañas_consolidadas:
    df_master = pd.concat(campañas_consolidadas, ignore_index=True)
    presupuesto_total_global = sum(totales_presupuesto.values())
    gasto_total_global = df_master['Gasto'].sum()
    
    st.title(f"⚡ Dashboard Gerencial Cantabria: {mes_seleccionado.title()}")
    if marca_seleccionada != "Todas las Marcas":
        st.subheader(f"Foco en la marca: {marca_seleccionada}")

    # KPIs Superiores
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Presupuesto Configurado", f"${presupuesto_total_global:,.0f}")
    with c2: st.metric("Inversión Ejecutada Total", f"${gasto_total_global:,.0f}")
    with c3:
        if mes_seleccionado == meses_disponibles[0]:
            st.metric("Día de Medición", f"Día {datetime.now().day}")
        else:
            st.metric("Estado del Mes", "Cerrado")

    # Módulo expandible de sincronizaciones
    with st.expander("🔗 Estado de Conexión de los Documentos"):
        for m in totales_presupuesto.keys():
            st.write(f"✅ **{m}**: Sincronizado | Presupuesto: ${totales_presupuesto[m]:,.0f} | Último registro: {fechas_actualizacion.get(m, 'N/D')}")

    if errores_reportados:
        for err in errores_reportados:
            st.warning(err)
            
    st.divider()

    # --- GRÁFICA TREEMAP MULTINIVEL ---
    st.header("📊 Distribución de Inversión por Marca y Plataforma")
    
    resumen_medios = df_master.groupby('Medio')['Gasto'].sum()
    mapa_medios = {med: f"{med} (${tot:,.0f})" for med, tot in resumen_medios.items()}
    df_master['Medio_Labels'] = df_master['Medio'].map(mapa_medios).astype(str)

    df_plot = df_master[df_master['Gasto'] > 0]
    if not df_plot.empty:
        camino_path = ['Marca', 'Medio_Labels', 'Objetivo_Final'] if marca_seleccionada == "Todas las Marcas" else ['Medio_Labels', 'Objetivo_Final']
        
        fig = px.treemap(df_plot, path=camino_path, values='Gasto', color='Gasto', color_continuous_scale=['#d6b58e', '#5b3f8e'])
        fig.update_traces(texttemplate="<b>%{label}</b><br>$%{value:,.0f}", hovertemplate="<b>%{label}</b><br>Inversión: $%{value:,.0f}<extra></extra>", textposition="middle center")
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se detectan datos de gasto mayores a $0 para graficar en este periodo.")

    # --- TABLA DE DETALLES ---
    with st.expander("📝 Desglose Estructurado de Campañas (Data Clean)"):
        df_display = df_master[['Marca', 'Medio', 'Campaña', 'Objetivo_Final', 'Resultados_Final', 'CPA_Final']].rename(
            columns={'Objetivo_Final': 'Objetivo', 'Resultados_Final': 'Resultados', 'CPA_Final': 'CPA'}
        )
        st.dataframe(df_display.sort_values(by=['Marca', 'Medio']), use_container_width=True, hide_index=True)

else:
    st.title("📊 Dashboard Gerencial Cantabria")
    if errores_reportados:
        for err in errores_reportados:
            st.error(err)

st.caption(f"Cantabria Digital Analytics | Strategic Analytics by goBIG")
