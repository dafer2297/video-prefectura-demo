import streamlit as st
import moviepy.editor as mp
from moviepy.config import change_settings
import whisper
import tempfile
import os

# --- CONFIGURACIÓN CRÍTICA PARA LA NUBE ---
# Esto le dice a Python dónde están las herramientas para texto y video
try:
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
except Exception as e:
    st.error(f"Error grave de configuración: {e}. Verifica packages.txt")
# ------------------------------------------

st.title("Versión 4: Diagnóstico y Reparación")

# === ZONA DE DIAGNÓSTICO ===
st.subheader("🔍 Diagnóstico del Sistema")
st.write("La aplicación está viendo estos archivos en la carpeta principal:")
# Esto nos dirá la verdad sobre qué archivos existen y cómo se llaman
archivos_reales = os.listdir(".")
st.code(archivos_reales, language="text")
st.warning("👉 Comprueba si 'logo.png' y 'outro.mp4' aparecen EXACTAMENTE así en la lista de arriba.")
st.divider()
# ===========================

uploaded_file = st.file_uploader("Sube tu video aquí", type=["mp4"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    st.video(video_path)

    if st.button("🛠️ Procesar Video (Intentar Reparar Todo)"):
        st.info("Iniciando. Por favor, paciencia...")
        bar = st.progress(0)
        
        try:
            # 1. Cargar Video Original
            video_original = mp.VideoFileClip(video_path)
            bar.progress(10)
            
            # 2. Generar Subtítulos (IA)
            st.text("Generando subtítulos...")
            model = whisper.load_model("tiny")
            result = model.transcribe(video_path)
            
            subtitle_clips = []
            for segment in result["segments"]:
                # Intentamos crear el clip de texto. Si falla, es culpa de ImageMagick.
                try:
                    # ESTILO: Texto blanco, borde negro, centrado abajo
                    txt_clip = mp.TextClip(
                        segment["text"], 
                        fontsize=video_original.h * 0.05,
                        color='white', 
                        font='Arial-Bold', 
                        stroke_color='black',
                        stroke_width=2,
                        method='caption',
                        size=(video_original.w * 0.9, None),
                        align='center'
                    )
                    txt_clip = txt_clip.set_start(segment["start"]).set_end(segment["end"])
                    # Posición: Centrado horizontal, al 85% de la altura vertical
                    txt_clip = txt_clip.set_position(('center', 0.85), relative=True)
                    subtitle_clips.append(txt_clip)
                except Exception as e_img:
                     st.error(f"Error creando subtítulos gráficos: {e_img}. ¡Falta ImageMagick en packages.txt!")
                     break # Paramos si no se pueden hacer textos

            bar.progress(40)

            # 3. Buscar Logo (Usando la lista real de archivos)
            st.text("Buscando logo...")
            nombres_posibles_logo = ["logo.png", "Logo.png", "LOGO.png"]
            # Busca cuál de los nombres posibles está en la lista real de archivos
            logo_real = next((f for f in nombres_posibles_logo if f in archivos_reales), None)
            
            clips_capas = [video_original] + subtitle_clips
            
            if logo_real:
                logo_clip = mp.ImageClip(logo_real).resize(height=video_original.h * 0.12)
                logo_clip = logo_clip.set_duration(video_original.duration)
                logo_clip = logo_clip.margin(right=20, top=20, opacity=0).set_pos(("right","top"))
                clips_capas.append(logo_clip)
                st.success(f"Logo encontrado: {logo_real}")
            else:
                st.error("❌ NO SE ENCONTRÓ EL LOGO. Revisa la lista de diagnóstico arriba.")

            # Crear la composición (Video + Subs + Logo)
            video_compuesto = mp.CompositeVideoClip(clips_capas)
            # *** ARREGLO DE AUDIO IMPORTANTE ***
            # Forzamos a que la composición use el audio del video original
            if video_original.audio:
                 video_compuesto.audio = video_original.audio
            else:
                 st.warning("El video original no parece tener audio.")
            
            bar.progress(60)
            
            # 4. Añadir Outro
            st.text("Buscando video de cierre...")
            nombres_posibles_outro = ["outro.mp4", "Outro.mp4", "OUTRO.mp4"]
            outro_real = next((f for f in nombres_posibles_outro if f in archivos_reales), None)
            
            if outro_real:
                outro_clip = mp.VideoFileClip(outro_real)
                if outro_clip.w != video_compuesto.w:
                    outro_clip = outro_clip.resize(width=video_compuesto.w)
                
                final_video = mp.concatenate_videoclips([video_compuesto, outro_clip])
                st.success(f"Cierre encontrado: {outro_real}")
            else:
                final_video = video_compuesto
                st.error("❌ NO SE ENCONTRÓ EL VIDEO DE CIERRE. Revisa la lista de diagnóstico.")

            bar.progress(80)
            
            # 5. Exportar
            st.text("Renderizando video final (puede tardar)...")
            output_path = "video_final_v4.mp4"
            # Usamos una configuración de audio más compatible (aac)
            final_video.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac",
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                preset="ultrafast",
                ffmpeg_params=["-ac", "2"] # Forzar 2 canales de audio
            )
            
            bar.progress(100)
            st.success("¡Proceso terminado!")
            
            st.write("### Resultado Final:")
            st.video(output_path)
            
            with open(output_path, "rb") as f:
                st.download_button("⬇️ Descargar Video Final", f, "video_prefectura_listo.mp4")

        except Exception as e:
            st.error(f"Ocurrió un error técnico inesperado: {e}")
