import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="OdontoCalendar Tool", page_icon="🦷")

# --- ESTILO CSS PERSONALIZADO ---
st.markdown("""
    <style>
    /* Ocultar botón automático de la tabla */
    [data-testid="stElementToolbar"] { display: none; }

    /* Borde VERDE cuando el cuadro de texto está activo */
    textarea:focus {
        border-color: #28a745 !important;
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
    }
    
    /* Estilo para las etiquetas */
    .stTextArea label {
        display: none; /* Escondemos la etiqueta de arriba para usar el st.info */
    }
    </style>
    """, unsafe_allow_html=True)

# Título con salto de línea
st.markdown("# 🦷 OdontoCalendar:  \n# Tabla OneNote a Google Calendar")

# LÓGICA DE INTERFAZ DINÁMICA
if "procesar" not in st.session_state:
    st.session_state['procesar'] = False

# 1. Entrada de datos
st.subheader("1. Carga de Datos")

# Si no hay texto, mostramos el mensaje informativo arriba del cuadro
datos_input = st.text_area(
    label="Input de Tabla", # El label existe pero el CSS lo oculta
    height=150, 
    placeholder="Pega aquí (EVALUACION, ASIGNATURA, FECHA)..."
)

if not datos_input:
    st.info("💡 Por favor, pega la tabla de OneNote arriba para comenzar.")
    st.session_state['procesar'] = False # Resetear si borran el texto
else:
    # Si hay texto, el mensaje de arriba desaparece y sale el botón de procesar
    if st.button("🚀 Procesar Tabla Pegada", use_container_width=True):
        st.session_state['procesar'] = True

# --- PROCESAMIENTO ---
if st.session_state['procesar'] and datos_input:
    try:
        # Diccionario de abreviaciones
        abreviaciones = {
            "1° Teórica": "1° T.",
            "2° Teórica": "2° T.",
            "3° Teórica": "3° T.",
            "4° Teórica": "4° T.",
            "1° Evaluación Clínica": "1° E.C.",
            "2° Evaluación Clínica": "2° E.C.",
            "Caso Clínico": "C.C.",
            "Presentación CC": "P.CC",
            "1° Examen": "1° E.",
            "2° Examen": "2° E."
        }

        df = pd.read_csv(io.StringIO(datos_input.strip()), sep='\t')
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        opciones_disponibles = [opt for opt in abreviaciones.keys() if opt in df['EVALUACION'].unique()]
        otros = [opt for opt in df['EVALUACION'].unique() if opt not in abreviaciones.keys()]
        opciones_finales = opciones_disponibles + otros

        st.divider()
        st.subheader("2. Filtra tu Calendario")
        categoria = st.selectbox("¿Qué calendario vas a actualizar ahora?", opciones_finales)
        
        # Preparar eventos
        df_filtrado = df[df['EVALUACION'] == categoria].copy()
        
        def formatear_titulo(fila):
            eval_orig = fila['EVALUACION']
            asignatura = fila['ASIGNATURA']
            abrev = abreviaciones.get(eval_orig, eval_orig)
            return f"{abrev} {asignatura}"

        calendar_df = pd.DataFrame()
        calendar_df['Subject'] = df_filtrado.apply(formatear_titulo, axis=1)
        calendar_df['Start Date'] = pd.to_datetime(df_filtrado['FECHA'] + "-2026", format='%d-%m-%Y').dt.strftime('%m/%d/%Y')
        calendar_df['End Date'] = calendar_df['Start Date']
        calendar_df['All Day Event'] = 'TRUE'
        calendar_df['Location'] = 'Universidad Mayor, Temuco'
        calendar_df['Private'] = 'TRUE'

        csv = calendar_df.to_csv(index=False).encode('utf-8')
        
        st.success(f"✅ ¡Tabla lista! {len(calendar_df)} eventos de '{categoria}'")
        
        st.download_button(
            label=f"📥 Descargar {categoria}.csv",
            data=csv,
            file_name=f"{categoria}.csv",
            mime='text/csv',
            use_container_width=True
        )
        
        st.dataframe(calendar_df[['Subject', 'Start Date']], use_container_width=True)

    except Exception as e:
        st.error("❌ Error: Verifica que copiaste la tabla completa con sus encabezados.")
