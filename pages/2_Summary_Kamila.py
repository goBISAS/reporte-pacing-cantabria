import streamlit as st
import pandas as pd
import urllib.parse
import re

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Summary Kamila", page_icon="⚡", layout="wide")

# ESTILOS PREMIUM GO BIG PARA KPIs
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    [data-testid="stMetricValue"] { font-size: 34px; color: #d6b58e !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #f5f5f5 !important; font-size: 15px !important; letter-spacing: 0.5px; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    
    /* Contenedores de las secciones de KPI */
    .kpi-section { 
        background-color: #141414; 
        border: 1px solid #262626; 
        border-radius: 12px; 
        padding: 25px; 
        margin-bottom: 25px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
    }
    .section-title { 
        color: #d6b58e; 
        font-weight: bold; 
        font-size: 17px; 
        border-bottom: 1px solid #333; 
        padding-bottom: 12px; 
        margin-bottom: 20px; 
        text-transform: uppercase; 
        letter-spacing: 1.5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Summary Estratégico: Cantabria Labs")
st.caption("Visión Gerencial de KPIs de Rendimiento (Fuente: Kamila)")

# ==========================================
# EXTRACCIÓN Y LIMPIEZA DE DATOS
# ==========================================
@st.cache_data(ttl=600)
def obtener_datos_summary():
    # URL del nuevo documento, apuntando a la hoja Summary
    id_publicacion = "1TQzJuqbBqESer_nGhG5kyl4oMcGVIcWV0Q5xCnlmxFc"
    sheet_enc = urllib.parse.quote("Summary")
    csv_url = f"https://docs.google.com/spreadsheets/d/{id_publicacion}/gviz/tq?tqx=out:csv&sheet={sheet_enc}"
    
    # Leemos forzando lectura como string
    df = pd.read_csv(csv_url, header=None, dtype=str).fillna("")
    
    datos_estructurados = []
    
    # Recorremos el dataframe saltando los encabezados internos
    for idx, row in df.iterrows():
        metrica = str(row.iloc[0]).strip()
        if metrica in ["", "None", "Métrica", "Alcance"]: continue
        
        # Mapeamos las columnas según la estructura de la imagen
        alcance_val = str(row.iloc[1]).strip()
        visitas_der_val = str(row.iloc[2]).strip()
        visitas_ali_val = str(row.iloc[3]).strip()
        res_der_val = str(row.iloc[4]).strip()
        f_inicio = str(row.iloc[5]).strip()
        f_fin = str(row.iloc[6]).strip()
        
        # Agrupamos por bloque de fechas válido
        if f_inicio not in ["", "None", "Fecha de inicio"]:
            periodo = f"{f_inicio} al {f_fin}"
            
            # Detectamos en qué columna cayó el valor numérico
            valor_final = "-"
            if alcance_val not in ["", "-", "None"]: valor_final = alcance_val
            elif visitas_der_val not in ["", "-", "None"]: valor_final = visitas_der_val
            elif visitas_ali_val not in ["", "-", "None"]: valor_final = visitas_ali_val
            elif res_der_val not in ["", "-", "None"]: valor_final = res_der_val
            
            datos_estructurados.append({
                "Periodo": periodo,
                "Metrica": metrica,
                "Valor": valor_final
            })
            
    return pd.DataFrame(datos_estructurados)

df_summary = obtener_datos_summary()

# ==========================================
# RENDERIZADO VISUAL
# ==========================================
if df_summary.empty:
    st.info("No se han encontrado registros válidos en la pestaña 'Summary'.")
else:
    # 1. Filtro lateral dinámico
    periodos_disponibles = df_summary['Periodo'].unique().tolist()
    with st.sidebar:
        st.markdown("### ⚙️ Contexto Summary")
        periodo_sel = st.selectbox("📅 Periodo de Análisis:", options=periodos_disponibles)
        
    df_filtrado = df_summary[df_summary['Periodo'] == periodo_sel]
    
    # Función de rescate seguro de métricas
    def get_metric(nombre_metrica):
        match = df_filtrado[df_filtrado['Metrica'].str.contains(nombre_metrica, case=False, na=False, regex=False)]
        return match.iloc[0]['Valor'] if not match.empty else "-"

    # 2. Despliegue de Tarjetas KPI
    # BLOQUE A: AWARENESS
    st.markdown("<div class='kpi-section'><div class='section-title'>👁️ Awareness y Alcance Global</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Alcance a la fecha", get_metric("Alcance a la fecha"))
    with c2: st.metric("Costo por alcance", get_metric("Costo por alcance a la fecha"))
    with c3: st.metric("% Interacción social", get_metric("% de interacción social"))
    st.markdown("</div>", unsafe_allow_html=True)
    
    # BLOQUE B: TRÁFICO DERMARKET
    st.markdown("<div class='kpi-section'><div class='section-title'>🛒 Tráfico Propio: Dermarket</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Visitas Dermarket", get_metric("Visitas a Dermarket"))
    with c2: st.metric("Costo por Visita", get_metric("Costo por Visita"))
    with c3: st.metric("CTR Dermarket", get_metric("CTR (visitas a dermarket)"))
    with c4: st.metric("CPA Global", get_metric("CPA"))
    st.markdown("</div>", unsafe_allow_html=True)
    
    # BLOQUE C: TRÁFICO ALIADOS
    st.markdown("<div class='kpi-section'><div class='section-title'>🤝 Tráfico de Salida: Aliados Comerciales</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Clics a Aliados", get_metric("Clics a aliados"))
    with c2: st.metric("Costo por Clic", get_metric("Costo por clic"))
    with c3: st.metric("CTR Aliados", get_metric("CTR (campañas clics aliados)"))
    st.markdown("</div>", unsafe_allow_html=True)
