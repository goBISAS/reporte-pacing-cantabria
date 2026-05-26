import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import urllib.parse
import re

# CONFIGURACIÓN DE PÁGINA PREMIUM
st.set_page_config(
    page_title="Cantabria - Multibrand Paid Media Dashboard",
    page_icon="⚡",
    layout="wide"
)

# ESTILOS PREMIUM GO BIG
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

# --- MAPEO HISTÓRICO DE REPOSITORIOS UNIFICADOS ---
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
    variantes_pestaña = [mes_str, mes_str.title(), mes_str.lower()]
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
        # 1. RADAR: Localizar fila de inicio (Fila 3)
        idx_header = 2
        
        # 2. LECTURA DEL PRESUPUESTO APROBADO MENSUAL (Líneas superiores)
        presupuesto_marca = 0.0
        for i in range(idx_header + 1):
            if i >= len(df_raw): break
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

        # 3. CONSTRUCCIÓN DE MATRIZ DE DATOS POSICIONAL POSICIONAL (Hyatt V5.0 / BogoApts V2.1)
        df_datos = df_raw.iloc[idx_header + 1:].copy()
        
        col_idx_medio = 0  # Columna A: Channel
        col_idx_camp = 1   # Columna B: Campaign
        col_idx_status = 4 # Columna E: Status (Activa / Pausada / Completada) -> INTEGRADO
        col_idx_spend = 7  # Columna H: Spend (COP)
        col_idx_res = 14   # Columna O: Platform Conversions
        col_idx_tipo = 15  # Columna P: Official Conversions
        col_idx_cpa = 17   # Columna R: CPA
        col_idx_fecha = 18 # Columna S: Actualizacion Pacing

        # 4. EXTRACCIÓN INVERSA DE FECHA DE ACTUALIZACIÓN
        marca_fecha = "N/D"
        if len(df_datos) > 0 and len(df_raw.columns) > col_idx_fecha:
            for row_pos in range(len(df_raw) - 1, idx_header, -1):
                val_celda = str(df_raw.iloc[row_pos, col_idx_fecha]).strip()
                val_lower = val_celda.lower()
                
                if val_celda != '' and val_lower not in ['nan', 'none', '<na>', '-', 'null', 'total']:
                    if not any(k in val_lower for k in ['actualiz', 'pacing', 'fecha', 'campaign', 'nombre']):
                        marca_fecha = val_celda
                        break
        fechas_actualizacion[marca] = marca_fecha

        # 5. CREACIÓN PROTEGIDA DE FILAS DE CAMPANAS
        lista_campanas_marca = []
        for idx, row in df_datos.iterrows():
            if len(row) <= max(col_idx_camp, col_idx_medio): continue
            
            celda_camp = str(row[col_idx_camp]).strip()
            celda_medio = str(row[col_idx_medio]).strip()
            
            if celda_camp == '' or any(k in celda_camp.lower() for k in ['campaign', 'campaña', 'nombre de la', 'total']):
                continue
                
            # Extracción segura e inserción de la columna de estado
            celda_status = str(row[col_idx_status]).strip() if len(row) > col_idx_status else 'N/D'
            if celda_status == '': celda_status = 'N/D'
            
            celda_spend = str(row[col_idx_spend]).strip() if len(row) > col_idx_spend else '0'
            celda_tipo = str(row[col_idx_tipo]).strip() if len(row) > col_idx_tipo else 'General'
            if celda_tipo == '': celda_tipo = 'Sin Objetivo'
            
            celda_res = str(row[col_idx_res]).strip() if len(row) > col_idx_res else 'N/D'
            celda_cpa = str(row[col_idx_cpa]).strip() if len(row) > col_idx_cpa else 'N/D'

            lista_campanas_marca.append({
                'Marca': marca,
                'Medio_Raw': celda_medio,
                'Campaña': celda_camp,
                'Estado': celda_status,
                'Gasto_Raw': celda_spend,
                'Objetivo': celda_tipo,
                'Resultados': celda_res,
                'CPA': celda_cpa
            })

        if lista_campanas_marca:
            df_marca_limpio = pd.DataFrame(lista_campanas_marca)
            
            # Relleno inteligente del canal hacia abajo (ffill)
            df_marca_limpio['Medio_Raw'] = df_marca_limpio['Medio_Raw'].replace(['', 'nan', 'NaN'], pd.NA)
            df_marca_limpio['Medio'] = df_marca_limpio['Medio_Raw'].ffill().fillna('Sin Medio')
            
            # Formateo numérico
            df_marca_limpio['Gasto'] = df_marca_limpio['Gasto_Raw'].str.replace(r'[^\d.-]', '', regex=True)
            df_marca_limpio['Gasto'] = pd.to_numeric(df_marca_limpio['Gasto'], errors='coerce').fillna(0)
            
            campañas_consolidadas.append(df_marca_limpio[['Marca', 'Medio', 'Campaña', 'Estado', 'Gasto', 'Objetivo', 'Resultados', 'CPA']])

    except Exception as e:
        errores_reportados.append(f"Error procesando los datos de **{marca}**: {str(e)}")

# --- RENDERIZADO VISUAL ---
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
            st.write(f"✅ **{m}**: Sincronizado | Presupuesto: ${totales_presupuesto.get(m, 0):,.0f} | Último registro: {fechas_actualizacion.get(m, 'N/D')}")

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
        camino_path = ['Marca', 'Medio_Labels', 'Objetivo'] if marca_seleccionada == "Todas las Marcas" else ['Medio_Labels', 'Objetivo']
        
        fig = px.treemap(df_plot, path=camino_path, values='Gasto', color='Gasto', color_continuous_scale=['#d6b58e', '#5b3f8e'])
        fig.update_traces(texttemplate="<b>%{label}</b><br>$%{value:,.0f}", hovertemplate="<b>%{label}</b><br>Inversión: $%{value:,.0f}<extra></extra>", textposition="middle center")
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se detectan datos de gasto mayores a $0 para graficar en este periodo.")

    # --- TABLA DE DETALLES CON COLUMNA ESTADO HOMOLOGADA ---
    with st.expander("📝 Desglose Estructurado de Campañas (Data Clean)"):
        st.dataframe(df_master[['Marca', 'Medio', 'Campaña', 'Estado', 'Objetivo', 'Resultados', 'CPA']].sort_values(by=['Marca', 'Medio']), use_container_width=True, hide_index=True)

else:
    st.title("📊 Dashboard Gerencial Cantabria")
    if errores_reportados:
        for err in errores_reportados:
            st.error(err)

st.caption(f"Cantabria Digital Analytics | Strategic Analytics by goBIG")
