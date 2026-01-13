import streamlit as st
import moviepy.editor as mp
import whisper
import tempfile
import os

st.title("🎥 Prototipo: Editor de Video Automático")
st.markdown("### Prefectura del Azuay - Prueba de Concepto")

# Carga del video
uploaded_file = st.file_uploader("Sube el video crudo (.mp4)", type=["mp4"])

if uploaded_file is not None:
    # 1. Guardar el video subido en un archivo temporal
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    st.video(video_path)
    st.write("Video cargado. Presiona el botón para editar.")

    if st.button("🚀 Iniciar Procesamiento Automático"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # --- FASE 1: EDICIÓN DE VIDEO (LOGO + CIERRE) ---
            status_text.text("1/3 Procesando video: Añadiendo logo y cierre...")
            
            # Cargar clips
            clip_principal = mp.VideoFileClip(video_path)
            
            # Intentar cargar outro, si no existe, avisa pero no falla
            try:
                clip_outro = mp.VideoFileClip("outro.mp4")
                # Si el outro es muy grande, lo ajustamos al tamaño del video principal
                if clip_outro.w != clip_principal.w:
                    clip_outro = clip_outro.resize(width=clip_principal.w)
            except:
                st.warning("No se encontró 'outro.mp4', se saltará este paso.")
                clip_outro = None

            # Configurar Logo
            try:
                logo = mp.ImageClip("logo.png")
                logo = logo.resize(height=clip_principal.h * 0.15) # Logo al 15% de altura
                logo = logo.set_duration(clip_principal.duration)
                logo = logo.set_pos(("right", "top")) # Posición
                logo = logo.margin(right=20, top=20, opacity=0)
                
                # Unir video + logo
                clip_con_logo = mp.CompositeVideoClip([clip_principal, logo])
            except:
                st.warning("No se encontró 'logo.png', se saltará el logo.")
                clip_con_logo = clip_principal

            # Unir todo con el cierre
            if clip_outro:
                video_final_editado = mp.concatenate_videoclips([clip_con_logo, clip_outro])
            else:
                video_final_editado = clip_con_logo
            
            progress_bar.progress(50)
            
            # --- FASE 2: INTELIGENCIA ARTIFICIAL (SUBTÍTULOS) ---
            status_text.text("2/3 Escuchando audio para generar subtítulos (IA)...")
            
            # Cargamos el modelo más ligero ('tiny') para que funcione rápido en la nube
            model = whisper.load_model("tiny")
            result = model.transcribe(video_path)
            texto_detectado = result["text"]
            
            progress_bar.progress(80)
            
            # --- FASE 3: EXPORTAR ---
            status_text.text("3/3 Renderizando video final... espera un momento.")
            
            output_path = "video_procesado.mp4"
            # Usamos preset 'ultrafast' para que no demore en la reunión
            video_final_editado.write_videofile(output_path, codec="libx264", preset="ultrafast")
            
            progress_bar.progress(100)
            status_text.success("¡Procesamiento Completado!")
            
            # Mostrar resultados
            st.markdown("#### Resultado:")
            st.video(output_path)
            
            st.info(f"📝 **Transcripción detectada por IA (Para subtítulos):**\n\n{texto_detectado}")
            
            with open(output_path, "rb") as file:
                st.download_button("Descargar Video Final", file, "video_prefectura.mp4")

        except Exception as e:
            st.error(f"Ocurrió un error técnico: {e}")
