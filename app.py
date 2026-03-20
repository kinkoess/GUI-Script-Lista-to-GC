import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="OdontoCalendar Tool", page_icon="🦷")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    textarea:focus { border-color: #28a745 !important; }
    .stTextArea label { display: none; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("# 🦷 OdontoCalendar:  \n# Tabla OneNote a Google Calendar")

# Lógica de reinicio
if 'procesar' not in st.session_state: st.session_state['procesar'] = False
def limpiar_estado(): st.session_state['procesar'] = False

st.subheader("1. Carga de Datos")
anio = st.number_input("Año Académico:", value=2026, step=1)

datos_input = st.text_area(
    label="Input_Tabla", height=150, 
    placeholder="Pega tu tabla aquí (EVALUACION, ASIGNATURA, FECHA, HORA*)...",
    on_change=limpiar_estado
)

if not datos_input:
    st.info("💡 Tip: Si agregas una columna 'HORA' (ej: 08:30), los eventos tendrán duración de 70 min.")
    st.session_state['procesar'] = False
else:
    if st.button("🚀 Procesar Tabla Pegada", use_container_width=True):
        st.session_state['procesar'] = True

# --- PROCESAMIENTO ---
if st.session_state.get('procesar') and datos_input:
    try:
        df = pd.read_csv(io.StringIO(datos_input.strip()), sep='\t')
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        # Validar columnas mínimas
        columnas_req = ['EVALUACION', 'ASIGNATURA', 'FECHA']
        if not all(col in df.columns for col in columnas_req):
            st.error("❌ Falta una columna básica: EVALUACION, ASIGNATURA o FECHA.")
            st.stop()

        st.divider()
        abreviaciones = {
            "1° Teórica": "1° T.", "2° Teórica": "2° T.", "3° Teórica": "3° T.", "4° Teórica": "4° T.",
            "1° Evaluación Clínica": "1° E.C.", "2° Evaluación Clínica": "2° E.C.", "Caso Clínico": "C.C.",
            "Presentación CC": "P.CC", "1° Examen": "1° E.", "2° Examen": "2° E."
        }

        # Modo de exportación
        st.subheader("2. Modo de Exportación")
        modo = st.radio("Selecciona:", ["Lista Completa", "Filtrar por Categoría"], index=0)

        df_final = df.copy() if modo == "Lista Completa" else df[df['EVALUACION'] == st.selectbox("Categoría:", [opt for opt in abreviaciones.keys() if opt in df['EVALUACION'].unique()] + [o for o in df['EVALUACION'].unique() if o not in abreviaciones])]
        nombre_archivo = "Evaluaciones.csv" if modo == "Lista Completa" else f"Filtrado.csv"

        # --- LÓGICA DE TIEMPO INTELIGENTE ---
        calendar_df = pd.DataFrame()
        
        def formatear_titulo(fila):
            abrev = abreviaciones.get(fila['EVALUACION'], fila['EVALUACION'])
            return f"{abrev} {fila['ASIGNATURA']}"

        calendar_df['Subject'] = df_final.apply(formatear_titulo, axis=1)
        calendar_df['Start Date'] = pd.to_datetime(df_final['FECHA'] + f"-{anio}", format='%d-%m-%Y').dt.strftime('%m/%d/%Y')
        
        # Si existe la columna HORA, calculamos tiempos
        if 'HORA' in df_final.columns:
            calendar_df['Start Time'] = df_final['HORA']
            # Calcular End Time (Start Time + 70 minutos)
            tiempos_fin = []
            for h in df_final['HORA']:
                try:
                    t_inicio = datetime.strptime(h, "%H:%M")
                    t_fin = t_inicio + timedelta(minutes=70)
                    tiempos_fin.append(t_fin.strftime("%H:%M"))
                except:
                    tiempos_fin.append("") # En caso de error de formato
            
            calendar_df['End Time'] = tiempos_fin
            calendar_df['All Day Event'] = 'FALSE'
        else:
            calendar_df['All Day Event'] = 'TRUE'

        calendar_df['End Date'] = calendar_df['Start Date']
        calendar_df['Location'] = 'Universidad Mayor, Temuco'
        calendar_df['Private'] = 'TRUE'

        # Vista previa y descarga
        calendar_df.index = range(1, len(calendar_df) + 1)
        st.success(f"✅ ¡Listos {len(calendar_df)} eventos!")
        st.download_button("📥 Descargar CSV", calendar_df.to_csv(index=False).encode('utf-8'), nombre_archivo, "text/csv", use_container_width=True)
        st.dataframe(calendar_df[['Subject', 'Start Date', 'All Day Event']], use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error: Revisa el formato de la tabla. {str(e)}")
