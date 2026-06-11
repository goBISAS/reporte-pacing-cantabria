import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import urllib.parse
import re

# ==========================================
# CONFIGURACIÓN DE PÁGINA PREMIUM UNIFICADA
# ==========================================
st.set_page_config(
    page_title="Cantabria - Multibrand Paid Media Dashboard",
    page_icon="⚡",
    layout="wide"
)

# ESTILOS PREMIUM GO BIG (Actualizados con Media Queries para previsualización)
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    [data-testid="stMetricValue"] { font-size: 32px; color: #d6b58e !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #f5f5f5 !important; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    .stSidebar { background-color: #1a1a1a; border-right: 1px solid #333; }
    .stPlotlyChart { border: 1px solid #333; border-radius: 8px; background-color: #1a1a1a; }
    
    .report-card { background-color: #141414; border: 1px solid #262626; border-radius: 12px; padding: 24px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .report-header { font-size: 20px; font-weight: bold; color: #d6b58e; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; font-family: 'Georgia', serif; }
    .analysis-box { color: #e0e0e0; font-size: 14.5px; line-height: 1.6; margin-bottom: 20px; text-align: justify; }
    .todo-box { background-color: #1c1510; border-left: 4px solid #d6b58e; padding: 15px 20px; border-radius: 4px; margin-top: 15px; }
    .todo-title { color: #d6b58e; font-weight: bold; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .todo-text { color: #f5f5f5; font-size: 14px; margin: 0; }
    .evidencia-btn { display: inline-block; background-color: transparent; color: #d6b58e !important; border: 1px solid #d6b58e; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 500; transition: all 0.3s ease; margin-top: 10px; text-align: center; }
    .evidencia-btn:hover { background-color: #d6b58e; color: #0d0d0d !important; }
    
    /* Previsualización Responsiva */
    .desktop-preview { display: block; width: 100%; max-height: 400px; object-fit: contain; margin-top: 15px; border-radius: 8px; border: 1px solid #333; }
    .mobile-btn-container { display: none; }
    
    @media (max-width: 768px) {
        .desktop-preview { display: none !important; }
        .mobile-btn-container { display: block !important; margin-top: 15px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- MAPEO HISTÓRICO DE REPOSITORIOS UNIFICADOS ---
DICCIONARIO_MARCAS = {
    "Uriage": "https://docs.google.com/spreadsheets/d/1XnkC6ONKaJm03k2qAtQmcwuoRrBSh6uXYsdewrlwjK0/",
    "Sensilis": "https://docs.google.com/spreadsheets/d/1e8ZkA61crydoXKdA3lQtMkMMYDHutSR7t6PK-8GvPo0/",
    "Apivita": "https://docs.google.com/spreadsheets/d/1r4KycpStMWvpF1fOzMgmLBjgVQ8dX8WTpgtKWgNm2lM/",
    "Cantabria Labs": "https://docs.google.com/spreadsheets/d/18DGFtWV_BAOLjxBlmImhZ_8Xuilc4CKK_bNZIHQnCcU/"
}

def limpiar_monto_numerico(valor_str):
    try:
        limpio = re.sub(r'[^\d.-]', '', str(valor_str))
        return float(limpio) if limpio else 0.0
    except:
        return 0.0

# ==========================================
# NAVEGACIÓN PRINCIPAL EN SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("## 📊 Control de Paid Media")
    st.write("Grupo: **Cantabria**")
    st.markdown("---")
    
    opcion_menu = st.radio(
        "🧠 Seleccione la Vista:",
        ["📈 Dashboard Gerencial", "📝 Reportes de Rendimiento"],
        index=0
    )
    st.markdown("---")

# ==========================================
# PÁGINA 1: DASHBOARD GERENCIAL
# ==========================================
def render_dashboard_gerencial():
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

    meses_disponibles = obtener_meses_disponibles()
    st.sidebar.markdown("### Contexto: Dashboard Gerencial")
    mes_seleccionado = st.sidebar.selectbox("📅 Seleccione el Mes de Reporte:", options=meses_disponibles, key="sb_mes_gerencial")
    marcas_disponibles = ["Todas las Marcas"] + list(DICCIONARIO_MARCAS.keys())
    marca_seleccionada = st.sidebar.selectbox("🧴 Filtrar por Marca:", options=marcas_disponibles, key="sb_marca_gerencial")

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
            idx_header = 2
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

            df_datos = df_raw.iloc[idx_header + 1:].copy()
            col_idx_medio = 0; col_idx_camp = 1; col_idx_status = 4; col_idx_spend = 7
            col_idx_res = 14; col_idx_tipo = 15; col_idx_cpa = 17; col_idx_fecha = 18 

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

            lista_campanas_marca = []
            for idx, row in df_datos.iterrows():
                if len(row) <= max(col_idx_camp, col_idx_medio): continue
                celda_camp = str(row[col_idx_camp]).strip()
                celda_medio = str(row[col_idx_medio]).strip()
                if celda_camp == '' or any(k in celda_camp.lower() for k in ['campaign', 'campaña', 'nombre de la', 'total']):
                    continue
                celda_status = str(row[col_idx_status]).strip() if len(row) > col_idx_status else 'N/D'
                if celda_status == '': celda_status = 'N/D'
                celda_spend = str(row[col_idx_spend]).strip() if len(row) > col_idx_spend else '0'
                celda_tipo = str(row[col_idx_tipo]).strip() if len(row) > col_idx_tipo else 'General'
                if celda_tipo == '': celda_tipo = 'Sin Objetivo'
                celda_res = str(row[col_idx_res]).strip() if len(row) > col_idx_res else 'N/D'
                celda_cpa = str(row[col_idx_cpa]).strip() if len(row) > col_idx_cpa else 'N/D'

                lista_campanas_marca.append({
                    'Marca': marca, 'Medio_Raw': celda_medio, 'Campaña': celda_camp,
                    'Estado': celda_status, 'Gasto_Raw': celda_spend, 'Objetivo': celda_tipo,
                    'Resultados': celda_res, 'CPA': celda_cpa
                })

            if lista_campanas_marca:
                df_marca_limpio = pd.DataFrame(lista_campanas_marca)
                df_marca_limpio['Medio_Raw'] = df_marca_limpio['Medio_Raw'].replace(['', 'nan', 'NaN'], pd.NA)
                df_marca_limpio['Medio'] = df_marca_limpio['Medio_Raw'].ffill().fillna('Sin Medio')
                df_marca_limpio['Gasto'] = df_marca_limpio['Gasto_Raw'].str.replace(r'[^\d.-]', '', regex=True)
                df_marca_limpio['Gasto'] = pd.to_numeric(df_marca_limpio['Gasto'], errors='coerce').fillna(0)
                campañas_consolidadas.append(df_marca_limpio[['Marca', 'Medio', 'Campaña', 'Estado', 'Gasto', 'Objetivo', 'Resultados', 'CPA']])

        except Exception as e:
            errores_reportados.append(f"Error procesando los datos de **{marca}**: {str(e)}")

    if campañas_consolidadas:
        df_master = pd.concat(campañas_consolidadas, ignore_index=True)
        presupuesto_total_global = sum(totales_presupuesto.values())
        gasto_total_global = df_master['Gasto'].sum()
        
        st.title(f"⚡ Dashboard Gerencial Cantabria: {mes_seleccionado.title()}")
        if marca_seleccionada != "Todas las Marcas":
            st.subheader(f"Foco en la marca: {marca_seleccionada}")

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Presupuesto Configurado", f"${presupuesto_total_global:,.0f}")
        with c2: st.metric("Inversión Ejecutada Total", f"${gasto_total_global:,.0f}")
        with c3:
            if mes_seleccionado == meses_disponibles[0]:
                st.metric("Día de Medición", f"Día {datetime.now().day}")
            else:
                st.metric("Estado del Mes", "Cerrado")

        with st.expander("🔗 Estado de Conexión de los Documentos"):
            for m in totales_presupuesto.keys():
                st.write(f"✅ **{m}**: Sincronizado | Presupuesto: ${totales_presupuesto.get(m, 0):,.0f} | Último registro: {fechas_actualizacion.get(m, 'N/D')}")

        if errores_reportados:
            for err in errores_reportados: st.warning(err)
                
        st.divider()
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

        with st.expander("📝 Desglose Estructurado de Campañas (Data Clean)"):
            st.dataframe(df_master[['Marca', 'Medio', 'Campaña', 'Estado', 'Objetivo', 'Resultados', 'CPA']].sort_values(by=['Marca', 'Medio']), use_container_width=True, hide_index=True)
    else:
        st.title("📊 Dashboard Gerencial Cantabria")
        if errores_reportados:
            for err in errores_reportados: st.error(err)

# ==========================================
# PÁGINA 2: REPORTES DE RENDIMIENTO Y OPTIMIZACIÓN
# ==========================================
def render_reportes_rendimiento():
    st.title("📈 Reportes de Rendimiento y Optimización")
    st.caption("Análisis cualitativo, pruebas de mercado y planes de acción estratégicos.")
    
    @st.cache_data(ttl=600)
    def cargar_reportes_desde_drive():
        registros_totales = []
        pestaña_target = "Reporte mensual"
        sheet_enc = urllib.parse.quote(pestaña_target)
        
        for marca, url_base in DICCIONARIO_MARCAS.items():
            try:
                id_publicacion = url_base.split("/d/")[1].split("/")[0]
                csv_url = f"https://docs.google.com/spreadsheets/d/{id_publicacion}/gviz/tq?tqx=out:csv&sheet={sheet_enc}"
                df_rep = pd.read_csv(csv_url, dtype=str).fillna('')
                if len(df_rep.columns) >= 6:
                    for idx, row in df_rep.iterrows():
                        if str(row.iloc[2]).strip() != '' and str(row.iloc[3]).strip() != '':
                            registros_totales.append({
                                "Marca": marca, "Año": str(row.iloc[0]).strip(), "Mes": str(row.iloc[1]).strip(),
                                "Medio": str(row.iloc[2]).strip(), "Observación": str(row.iloc[3]).strip(),
                                "Evidencia": str(row.iloc[4]).strip(), "To_Do": str(row.iloc[5]).strip()
                            })
            except: continue
        return pd.DataFrame(registros_totales)

    df_reportes = cargar_reportes_desde_drive()
    if df_reportes.empty:
        st.info("No se han encontrado registros en las pestañas 'Reporte mensual' de las marcas configuradas.")
        return

    st.sidebar.markdown("### Contexto: Rendimiento")
    marcas_rep = ["Todas las Marcas"] + list(df_reportes['Marca'].unique())
    marca_sel = st.sidebar.selectbox("🧴 Filtrar por Marca:", options=marcas_rep, key="sb_marca_rep")
    
    meses_disponibles = ["Todos"] + list(df_reportes['Mes'].unique())
    mes_sel = st.sidebar.selectbox("📅 Filtrar por Mes:", options=meses_disponibles, key="sb_mes_rep")
    
    medios_disponibles = ["Todos"] + list(df_reportes['Medio'].unique())
    medio_sel = st.sidebar.selectbox("🎯 Filtrar por Medio:", options=medios_disponibles, key="sb_medio_rep")

    df_filtrado = df_reportes.copy()
    if marca_sel != "Todas las Marcas": df_filtrado = df_filtrado[df_filtrado['Marca'] == marca_sel]
    if mes_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Mes'] == mes_sel]
    if medio_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Medio'] == medio_sel]

    st.write(f"Mostrando **{len(df_filtrado)}** análisis encontrados:")
    
    for _, fila in df_filtrado.iterrows():
        evidencia_url = fila['Evidencia']
        evidencia_html = ""
        
        if evidencia_url and evidencia_url.startswith("http"):
            # LÓGICA DE DETECCIÓN: Buscar si es un archivo directo de Google Drive
            match_file = re.search(r'/file/d/([a-zA-Z0-9_-]+)', evidencia_url)
            
            if match_file:
                # Si es un archivo, extraemos el ID y habilitamos la previsualización responsiva
                img_id = match_file.group(1)
                img_direct_url = f"https://drive.google.com/uc?export=view&id={img_id}"
                evidencia_html = f"""
                <div style="margin-top: 15px;">
                    <img src="{img_direct_url}" class="desktop-preview" alt="Evidencia visual">
                    <div class="mobile-btn-container">
                        <a href="{evidencia_url}" target="_blank" class="evidencia-btn">🔗 Abrir evidencia en Google Drive</a>
                    </div>
                </div>
                """
            else:
                # Si es una carpeta de Drive (folders) u otro enlace web, solo permitimos el botón
                evidencia_html = f"""
                <div style="margin-top: 15px;">
                    <a href="{evidencia_url}" target="_blank" class="evidencia-btn">🔗 Abrir enlace de evidencia</a>
                </div>
                """

        card_html = f"""
        <div class="report-card">
            <div class="report-header">
                [{fila['Marca'].upper()}] {fila['Medio']} | {fila['Mes']} {fila['Año']}
            </div>
            <div style="color: #d6b58e; font-weight: bold; margin-bottom: 5px; font-size:12px; letter-spacing:0.5px;">ANÁLISIS E INSIGHTS:</div>
            <div class="analysis-box">
                {fila['Observación']}
            </div>
            {evidencia_html}
        """
        st.markdown(card_html, unsafe_allow_html=True)
        
        if fila['To_Do']:
            todo_html = f"""
            <div class="todo-box">
                <div class="todo-title">⚡ Siguientes Pasos (To Do):</div>
                <p class="todo-text">{fila['To_Do']}</p>
            </div>
            """
            st.markdown(todo_html, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# RUTAS DE ENRUTAMIENTO DINÁMICO
# ==========================================
if opcion_menu == "📈 Dashboard Gerencial":
    render_dashboard_gerencial()
elif opcion_menu == "📝 Reportes de Rendimiento":
    render_reportes_rendimiento()

st.caption(f"Cantabria Digital Analytics | Strategic Analytics by goBIG v2.6")
