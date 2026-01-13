import streamlit as st
import moviepy.editor as mp
from moviepy.config import change_settings
import whisper
import tempfile
import os
import math

# Configuración para que funcione ImageMagick en la nube
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

st.title("🎬 Editor Automático Pro: Subtítulos + Branding")
st.markdown("### Prefectura del Azuay")

uploaded_file = st.file_uploader("Sube el video crudo (.mp4)", type=["mp4"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    st.video(video_path)

    if st.button("🚀 Procesar Video Completo"):
        status = st.empty()
        bar = st.progress(0)
        
        try:
            # 1. Cargar Video
            status.text("Cargando video...")
            video = mp.VideoFileClip(video_path)
            
            # 2. Generar Subtítulos con IA
            status.text("Escuchando audio y generando textos...")
            bar.progress(20)
            model = whisper.load_model("tiny") # Modelo rápido
            result = model.transcribe(video_path)
            
            # Crear clips de texto
            subtitle_clips = []
            for segment in result["segments"]:
                # Configuración del estilo del subtítulo
                txt_clip = mp.TextClip(
                    segment["text"], 
                    fontsize=24, 
                    color='white', 
                    bg_color='rgba(0,0,0,0.6)', # Fondo semitransparente
                    font='Arial-Bold',
                    method='caption',
                    size=(video.w * 0.9, None) # Ancho del 90% del video
                )
                txt_clip = txt_clip.set_start(segment["start"]).set_end(segment["end"])
                txt_clip = txt_clip.set_position(('center', 'bottom')) # Ubicación abajo
                subtitle_clips.append(txt_clip)
            
            # Unir video con subtítulos
            video_con_subs = mp.CompositeVideoClip([video] + subtitle_clips)
            bar.progress(50)

            # 3. Añadir Logo (Intenta buscar logo.png o Logo.png)
            status.text("Añadiendo identidad visual...")
            logo_file = "logo.png" if os.path.exists("logo.png") else "Logo.png"
            
            if os.path.exists(logo_file):
                logo = mp.ImageClip(logo_file).resize(height=80)
                logo = logo.set_duration(video.duration)
                logo = logo.margin(right=20, top=20, opacity=0).set_pos(("right","top"))
                video_con_subs = mp.CompositeVideoClip([video_con_subs, logo])
            else:
                st.warning(f"No encontré {logo_file}, revisa el nombre en GitHub.")

            # 4. Añadir Cierre (Intenta buscar outro.mp4 o Outro.mp4)
            outro_file = "outro.mp4" if os.path.exists("outro.mp4") else "Outro.mp4"
            
            if os.path.exists(outro_file):
                outro = mp.VideoFileClip(outro_file)
                # Ajustar tamaño del outro al video principal
                if outro.w != video.w:
                    outro = outro.resize(width=video.w)
                final_video = mp.concatenate_videoclips([video_con_subs, outro])
            else:
                final_video = video_con_subs
                st.warning(f"No encontré {outro_file}, revisa el nombre en GitHub.")

            # 5. Exportar
            status.text("Renderizando video final (esto toma tiempo)...")
            bar.progress(80)
            output_path = "video_final_con_subs.mp4"
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast", remove_temp=False)
            
            bar.progress(100)
            status.success("¡Video Listo!")
            st.video(output_path)
            
            with open(output_path, "rb") as file:
                st.download_button("Descargar Video", file, "video_prefectura_subs.mp4")

        except Exception as e:
            st.error(f"Error: {e}")
