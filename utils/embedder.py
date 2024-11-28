import os
import numpy as np
import ollama
import requests


class OllamaNameEmbedder:
    def __init__(self):
        self.name2embed = {}
        self.persist_file = 'name2embed.npy'
        if os.path.exists(self.persist_file):
            self.name2embed = np.load(self.persist_file, allow_pickle=True).item()
    
    def persist(self):
        np.save(self.persist_file, self.name2embed)

    def embed(self, name):
        if name in self.name2embed:
            return self.name2embed[name]
        else:
            embedding = ollama.embeddings(
                model='bge-large',
                prompt=name,
            )['embedding']
            self.name2embed[name] = embedding
            return embedding
        
    def embed_names(self, names):
        embeddings = [self.embed(name) for name in names]
        self.persist()
        return embeddings
        
    def cosine_similarity(self, embed_a, embed_b):
        return np.dot(embed_a, embed_b) / (np.linalg.norm(embed_a) * np.linalg.norm(embed_b))



class SiliconFlowEmbedder:
    def __init__(self, api_key = None):
        if api_key is None:
            raise Exception("api_key 未设置")
        self.url = "https://api.siliconflow.cn/v1/embeddings"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def embed(self, texts):
        if not isinstance(texts, list):
            texts = [texts]
            
        payload = {
            "model": "netease-youdao/bce-embedding-base_v1",
            "encoding_format": "float",
            "input": texts
        }
        
        response = requests.request("POST", self.url, json=payload, headers=self.headers)
        return [data['embedding'] for data in response.json()['data']]
    

if __name__ == "__main__":
    # 使用示例
    embedder = SiliconFlowEmbedder(api_key=os.getenv("SILICON_FLOW_API_KEY", None))
    embeddings = embedder.embed(["hello world", "hello world2"])
    print(len(embeddings[0]))
