import streamlit as st
import os
import tempfile
from pytube import YouTube
from moviepy.editor import *
import requests
import whisper
import openai
import string
import codecs
import io
from gtts import gTTS
from pydub import AudioSegment
from pydub.silence import detect_silence
import librosa


# --- Function Definitions ---

def download_youtube_video_tonewName(url):
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    filename = stream.download()
    new_filename = "music.mp3"
    os.rename(filename, new_filename)

    # 轉換音訊編解碼器
    sound = AudioSegment.from_file(new_filename)
    sound.export(new_filename, format="mp3", bitrate="192k")

    return new_filename    
    

def download_youtube_video(url):
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    return stream.download()

def extract_audio_from_video(video_path):
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
      
        audioclip = AudioFileClip(video_path)

        allAudio = []
      # 切割音訊
        duration = audioclip.duration
        start_time = 0 # 起始時間，單位為秒
        end_time = 660 # 結束時間，單位為秒
        count = 1
        while start_time < duration:
            if end_time > duration:
                end_time = duration
            # 切割音訊
            new_audioclip = audioclip.subclip(start_time, end_time)

            name = temp_audio.name
            # 使用 replace() 函数删除空格
            name = name.replace(" ", "")

            # 使用 translate() 函数删除标点符号
            name = name.translate(str.maketrans("", "", string.punctuation))

            # 儲存音訊
            output_path = "{}_{}.mp3".format(temp_audio.name,count)
            new_audioclip.audio.write_audiofile(output_path,  codec='mp3')
         
            allAudio.append(output_path)

            start_time = end_time
            end_time += 660
            count += 1
        
        audioclip.close()
        return allAudio


# --- Streamlit App ---

st.title("YouTube to Text with OpenAI")

# --- Sidebar for API Key Input ---
with st.sidebar:
    st.title("Settings")
    st.markdown("### Enter your OpenAI API Key below:")
    
    # Initialize session state for the API key
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
        
    # Input field for the API key
    st.session_state.api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="Enter your OpenAI API key",
        key="api_key_input"
    )
    
    # Display the current status of the API key
    if st.session_state.api_key:
        st.success("API Key saved successfully!")
        openai.api_key = st.session_state.api_key  # Set the OpenAI API key
    else:
        st.warning("Please enter your API Key.")

# --- Main App Content ---

youtube_url = st.text_input("Enter YouTube URL:")

if st.button("Process YouTube Video"):
    if not st.session_state.api_key:
        st.error("Please enter your OpenAI API Key in the sidebar.")
    elif youtube_url:
        try:
            st.info("Downloading and processing audio...")
            audio_file_name = download_youtube_video_tonewName(youtube_url) 
            st.success(f"Audio downloaded: {audio_file_name}")

            st.info("Extracting audio from video...")
            audio_chunks = extract_audio_from_video(audio_file_name)
            st.success(f"Audio extracted into {len(audio_chunks)} chunks.")

            full_text = ""
            for i, chunk in enumerate(audio_chunks):
                st.info(f"Transcribing chunk {i+1}/{len(audio_chunks)}...")
                try:
                   
                    with open(chunk, "rb") as audio_file:
                        transcript = openai.Audio.transcribe("whisper-1", audio_file)
                        text = transcript["text"]
                        full_text += text + "\n\n"
                    st.success(f"Chunk {i+1} transcribed.")
                except Exception as e:
                    st.error(f"Error transcribing chunk {i+1}: {e}")
                    break #Stop if one chunk fails. consider logging or skipping instead.
            
            st.subheader("Transcription:")
            st.write(full_text)

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a YouTube URL.")
