import os
import pyaudio
import wave
import requests
import speech_recognition as sr
import io
import urllib.parse

# Konfigurasi API
BASE_URL = "http://192.168.3.1:3000"
SPEECH_TO_SPEECH_API = f"{BASE_URL}/api/speech-to-speech/generate?key=gadingnst&format="
TEXT_TO_SPEECH_API = f"{BASE_URL}/api/text-to-speech/generate?key=gadingnst"
WAKE_WORD = "alexa"

SAMPLE_RATE = 48000  # Gunakan 48000 Hz

def log_ai_headers(response):
  """Menampilkan header AI-Text-Request dan AI-Text-Response jika tersedia"""
  request_text = response.headers.get("AI-Text-Request", "N/A")
  response_text = response.headers.get("AI-Text-Response", "N/A")

  # Decode URI jika header tidak kosong
  request_text = urllib.parse.unquote(request_text) if request_text != "N/A" else "N/A"
  response_text = urllib.parse.unquote(response_text) if response_text != "N/A" else "N/A"

  # Only log if the text is not "N/A"
  if request_text != "N/A":
    print(f"📥 AI-Text-Request: {request_text}")
  if response_text != "N/A":
    print(f"📤 AI-Text-Response: {response_text}")

def send_text_to_speech(text):
  """Mengirim teks ke API TTS dan menerima respon audio MP3"""
  headers = {"Content-Type": "application/json"}
  payload = {"text": text}
  
  response = requests.post(TEXT_TO_SPEECH_API, headers=headers, json=payload)

  if response.status_code == 200:
    print("✅ Received response audio from TTS!")
    log_ai_headers(response)  # Log header AI
    return response.content  # Kembalikan audio MP3 dari API
  else:
    print("❌ Error:", response.status_code, response.text)
    return None

def record_dynamic_audio():
  """Merekam suara dengan 48000 Hz"""
  recognizer = sr.Recognizer()
  mic = sr.Microphone(sample_rate=SAMPLE_RATE)  # Pastikan menggunakan 48000 Hz

  print("🎤 Recording... Speak now!")
  with mic as source:
    recognizer.adjust_for_ambient_noise(source)
    try:
      audio = recognizer.listen(source, timeout=10, phrase_time_limit=3)
    except sr.WaitTimeoutError:
      print("⏳ No response detected, returning to standby mode...")
      return None

  # Simpan ke dalam buffer sebagai WAV
  wav_buffer = io.BytesIO()
  with wave.open(wav_buffer, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)  # 16-bit PCM
    wf.setframerate(SAMPLE_RATE)  # Pastikan 48000 Hz
    wf.writeframes(audio.frame_data)

  return wav_buffer.getvalue()

def send_audio_to_api(audio_data):
  """Mengirim audio WAV ke API dan menerima respon audio MP3"""
  headers = {"content-type": "audio/wav"}
  response = requests.post(SPEECH_TO_SPEECH_API, headers=headers, data=audio_data)

  if response.status_code == 200:
    print("✅ Received response audio!")
    log_ai_headers(response)  # Log header AI
    return response.content  # Kembalikan audio MP3 dari API
  else:
    print("❌ Error:", response.status_code, response.text)
    return None

def play_audio(audio_data):
  """Memainkan audio MP3 dengan mpg123"""
  with open("temp_audio.mp3", "wb") as f:
    f.write(audio_data)
  os.system("mpg123 -q temp_audio.mp3")

def listen_mode():
  """Tetap dalam mode listen hingga tidak ada suara balasan"""
  while True:
    audio_data = record_dynamic_audio()
    if audio_data:
      response_audio = send_audio_to_api(audio_data)
      if response_audio:
        play_audio(response_audio)  # Putar audio yang diterima
    else:
      print("🔕 No more response, returning to standby mode...")
      break  # Keluar dari listen mode jika tidak ada suara

def wake_word_detection():
  """Mendeteksi wake word untuk memulai rekaman"""
  recognizer = sr.Recognizer()
  mic = sr.Microphone(sample_rate=SAMPLE_RATE)

  print(f"🟢 Standby mode... Say '{WAKE_WORD}' to activate listening mode.")

  with mic as source:
    recognizer.adjust_for_ambient_noise(source)

  while True:
    with mic as source:
      try:
        print("🎧 Listening for wake word...")
        audio = recognizer.listen(source)
        text = recognizer.recognize_google(audio).lower()
        print(f"Heard: {text}")

        if WAKE_WORD in text:
          print("🚀 Wake word detected! Sending response...")
          
          # Kirim teks ke API TTS dan mainkan audionya
          response_audio = send_text_to_speech("Ya, saya mendengar Anda. Silakan berbicara.")
          if response_audio:
            play_audio(response_audio)
          
          # Masuk ke mode listen setelah respons pertama
          listen_mode()
          print("🔁 Returning to standby mode...")

      except sr.UnknownValueError:
        print("No wake word detected")
      except sr.RequestError:
        print("Speech recognition service unavailable")

if __name__ == "__main__":
  wake_word_detection()
