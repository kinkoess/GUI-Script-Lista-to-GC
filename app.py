import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="OdontoCalendar Tool", page_icon="🦷")
st.title("🦷 OdontoCalendar: OneNote a Google")

# 1. Entrada de datos
st.subheader("1. Pega tu tabla de OneNote")
datos_input = st.text_area("Copia la tabla completa de OneNote y pégala aquí:", height=200, placeholder="EVALUACION\tASIGNATURA\tFECHA...")

# 2. Configuración de Abreviaciones
# Puedes editarlas directamente aquí en el código
abreviaciones = {
    "1° Teórica": "1° T.",
    "2° Teórica": "2° T.",
    "3° Teórica": "3° T.",
    "4° Teórica": "4° T.",
    "1° Evaluación Clínica": "1° E.C.",
    "2° Evaluación Clínica": "2° E.C.",
    "1° Examen": "1° E.",
    "2° Examen": "2° E.",
    "Caso Clínico": "C.C.",
    "Presentación CC": "P.CC"
}

if datos_input:
    try:
        # Procesamiento inicial
        df = pd.read_csv(io.StringIO(datos_input.strip()), sep='\t')
        df.columns = df.columns.str.strip()
        
        # Obtener opciones únicas para el filtro
        opciones_filtro = df['EVALUACION'].unique().tolist()
        
        st.subheader("2. Filtra tu Calendario")
        categoria = st.selectbox("¿Qué calendario vas a actualizar ahora?", opciones_filtro)
        
        # Procesamiento final
        if st.button("Generar Archivo para Google"):
            df_filtrado = df[df['EVALUACION'] == categoria].copy()
            
            def formatear_titulo(fila):
                eval_orig = fila['EVALUACION']
                asignatura = fila['ASIGNATURA']
                abrev = abreviaciones.get(eval_orig, eval_orig)
                return f"{abrev} {asignatura}"

            calendar_df = pd.DataFrame()
            calendar_df['Subject'] = df_filtrado.apply(formatear_titulo, axis=1)
            # Asumimos año 2026 por tus archivos anteriores, o podrías hacerlo dinámico
            calendar_df['Start Date'] = pd.to_datetime(df_filtrado['FECHA'] + "-2026", format='%d-%m-%Y').dt.strftime('%m/%d/%Y')
            calendar_df['End Date'] = calendar_df['Start Date']
            calendar_df['All Day Event'] = 'TRUE'
            calendar_df['Location'] = 'Universidad Mayor, Temuco'
            calendar_df['Private'] = 'TRUE'

            # Botón de descarga
            csv = calendar_df.to_csv(index=False).encode('utf-8')
            st.success(f"¡Listo! Se encontraron {len(calendar_df)} eventos de {categoria}")
            st.download_button(
                label=f"Descargar CSV para {categoria}",
                data=csv,
                file_name=f"calendario_{categoria.lower().replace(' ', '_')}.csv",
                mime='text/csv',
            )
            st.dataframe(calendar_df[['Subject', 'Start Date']]) # Vista previa

    except Exception as e:
        st.error("Error al leer la tabla. Asegúrate de copiarla completa desde OneNote con sus encabezados.")