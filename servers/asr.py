from flask import Flask, request, jsonify
from omnisense.models import OmniSenseVoiceSmall
import os

app = Flask(__name__)

# 初始化OmniSense模型
model = OmniSenseVoiceSmall("iic/SenseVoiceSmall", quantize=True, device_id=0)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        # 检查是否有文件上传
        if 'audio' not in request.files:
            return jsonify({'error': '没有上传音频文件'}), 400
        
        audio_file = request.files['audio']
        
        # 获取请求参数，使用默认值
        language = request.form.get('language', 'zh')
        textnorm = request.form.get('textnorm', 'withitn')
        batch_size = int(request.form.get('batch_size', 8))
        timestamps = request.form.get('timestamps', 'false').lower() == 'true'
        
        # 保存上传的音频文件
        temp_path = 'temp_audio.wav'
        audio_file.save(temp_path)
        
        # 进行转写
        result = model.transcribe(
            temp_path,
            language=language,
            textnorm=textnorm,
            batch_size=batch_size,
            timestamps=timestamps
        )
        
        # 删除临时文件
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'text': result[0].text
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
