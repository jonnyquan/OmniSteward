#!/usr/bin/env python
import numpy as np
import torch
import logging
import zerorpc
import threading
import queue
import time

class VADService:
    def __init__(self, vad_threshold: float = 0.5):
        """
        初始化VAD检测服务
        Args:
            vad_threshold: VAD检测的阈值
        """
        self.vad_threshold = vad_threshold
        
        # 加载Silero VAD模型
        self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False)
        logging.info("Silero VAD模型加载完成")
        self.last_use_time = time.time()
    
    def _int2float(self, sound: np.ndarray) -> np.ndarray:
        """将int16音频数据转换为float32"""
        abs_max = np.abs(sound).max()
        sound = sound.astype('float32')
        if abs_max > 0:
            sound *= 1/32768
        sound = sound.squeeze()
        return sound
    
    def detect_speech(self, audio_data: bytes, sample_rate: int = 16000) -> float:
        self.last_use_time = time.time()
        """
        检测音频数据中是否包含语音
        Args:
            audio_data: 原始音频字节数据
            sample_rate: 采样率
        Returns:
            语音概率 (0-1之间的浮点数)
        """
        # 检查音频数据长度
        
        audio_int16 = np.frombuffer(audio_data, np.int16)
        # 将字节数据转换为numpy数组
        audio_float32 = self._int2float(audio_int16)
        inputs = torch.from_numpy(audio_float32)
        # VAD检测
        speech_prob = self.model(
            inputs, 
            sample_rate
        ).item()
        return speech_prob


class VADServiceRPC:
    def __init__(self):
        """初始化VAD RPC服务"""
        self.instances = {}
        self.standby_instance_queue = queue.Queue(maxsize=10)
        self.monitor_thread = threading.Thread(target=self.monitor_instances)
        self.monitor_thread.start()        
        logging.info("VAD RPC服务初始化完成")
        
        
    def monitor_instances(self):
        while True:
            while self.standby_instance_queue.qsize() < 3: # 预先创建实例
                self.standby_instance_queue.put(VADService()) 
            session_ids = list(self.instances.keys())
            for session_id in session_ids:
                if time.time() - self.instances[session_id].last_use_time > 300:
                    self.stop_instance(session_id)
                    print(f"VAD实例{session_id}已停止")
            time.sleep(30)
            
    def detect_speech(self, audio_data: bytes, session_id: str):
        """
        RPC方法：检测音频数据中是否包含语音
        Args:
            audio_data: 原始音频字节数据
        Returns:
            包含检测结果的字典
        """
        try:
            if session_id not in self.instances:
                self.start_instance(session_id)
            vad_instance = self.instances[session_id]
            speech_prob = vad_instance.detect_speech(audio_data)
            return {
                'type': 'detection_result',
                'speech_prob': speech_prob,
                'is_speech': speech_prob >= vad_instance.vad_threshold
            }
        except Exception as e:
            return {
                'type': 'error',
                'error': str(e)
            }
        
    def start_instance(self, session_id: str):
        """
        启动VAD实例, 如果队列中没有实例, 则创建新的实例，否则从队列中获取实例，这样更快
        """
        try:
            vad_instance = self.standby_instance_queue.get(timeout=1)
            self.instances[session_id] = vad_instance
            vad_instance.last_use_time = time.time() # 更新时间戳
        except queue.Empty:
            self.instances[session_id] = VADService()
        
    def stop_instance(self, session_id: str):
        if session_id in self.instances:
            del self.instances[session_id]


def main():
    logging.basicConfig(level=logging.INFO)
    server = zerorpc.Server(VADServiceRPC(), heartbeat=60)
    server.bind("tcp://0.0.0.0:4242")
    logging.info("VAD RPC服务启动成功：tcp://0.0.0.0:4242")
    server.run()

if __name__ == '__main__':
    main()
