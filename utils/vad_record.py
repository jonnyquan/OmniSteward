import pyaudio
import time
import uuid
import wave
import zerorpc

class AudioVADRecorder:
    def __init__(self, 
                 server_url: str = "tcp://127.0.0.1:4242",
                 sample_rate: int = 16000,
                 vad_threshold: float = 0.5):
        """
        初始化录音和VAD检测器
        Args:
            server_url: VAD RPC服务地址
            sample_rate: 采样率
            chunk_size: 每次读取的音频样本数
            vad_threshold: VAD检测的阈值
        """
        self.sample_rate = sample_rate
        self.num_samples = 512
        self.vad_threshold = vad_threshold
        
        # 初始化PyAudio
        self.audio = pyaudio.PyAudio()
        self.rpc_client = zerorpc.Client()
        self.rpc_client.connect(server_url)

    def start_recording(self, out_file: str, timeout: float = 3, min_duration: float = 3, max_duration: float = 60):
        """开始录音和VAD检测"""
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        SAMPLE_RATE = self.sample_rate
        CHUNK = int(SAMPLE_RATE / 10) * 4
        session_id = str(uuid.uuid4())
        self.rpc_client.start_instance(session_id)
        stream = self.audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=SAMPLE_RATE,
                            input=True,
                            frames_per_buffer=CHUNK)
        data = []
        start_time = time.time()
        last_speech_time = start_time
        print("开始录音...")
        while True:
            # 读取音频数据
            audio_chunk = stream.read(self.num_samples, exception_on_overflow=False)
            response = self.rpc_client.detect_speech(audio_chunk, session_id)
            speech_prob = response['speech_prob']

            if speech_prob >= self.vad_threshold: # 检测到语音
                last_speech_time = time.time() # 更新语音检测时间
            else:
                exceed_timeout = time.time() - last_speech_time > timeout # 一直没有活动，则结束录音
                longer_than_min_duration = time.time() - start_time > min_duration # 录音时间超过最小时长
                if longer_than_min_duration:
                    print(".", end="", flush=True)
                if exceed_timeout and longer_than_min_duration: # 结束录音
                    break
            if time.time() - start_time > max_duration: # 录音时间超过最大时长
                break
            data.append(audio_chunk)
        print("\n录音结束...")
        self.save_audio(data, out_file)

        try:
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"Error stopping stream: {e}")
        return out_file


    def save_audio(self, data: list, out_file: str):
        """保存录音数据为WAV文件"""
        out_stream = wave.open(out_file, 'wb')
        out_stream.setnchannels(1)
        out_stream.setsampwidth(2)
        out_stream.setframerate(self.sample_rate)
        out_stream.writeframes(b''.join(data))
        out_stream.close()

if __name__ == '__main__':
    vad_recorder = AudioVADRecorder()
    print("开始录音...")
    vad_recorder.start_recording(out_file="test.wav", timeout=1, min_duration=5)