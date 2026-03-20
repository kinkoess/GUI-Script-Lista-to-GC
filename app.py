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

# Contenedor para el mensaje inicial
contenedor_mensaje = st.empty()

# ÁREA DE TEXTO
datos_input = st.text_area(
    label="Input_Tabla",
    height=150, 
    placeholder="Pega aquí tu tabla de OneNote..."
)

# Lógica del mensaje de bienvenida
if not datos_input:
    contenedor_mensaje.info("💡 Por favor, pega la tabla de OneNote arriba para comenzar.")
    st.session_state['procesar'] = False
else:
    contenedor_mensaje.empty()
    if st.button("🚀 Procesar Tabla Pegada", use_container_width=True):
        st.session_state['procesar'] = True

# --- PROCESAMIENTO ---
if st.session_state.get('procesar') and datos_input:
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

        # Leer tabla
        df = pd.read_csv(io.StringIO(datos_input.strip()), sep='\t')
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        st.divider()
        
        # NUEVO PASO INTERMEDIO: Selección de Modo
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
            st.info("ℹ️ Se exportarán todos los eventos detectados en la tabla.")
            
        else:
            # Lógica de filtrado existente
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
        calendar_df['Start Date'] = pd.to_datetime(df_final['FECHA'] + "-2026", format='%d-%m-%Y').dt.strftime('%m/%d/%Y')
        calendar_df['End Date'] = calendar_df['Start Date']
        calendar_df['All Day Event'] = 'TRUE'
        calendar_df['Location'] = 'Universidad Mayor, Temuco'
        calendar_df['Private'] = 'TRUE'

        csv = calendar_df.to_csv(index=False).encode('utf-8')
        
        st.success(f"✅ ¡Datos listos! {len(calendar_df)} eventos encontrados.")
        
        st.download_button(
            label=f"📥 Descargar {nombre_archivo}",
            data=csv,
            file_name=nombre_archivo,
            mime='text/csv',
            use_container_width=True
        )
        
        st.dataframe(calendar_df[['Subject', 'Start Date']], use_container_width=True)

    except Exception as e:
        st.error("❌ Error: La tabla no tiene el formato esperado. Asegúrate de copiar los encabezados.")
