import socket

class BemfaTCPClient:
    def __init__(self, uid, topic):
        self.server_address = ('bemfa.com', 8344)
        self.uid = uid
        self.topic = topic
        
    def send_message(self, msg):
        # 构建发送消息的指令
        publish_cmd = f'cmd=2&uid={self.uid}&topic={self.topic}&msg={msg}\r\n'
        
        # 创建socket连接并发送消息
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(self.server_address)
                print(f"已连接到 {self.server_address[0]}:{self.server_address[1]}")
                
                s.sendall(publish_cmd.encode('utf-8'))
                print(f"已发送消息: {publish_cmd}")
                
                response = s.recv(1024)
                print(f"收到响应: {response.decode('utf-8')}")
                return response.decode('utf-8')
                
            except Exception as e:
                print(f"发送消息时出错: {str(e)}")
                return None

# 使用示例:
if __name__ == '__main__':
    uid = 'b973c7aabf4848b891c875c6e736208b'
    topic = 'A59FE5002'
    
    client = BemfaTCPClient(uid, topic)
    client.send_message('cycle:clear')