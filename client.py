import pyaudio
import wave
import requests
import threading

azuer_server_url = "https://tstapispeech-dnhxfah2d2fzbnf8.southeastasia-01.azurewebsites.net/upload-audio/"
tunnel_url = "https://9f3180f804e3.ngrok-free.app/upload-audio/"
local_url = 'http://localhost:8080/upload-audio/'

current_url = tunnel_url
stop_event = threading.Event()

def record_and_send(filename="output.mp3", seconds = 5):
    def record():
        # Record audio
        chunk = 1024
        fmt = pyaudio.paInt16
        channels = 1
        rate = 44100
        p = pyaudio.PyAudio()
        stream = p.open(format=fmt, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
        print("Recording... (press Enter to stop)")
        frames = []
        while not stop_event.is_set():
            frames.append(stream.read(chunk, exception_on_overflow = False))
        print("Done recording.")
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(fmt))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        with open(filename, 'rb') as f:
            files = {'audio_link': f}
            requests.post(current_url, files = files, data = {'user_id' : '918122378758'})
        
        '''s = "rice1kg,idli"
        requests.post(current_url, data = {'text' : s, 'user_id' : '001'})'''

    # Kick off the recorder thread
    t = threading.Thread(target = record, daemon=True)
    t.start()

    # Wait for user to press Enter
    input()
    stop_event.set()
    t.join()

if __name__ == "__main__":
    record_and_send()

