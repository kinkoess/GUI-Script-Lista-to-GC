import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="OdontoCalendar Tool", page_icon="🦷")

# --- ESTILO CSS PERSONALIZADO ---
st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    textarea:focus {
        border-color: #28a745 !important;
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
    }
    .stTextArea label { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Título con salto de línea
st.markdown("# 🦷 OdontoCalendar:  \n# Tabla OneNote a Google Calendar")

# --- LÓGICA DE REINICIO ---
if 'procesar' not in st.session_state:
    st.session_state['procesar'] = False

def limpiar_estado():
    st.session_state['procesar'] = False

st.subheader("1. Carga de Datos")

# Selector de Año Académico
anio_actual = datetime.now().year
col_anio, _ = st.columns([1, 2])
with col_anio:
    anio = st.number_input("Año Académico:", value=2026, step=1)

# Contenedor para el mensaje inicial
contenedor_mensaje = st.empty()

# ÁREA DE TEXTO
datos_input = st.text_area(
    label="Input_Tabla",
    height=150, 
    placeholder="Pega aquí tu tabla de OneNote...",
    on_change=limpiar_estado
)

# Lógica del mensaje de bienvenida
if not datos_input:
    contenedor_mensaje.info("💡 Por favor, pega la tabla de OneNote arriba para comenzar. (Opcional: columna 'HORA')")
    st.session_state['procesar'] = False
else:
    contenedor_mensaje.empty()
    if st.button("🚀 Procesar Tabla Pegada", use_container_width=True):
        st.session_state['procesar'] = True

# --- PROCESAMIENTO Y VALIDACIÓN ---
if st.session_state.get('procesar') and datos_input:
    try:
        df = pd.read_csv(io.StringIO(datos_input.strip()), sep='\t')
        df.columns = df.columns.str.strip()
        # Convertimos valores nulos de texto a vacíos para evitar el "None"
        df = df.fillna("")
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        columnas_requeridas = ['EVALUACION', 'ASIGNATURA', 'FECHA']
        if not all(col in df.columns for col in columnas_requeridas):
            st.error("❌ Error: La tabla no tiene el formato esperado (EVALUACION, ASIGNATURA, FECHA).")
            st.stop()

        st.divider()
        
        abreviaciones = {
            "1° Teórica": "1° T.", "2° Teórica": "2° T.", "3° Teórica": "3° T.", "4° Teórica": "4° T.",
            "1° Evaluación Clínica": "1° E.C.", "2° Evaluación Clínica": "2° E.C.", "Caso Clínico": "C.C.",
            "Presentación CC": "P.CC", "1° Examen": "1° E.", "2° Examen": "2° E."
        }

        # MODO DE EXPORTACIÓN
        st.subheader("2. Modo de Exportación")
        modo = st.radio(
            "¿Cómo quieres exportar tus eventos?",
            ["Lista Completa (Todo en un solo archivo)", "Filtrar por Categoría (Separar calendarios)"],
            index=0
        )

        df_final = pd.DataFrame()
        nombre_archivo = ""

        if modo == "Lista Completa (Todo en un solo archivo)":
            df_final = df.copy()
            nombre_archivo = "Evaluaciones.csv"
        else:
            opciones_disponibles = [opt for opt in abreviaciones.keys() if opt in df['EVALUACION'].unique()]
            otros = [opt for opt in df['EVALUACION'].unique() if opt not in abreviaciones.keys()]
            opciones_finales = opciones_disponibles + otros

            st.subheader("3. Filtra tu Calendario")
            categoria = st.selectbox("¿Qué calendario vas a actualizar ahora?", opciones_finales)
            df_final = df[df['EVALUACION'] == categoria].copy()
            nombre_archivo = f"{categoria}.csv"

        # --- GENERACIÓN DEL FORMATO GOOGLE ---
        def formatear_titulo(fila):
            eval_orig = fila['EVALUACION']
            asignatura = fila['ASIGNATURA']
            abrev = abreviaciones.get(eval_orig, eval_orig)
            return f"{abrev} {asignatura}"

        calendar_df = pd.DataFrame()
        calendar_df['Subject'] = df_final.apply(formatear_titulo, axis=1)
        calendar_df['Start Date'] = pd.to_datetime(df_final['FECHA'] + f"-{anio}", format='%d-%m-%Y').dt.strftime('%m/%d/%Y')
        calendar_df['End Date'] = calendar_df['Start Date']
        
        # --- LÓGICA DE HORA ---
        tiene_hora = 'HORA' in df_final.columns
        if tiene_hora:
            calendar_df['Start Time'] = df_final['HORA']
            tiempos_fin = []
            all_day_status = []
            
            for h in df_final['HORA']:
                if h and h != "":
                    try:
                        t_inicio = datetime.strptime(h, "%H:%M")
                        t_fin = t_inicio + timedelta(minutes=70)
                        tiempos_fin.append(t_fin.strftime("%H:%M"))
                        all_day_status.append('FALSE')
                    except:
                        tiempos_fin.append("") 
                        all_day_status.append('TRUE')
                else:
                    tiempos_fin.append("")
                    all_day_status.append('TRUE')
            
            calendar_df['End Time'] = tiempos_fin
            calendar_df['All Day Event'] = all_day_status
        else:
            calendar_df['All Day Event'] = 'TRUE'

        calendar_df['Location'] = 'Universidad Mayor, Temuco'
        calendar_df['Private'] = 'TRUE'

        calendar_df.index = range(1, len(calendar_df) + 1)
        
        # Botón de descarga
        csv = calendar_df.to_csv(index=False).encode('utf-8')
        st.success(f"✅ ¡Datos listos!")
        
        st.download_button(
            label=f"📥 Descargar {nombre_archivo}",
            data=csv,
            file_name=nombre_archivo,
            mime='text/csv',
            use_container_width=True
        )

        # --- PREVISUALIZACIÓN LIMPIA ---
        if tiene_hora:
            # Reemplazamos los valores vacíos reales por un string vacío para la tabla visual
            preview_df = calendar_df[['Subject', 'Start Date', 'Start Time', 'End Time']].fillna("")
            st.dataframe(preview_df, use_container_width=True)
        else:
            st.dataframe(calendar_df[['Subject', 'Start Date']], use_container_width=True)

        if st.button("🔄 Reiniciar"):
            st.session_state['procesar'] = False
            st.rerun()

    except Exception as e:
        st.error(f"❌ Error crítico: {str(e)}")
        st.stop()
