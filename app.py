import streamlit as st
import moviepy.editor as mp
from moviepy.config import change_settings
import whisper
import tempfile
import os
import shutil

# --- CONFIGURACIÓN OBLIGATORIA PARA LINUX (NUBE) ---
# Esto conecta Python con la herramienta de dibujo
if os.path.exists("/usr/bin/convert"):
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
else:
    st.error("🚨 ERROR CRÍTICO: No encuentro ImageMagick. Revisa tu archivo packages.txt")

st.title("🎬 Editor Final: Audio + Subtítulos + Logo")

# --- DIAGNÓSTICO RÁPIDO ---
st.write("📂 **Archivos detectados en tu carpeta:**")
archivos = os.listdir(".")
st.code(archivos) # Mira aquí si tu logo se llama 'logo.png' o 'Logo.png'

uploaded_file = st.file_uploader("Sube el video (.mp4)", type=["mp4"])

if uploaded_file is not None:
    # Guardar video temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
        tfile.write(uploaded_file.read())
        video_path = tfile.name
    
    st.video(video_path) # Muestra el original para confirmar que tiene audio

    if st.button("🚀 PROCESAR VIDEO (Versión Definitiva)"):
        st.info("⏳ Iniciando... (Esto tarda unos minutos, no cierres la app)")
        bar = st.progress(0)
        
        try:
            # 1. CARGAR VIDEO
            video = mp.VideoFileClip(video_path)
            audio_original = video.audio # Guardamos el audio aparte por seguridad
            
            # 2. IA DE SUBTÍTULOS
            st.text("🧠 Escuchando audio...")
            model = whisper.load_model("tiny")
            result = model.transcribe(video_path)
            bar.progress(30)

            # 3. CREAR SUBTÍTULOS (QUEMADOS EN IMAGEN)
            st.text("✍️ Dibujando subtítulos en el video...")
            subs = []
            for segment in result["segments"]:
                txt = segment["text"].strip()
                # Configuración a prueba de fallos para el texto
                txt_clip = mp.TextClip(
                    txt, 
                    fontsize=video.h * 0.06, # Tamaño relativo (6%)
                    color='white', 
                    bg_color='rgba(0,0,0,0.5)', # Fondo negro semitransparente
                    font='Dejavu-Sans', # Fuente segura en Linux
                    method='caption', # Auto-ajuste de ancho
                    size=(video.w * 0.9, None), # Ancho máximo
                    align='center'
                )
                txt_clip = txt_clip.set_start(segment["start"]).set_end(segment["end"])
                # Posición: Abajo al centro
                txt_clip = txt_clip.set_position(('center', 0.8), relative=True)
                subs.append(txt_clip)

            # 4. BUSCAR LOGO (Insensible a mayúsculas)
            logo_final = None
            for nombre in ["logo.png", "Logo.png", "LOGO.png"]:
                if os.path.exists(nombre):
                    logo_clip = mp.ImageClip(nombre).resize(height=video.h * 0.15)
                    logo_clip = logo_clip.set_duration(video.duration)
                    logo_clip = logo_clip.margin(right=20, top=20, opacity=0).set_pos(("right","top"))
                    logo_final = logo_clip
                    st.success(f"✅ Logo encontrado: {nombre}")
                    break
            
            # 5. BUSCAR OUTRO
            outro_final = None
            for nombre in ["outro.mp4", "Outro.mp4"]:
                if os.path.exists(nombre):
                    outro_clip = mp.VideoFileClip(nombre)
                    if outro_clip.w != video.w:
                        outro_clip = outro_clip.resize(width=video.w)
                    outro_final = outro_clip
                    st.success(f"✅ Outro encontrado: {nombre}")
                    break

            # 6. MEZCLAR TODO
            st.text("🎨 Componiendo video final...")
            # Capas: Video Fondo + Subtítulos + Logo (si existe)
            capas = [video] + subs
            if logo_final:
                capas.append(logo_final)
            
            video_editado = mp.CompositeVideoClip(capas)
            
            # Restaurar Audio explícitamente
            video_editado.audio = audio_original

            # Unir con Outro (si existe)
            if outro_final:
                video_final = mp.concatenate_videoclips([video_editado, outro_final])
            else:
                video_final = video_editado

            bar.progress(70)

            # 7. EXPORTAR (Configuración para arreglar el sonido)
            output_file = "video_completo.mp4"
            video_final.write_videofile(
                output_file, 
                codec='libx264', 
                audio_codec='aac', # Codec universal de audio
                temp_audiofile='temp-audio.m4a', 
                remove_temp=True,
                preset='ultrafast', # Renderizado rápido
                fps=24
            )
            
            bar.progress(100)
            st.success("¡ÉXITO! Video generado correctamente.")
            
            # Mostrar resultado
            st.video(output_file)
            
            with open(output_file, "rb") as f:
                st.download_button("⬇️ Descargar Video Listo", f, "video_prefectura.mp4")

        except Exception as e:
            st.error(f"❌ Ocurrió un error: {e}")
            st.warning("Si el error menciona 'ImageMagick', verifica el archivo packages.txt")

