import requests
import sounddevice as sd
import numpy as np
import wave
import keyboard

url = "https://promoted-solid-gannet.ngrok-free.app/user_request/"
samplerate = 44100
channels = 2
filename = "output.wav"
recording = []

def callback(indata, frames, time, status):
    if status:
        print(status)
    recording.append(indata.copy())
    
def generate_audio():
    with sd.InputStream(samplerate = samplerate, channels = channels, callback = callback):
        print("Recording...")
        input("Press a key to stop.")
    audio_data = np.concatenate(recording, axis = 0)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(samplerate)
        wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
    print(f"Recording saved as {filename}")
    return filename
    
            


if __name__ == "__main__":
    text = ''
    if text:
        requests.post(url, json = {"user_id" : "1", "text" : text})
    else:
        filename = generate_audio()
        requests.post(url, json = {"user_id" : "1", "audio" : filename})
        
        