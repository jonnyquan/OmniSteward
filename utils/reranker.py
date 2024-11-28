import requests
import os
from typing import List

class Reranker: 
    def __init__(self, api_key = None):
        self.api_key = api_key

    def __call__(self, query: str, documents: List[str], top_n: int = 10) -> dict:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 待排序文档列表
            top_n: 返回前n个结果
        
        Returns:
            重排序结果
        """
        url = "https://api.siliconflow.cn/v1/rerank"
        
        payload = {
            "model": "BAAI/bge-reranker-v2-m3",
            "query": query,
            "documents": documents,
            "top_n": top_n,
            "return_documents": False,
            "max_chunks_per_doc": 123,
            "overlap_tokens": 79
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # 检查HTTP错误
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"重排序API调用失败: {str(e)}")

if __name__ == "__main__":
    # 示例使用
    query = "Apple"
    documents = ["苹果", "香蕉", "水果", "蔬菜"]
    reranker = Reranker(api_key=os.getenv("SILICON_FLOW_API_KEY", None))
    try:
        result = reranker.rerank_documents(query, documents)
        print(result)
    except Exception as e:
        print(f"错误: {str(e)}")