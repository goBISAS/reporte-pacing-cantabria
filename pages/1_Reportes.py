import streamlit as st
import pandas as pd
import urllib.parse
import re

st.set_page_config(page_title="Reportes de Rendimiento", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    .report-card { background-color: #141414; border: 1px solid #262626; border-radius: 12px; padding: 24px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .report-header { font-size: 20px; font-weight: bold; color: #d6b58e; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; font-family: 'Georgia', serif; }
    .analysis-box { color: #e0e0e0; font-size: 14.5px; line-height: 1.6; margin-bottom: 20px; text-align: justify; }
    .todo-box { background-color: #1c1510; border-left: 4px solid #d6b58e; padding: 15px 20px; border-radius: 4px; margin-top: 15px; }
    .todo-title { color: #d6b58e; font-weight: bold; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .todo-text { color: #f5f5f5; font-size: 14px; margin: 0; }
    .evidencia-btn { display: inline-block; background-color: transparent; color: #d6b58e !important; border: 1px solid #d6b58e; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 500; transition: all 0.3s ease; margin-top: 10px; text-align: center; }
    .evidencia-btn:hover { background-color: #d6b58e; color: #0d0d0d !important; }
    </style>
    """, unsafe_allow_html=True)

DICCIONARIO_MARCAS = {
    "Uriage": "https://docs.google.com/spreadsheets/d/1XnkC6ONKaJm03k2qAtQmcwuoRrBSh6uXYsdewrlwjK0/",
    "Sensilis": "https://docs.google.com/spreadsheets/d/1e8ZkA61crydoXKdA3lQtMkMMYDHutSR7t6PK-8GvPo0/",
    "Apivita": "https://docs.google.com/spreadsheets/d/1r4KycpStMWvpF1fOzMgmLBjgVQ8dX8WTpgtKWgNm2lM/",
    "Cantabria Labs": "https://docs.google.com/spreadsheets/d/18DGFtWV_BAOLjxBlmImhZ_8Xuilc4CKK_bNZIHQnCcU/"
}

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
    st.info("No se han encontrado registros en las pestañas 'Reporte mensual'.")
else:
    st.sidebar.markdown("### Filtros de Rendimiento")
    marcas_rep = ["Todas las Marcas"] + list(df_reportes['Marca'].unique())
    marca_sel = st.sidebar.selectbox("🧴 Filtrar por Marca:", options=marcas_rep)
    
    meses_disponibles = ["Todos"] + list(df_reportes['Mes'].unique())
    mes_sel = st.sidebar.selectbox("📅 Filtrar por Mes:", options=meses_disponibles)
    
    medios_disponibles = ["Todos"] + list(df_reportes['Medio'].unique())
    medio_sel = st.sidebar.selectbox("🎯 Filtrar por Medio:", options=medios_disponibles)

    df_filtrado = df_reportes.copy()
    if marca_sel != "Todas las Marcas": df_filtrado = df_filtrado[df_filtrado['Marca'] == marca_sel]
    if mes_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Mes'] == mes_sel]
    if medio_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Medio'] == medio_sel]

    st.write(f"Mostrando **{len(df_filtrado)}** análisis encontrados:")
    
    for _, fila in df_filtrado.iterrows():
        evidencia_url = fila['Evidencia']
        evidencia_html = ""
        if evidencia_url and evidencia_url.startswith("http"):
            evidencia_html = f"<div style='margin-top: 15px;'><a href='{evidencia_url}' target='_blank' class='evidencia-btn'>🔗 Abrir enlace de evidencia</a></div>"

        card_html = f"<div class='report-card'><div class='report-header'>[{fila['Marca'].upper()}] {fila['Medio']} | {fila['Mes']} {fila['Año']}</div><div style='color: #d6b58e; font-weight: bold; margin-bottom: 5px; font-size:12px; letter-spacing:0.5px;'>ANÁLISIS E INSIGHTS:</div><div class='analysis-box'>{fila['Observación']}</div>{evidencia_html}</div>"
        st.markdown(card_html, unsafe_allow_html=True)
        
        if fila['To_Do']:
            todo_html = f"<div class='todo-box'><div class='todo-title'>⚡ Siguientes Pasos (To Do):</div><p class='todo-text'>{fila['To_Do']}</p></div>"
            st.markdown(todo_html, unsafe_allow_html=True)
