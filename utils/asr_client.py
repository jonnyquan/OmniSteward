import sounddevice as sd
import soundfile as sf
import requests
import os
import time
from utils.vad_record import AudioVADRecorder
from typing import Callable

class LocalASR:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url

    def __call__(self, audio: str | bytes, language='auto', textnorm='withitn', batch_size=8, timestamps=False):
        # 使用服务器进行转写
        if isinstance(audio, str):
            with open(audio, 'rb') as f:
                audio = f.read()
        else:
            assert isinstance(audio, bytes), "audio must be a bytes object"
        files = {'audio': audio}
        data = {
            'language': language,
            'textnorm': textnorm,
            'batch_size': batch_size,
            'timestamps': timestamps
        }
        response = requests.post(f"{self.server_url}/transcribe", files=files, data=data)
        response.raise_for_status()
        result = response.json()
        return result['text']
    

class OnlineASR:
    def __init__(self, api_key = None):
        if api_key is None:
            raise Exception("api_key 未设置")
        self.api_key = api_key
        self.url = "https://api.siliconflow.cn/v1/audio/transcriptions"
        self.model = 'FunAudioLLM/SenseVoiceSmall'
    
    def __call__(self, audio: str | bytes, **kwargs):
        # 处理音频文件输入
        if isinstance(audio, str):
            with open(audio, 'rb') as f:
                audio = f.read()    
        else:
            assert isinstance(audio, bytes), "audio must be a bytes object"
        files = {
            'file': ('audio.wav', audio, 'audio/wav')
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            'model': self.model,
        }
        response = requests.post(self.url, headers=headers, files=files, data=data)
        return response.json()['text']


class ASR:
    def __init__(self, transcribe: Callable, vad_server_url="tcp://127.0.0.1:4242"):
        self.transcribe = transcribe
        self.vad_server_url = vad_server_url
        self.sample_rate = 16000
        self.vad_recorder = AudioVADRecorder(server_url=self.vad_server_url, sample_rate=self.sample_rate)
        self.audio_path = 'recording.wav'
        

    def record_audio(self, duration=5):
        # 录制音频
        print("开始录音...")
        recording = sd.rec(int(duration * self.sample_rate), 
                        samplerate=self.sample_rate, 
                        channels=1)
        sd.wait()  # 等待录音完成
        print("录音结束")

        # 保存录音文件
        sf.write(self.audio_path, recording, self.sample_rate)

        return self.audio_path
    
    def record_and_transcribe(self, duration=5, language='auto', textnorm='withitn', batch_size=8, timestamps=False):
        audio_path = self.record_audio(duration=duration)
        text = self.transcribe(audio_path, language=language, textnorm=textnorm, batch_size=batch_size, timestamps=timestamps)
        os.remove(audio_path)
        return text
    

    def auto_record_and_transcribe(self, duration=5, language='auto', textnorm='withitn', batch_size=8, timestamps=False):
        out_file = self.audio_path
        self.vad_recorder.start_recording(out_file=out_file, timeout=2, min_duration=duration)
        start = time.time()
        text = self.transcribe(out_file, language=language, textnorm=textnorm, batch_size=batch_size, timestamps=timestamps)
        print(f"【转写时间】：{time.time() - start:.2f}秒")
        os.remove(out_file)
        return text


if __name__ == '__main__':  
    asr = ASR()
    result = asr.record_and_transcribe(duration=5)
    print("转写结果:", result)
