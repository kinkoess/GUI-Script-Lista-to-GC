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

    /* Cambiar el borde de rojo a VERDE cuando el cuadro de texto está activo */
    textarea:focus {
        border-color: #28a745 !important;
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
    }
    
    /* Hacer el título del área de texto más visible */
    .stTextArea label {
        font-size: 1.2rem !important;
        font-weight: bold !important;
        color: #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Título con el salto de línea que pediste
st.markdown("# 🦷 OdontoCalendar:  \n# Tabla OneNote a Google Calendar")

# 1. Entrada de datos
st.subheader("1. Carga de Datos")
datos_input = st.text_area("📋 Pega tu tabla de OneNote aquí:", height=200, placeholder="EVALUACION\tASIGNATURA\tFECHA...")

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

# LÓGICA DE DETECCIÓN DE TEXTO
if not datos_input:
    st.info("💡 Por favor, pega la tabla de OneNote arriba para comenzar.")
else:
    # Botón grande para "confirmar" el pegado sin usar Ctrl+Enter obligatoriamente para ver cambios
    if st.button("🚀 Procesar Tabla Pegada"):
        st.session_state['procesar'] = True
    
    if st.session_state.get('procesar'):
        try:
            df = pd.read_csv(io.StringIO(datos_input.strip()), sep='\t')
            df.columns = df.columns.str.strip()
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            
            opciones_disponibles = [opt for opt in abreviaciones.keys() if opt in df['EVALUACION'].unique()]
            otros = [opt for opt in df['EVALUACION'].unique() if opt not in abreviaciones.keys()]
            opciones_finales = opciones_disponibles + otros

            st.divider()
            st.subheader("2. Filtra tu Calendario")
            categoria = st.selectbox("¿Qué calendario vas a actualizar ahora?", opciones_finales)
            
            # Preparar descarga
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
            
            st.success(f"✅ ¡Tabla detectada! {len(calendar_df)} eventos encontrados para {categoria}")
            
            st.download_button(
                label=f"📥 Descargar {categoria}.csv",
                data=csv,
                file_name=f"{categoria}.csv",
                mime='text/csv',
                use_container_width=True # Botón a lo ancho para que sea fácil clickear
            )
            
            st.dataframe(calendar_df[['Subject', 'Start Date']], use_container_width=True)

        except Exception as e:
            st.error("❌ Error: La tabla no tiene el formato correcto. Asegúrate de incluir los encabezados.")
