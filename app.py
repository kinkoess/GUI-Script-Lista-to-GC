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
    
    /* Escondemos la etiqueta original del text_area */
    .stTextArea label {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

# Título con salto de línea
st.markdown("# 🦷 OdontoCalendar:  \n# Tabla OneNote a Google Calendar")

st.subheader("1. Carga de Datos")

# CREAMOS UN CONTENEDOR PARA EL MENSAJE
# Esto permite que el mensaje "vuele" en cuanto hay texto
contenedor_mensaje = st.empty()

# ÁREA DE TEXTO
datos_input = st.text_area(
    label="Input_Tabla",
    height=150, 
    placeholder="Pega aquí tu tabla de OneNote..."
)

# LÓGICA INSTANTÁNEA
if not datos_input:
    contenedor_mensaje.info("💡 Por favor, pega la tabla de OneNote arriba para comenzar.")
    # Resetear el estado de procesamiento si se borra el texto
    st.session_state['procesar'] = False
else:
    # SI HAY TEXTO, EL CONTENEDOR SE VACÍA INMEDIATAMENTE
    contenedor_mensaje.empty()
    
    # Aparece el botón de procesar de una vez
    if st.button("🚀 Procesar Tabla Pegada", use_container_width=True):
        st.session_state['procesar'] = True

# --- PROCESAMIENTO ---
if st.session_state.get('procesar') and datos_input:
    try:
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

        # Leer tabla (OneNote usa tabuladores \t)
        df = pd.read_csv(io.StringIO(datos_input.strip()), sep='\t')
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        opciones_disponibles = [opt for opt in abreviaciones.keys() if opt in df['EVALUACION'].unique()]
        otros = [opt for opt in df['EVALUACION'].unique() if opt not in abreviaciones.keys()]
        opciones_finales = opciones_disponibles + otros

        st.divider()
        st.subheader("2. Filtra tu Calendario")
        categoria = st.selectbox("¿Qué calendario vas a actualizar ahora?", opciones_finales)
        
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
        
        st.success(f"✅ ¡Tabla detectada! {len(calendar_df)} eventos encontrados.")
        
        st.download_button(
            label=f"📥 Descargar {categoria}.csv",
            data=csv,
            file_name=f"{categoria}.csv",
            mime='text/csv',
            use_container_width=True
        )
        
        st.dataframe(calendar_df[['Subject', 'Start Date']], use_container_width=True)

    except Exception as e:
        st.error("❌ Error: La tabla no tiene el formato esperado. Asegúrate de copiar los encabezados.")
