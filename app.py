import streamlit as st
import moviepy.editor as mp
from moviepy.config import change_settings
import whisper
import tempfile
import os

# CONFIGURACIÓN SEGURA DE IMAGEMAGICK
# Intentamos configurar la herramienta de texto. Si falla, no rompe la app, solo avisa.
try:
    if os.path.exists("/usr/bin/convert"):
        change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
    else:
        st.warning("⚠️ Ojo: No encuentro ImageMagick. Los subtítulos podrían fallar.")
except Exception as e:
    st.warning(f"Nota técnica: {e}")

st.title("🎬 Editor Final: Audio + Subtítulos")

uploaded_file = st.file_uploader("Sube el video (.mp4)", type=["mp4"])

if uploaded_file is not None:
    # Guardar temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
        tfile.write(uploaded_file.read())
        video_path = tfile.name
    
    st.video(video_path)

    if st.button("🚀 PROCESAR AHORA"):
        status = st.empty()
        bar = st.progress(0)
        
        try:
            status.text("⏳ Cargando video y audio...")
            video = mp.VideoFileClip(video_path)
            audio_original = video.audio # Guardamos el audio original
            
            # --- SUBTÍTULOS ---
            status.text("🧠 La IA está escuchando...")
            model = whisper.load_model("tiny")
            result = model.transcribe(video_path)
            bar.progress(30)
            
            status.text("✍️ Creando textos...")
            subs = []
            for segment in result["segments"]:
                # Creamos el texto
                txt = segment["text"].strip()
                txt_clip = mp.TextClip(
                    txt, 
                    fontsize=video.h * 0.05, 
                    color='white', 
                    font='Arial', # Fuente básica que siempre existe
                    stroke_color='black', 
                    stroke_width=2,
                    method='caption',
                    size=(video.w * 0.9, None), 
                    align='center'
                )
                txt_clip = txt_clip.set_start(segment["start"]).set_end(segment["end"])
                txt_clip = txt_clip.set_position(('center', 0.8), relative=True)
                subs.append(txt_clip)
            
            # --- LOGO Y CIERRE ---
            status.text("🎨 Montando logo y cierre...")
            elementos_extra = []
            
            # Buscar Logo (cualquier nombre)
            for f in ["logo.png", "Logo.png", "LOGO.png"]:
                if os.path.exists(f):
                    l = mp.ImageClip(f).resize(height=video.h*0.15)
                    l = l.set_duration(video.duration).margin(right=10, top=10, opacity=0).set_pos(("right","top"))
                    elementos_extra.append(l)
                    break
            
            # Mezclar video + subs + logo
            video_final = mp.CompositeVideoClip([video] + subs + elementos_extra)
            video_final.audio = audio_original # Restaurar audio
            
            # Buscar Outro
            for f in ["outro.mp4", "Outro.mp4"]:
                if os.path.exists(f):
                    out = mp.VideoFileClip(f)
                    if out.w != video_final.w: out = out.resize(width=video_final.w)
                    video_final = mp.concatenate_videoclips([video_final, out])
                    break
            
            bar.progress(80)
            status.text("💾 Guardando archivo final...")
            
            output = "video_listo.mp4"
            video_final.write_videofile(
                output, 
                codec='libx264', 
                audio_codec='aac', 
                temp_audiofile='temp-audio.m4a', 
                remove_temp=True, 
                preset='ultrafast'
            )
            
            bar.progress(100)
            status.success("¡Hecho!")
            st.video(output)
            
            with open(output, "rb") as f:
                st.download_button("Descargar Video", f, "video_final.mp4")

        except Exception as e:
            st.error(f"Error: {e}")

