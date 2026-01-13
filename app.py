import streamlit as st
import moviepy.editor as mp
from moviepy.config import change_settings
import whisper
import tempfile
import os

# Configuración necesaria para la nube
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

st.title("Versión 3: Audio Reparado + Subtítulos Visibles")

# --- DIAGNÓSTICO DE ARCHIVOS (Esto te dirá qué nombres ve el sistema) ---
st.write("📂 **Archivos detectados en la carpeta:**")
archivos_en_carpeta = os.listdir(".")
st.code(archivos_en_carpeta) # Muestra la lista en pantalla
# -----------------------------------------------------------------------

uploaded_file = st.file_uploader("Sube tu video aquí", type=["mp4"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    st.video(video_path)

    if st.button("🔴 Procesar Video (Con Audio y Subs)"):
        st.info("Iniciando procesamiento... Por favor espera.")
        bar = st.progress(0)
        
        try:
            # 1. Cargar Video
            video = mp.VideoFileClip(video_path)
            
            # 2. Generar Subtítulos (IA)
            model = whisper.load_model("tiny")
            result = model.transcribe(video_path)
            
            subtitle_clips = []
            for segment in result["segments"]:
                # ESTILO INSTAGRAM: Texto blanco con borde negro
                txt_clip = mp.TextClip(
                    segment["text"], 
                    fontsize=video.h * 0.05, # El tamaño depende de la altura del video (5%)
                    color='white', 
                    font='Arial-Bold', 
                    stroke_color='black', # Borde negro para legibilidad
                    stroke_width=2,
                    method='caption',
                    size=(video.w * 0.9, None) # Ancho máximo
                )
                txt_clip = txt_clip.set_start(segment["start"]).set_end(segment["end"])
                
                # POSICIÓN: 'center' horizontal, y al 80% de altura (no al fondo del todo)
                txt_clip = txt_clip.set_position(('center', 0.8), relative=True)
                subtitle_clips.append(txt_clip)
            
            bar.progress(40)

            # 3. Buscar Logo (Automático)
            # Buscamos si existe alguno de estos nombres
            posibles_logos = ["logo.png"]
            logo_real = next((f for f in posibles_logos if os.path.exists(f)), None)
            
            clips_a_mezclar = [video] + subtitle_clips
            
            if logo_real:
                logo = mp.ImageClip(logo_real).resize(height=video.h * 0.1) # 10% de altura
                logo = logo.set_duration(video.duration)
                logo = logo.margin(right=20, top=20, opacity=0).set_pos(("right","top"))
                clips_a_mezclar.append(logo)
            else:
                st.warning("⚠️ No encontré el archivo del logo (revisa la lista de arriba).")

            # Mezclar todo (Video + Subs + Logo)
            video_procesado = mp.CompositeVideoClip(clips_a_mezclar)
            
            # FORZAR AUDIO: Aseguramos que el video final tenga el audio del original
            video_procesado.audio = video.audio
            
            # 4. Añadir Outro
            posibles_outros = ["outro.mp4"]
            outro_real = next((f for f in posibles_outros if os.path.exists(f)), None)
            
            if outro_real:
                outro = mp.VideoFileClip(outro_real)
                # Ajustar tamaño
                if outro.w != video_procesado.w:
                    outro = outro.resize(width=video_procesado.w)
                
                final_video = mp.concatenate_videoclips([video_procesado, outro])
            else:
                final_video = video_procesado
                st.warning("⚠️ No encontré el archivo de cierre (revisa la lista de arriba).")

            bar.progress(70)
            
            # 5. Exportar (Configuración especial para audio)
            output_path = "video_final_v3.mp4"
            final_video.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", # Codec de audio estándar
                temp_audiofile='temp-audio.m4a', 
                remove_temp=True, 
                preset="ultrafast"
            )
            
            bar.progress(100)
            st.success("¡Video generado con sonido!")
            
            st.video(output_path)
            
            with open(output_path, "rb") as f:
                st.download_button("Descargar Video Final", f, "video_listo.mp4")

        except Exception as e:
            st.error(f"Error técnico: {e}")
