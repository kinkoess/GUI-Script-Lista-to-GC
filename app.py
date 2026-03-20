import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="OdontoCalendar Tool", page_icon="🦷")

# --- ESTILO PARA OCULTAR SOLO EL BOTÓN DE LA TABLA ---
st.markdown("""
    <style>
    /* Esto oculta el menú de opciones que sale sobre las tablas/dataframes */
    [data-testid="stElementToolbar"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🦷 OdontoCalendar: OneNote a Google")

# 1. Entrada de datos
st.subheader("1. Pega tu tabla de OneNote")
datos_input = st.text_area("Copia la tabla completa de OneNote y pégala aquí:", height=200, placeholder="EVALUACION\tASIGNATURA\tFECHA...")

# 2. Diccionario con el ORDEN y ABREVIACIONES exactas
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

if datos_input:
    try:
        # Procesamiento inicial
        df = pd.read_csv(io.StringIO(datos_input.strip()), sep='\t')
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        # Filtramos las opciones respetando tu orden
        opciones_disponibles = [opt for opt in abreviaciones.keys() if opt in df['EVALUACION'].unique()]
        otros = [opt for opt in df['EVALUACION'].unique() if opt not in abreviaciones.keys()]
        opciones_finales = opciones_disponibles + otros

        st.subheader("2. Filtra tu Calendario")
        categoria = st.selectbox("¿Qué calendario vas a actualizar ahora?", opciones_finales)
        
        if st.button("Generar Archivo para Google"):
            # Filtro estricto
            df_filtrado = df[df['EVALUACION'] == categoria].copy()
            
            def formatear_titulo(fila):
                eval_orig = fila['EVALUACION']
                asignatura = fila['ASIGNATURA']
                abrev = abreviaciones.get(eval_orig, eval_orig)
                return f"{abrev} {asignatura}"

            calendar_df = pd.DataFrame()
            calendar_df['Subject'] = df_filtrado.apply(formatear_titulo, axis=1)
            # Año 2026 configurado
            calendar_df['Start Date'] = pd.to_datetime(df_filtrado['FECHA'] + "-2026", format='%d-%m-%Y').dt.strftime('%m/%d/%Y')
            calendar_df['End Date'] = calendar_df['Start Date']
            calendar_df['All Day Event'] = 'TRUE'
            calendar_df['Location'] = 'Universidad Mayor, Temuco'
            calendar_df['Private'] = 'TRUE'

            # Botón de descarga
            csv = calendar_df.to_csv(index=False).encode('utf-8')
            st.success(f"¡Listo! Se encontraron {len(calendar_df)} eventos para {categoria}")
            
            nombre_archivo_final = f"{categoria}.csv"
            
            # Botón con el icono de descarga
            st.download_button(
                label=f"📥 Descargar archivo: {nombre_archivo_final}",
                data=csv,
                file_name=nombre_archivo_final,
                mime='text/csv',
            )
            
            # Vista previa limpia
            st.dataframe(calendar_df[['Subject', 'Start Date']], use_container_width=True) 

    except Exception as e:
        st.error(f"Error al procesar: Asegúrate de que las columnas se llamen EVALUACION, ASIGNATURA y FECHA.")
