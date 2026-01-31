import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Tuple
import openai

from src.config import get_settings

settings = get_settings()


class VectorService:
    """向量搜索服务 - 使用 ChromaDB"""
    
    def __init__(self):
        # 初始化 ChromaDB 客户端
        self.client = chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=settings.chroma_persist_dir,
            anonymized_telemetry=False
        ))
        
        # 获取或创建任务集合
        self.collection = self.client.get_or_create_collection(
            name="tasks",
            metadata={"hnsw:space": "cosine"}
        )
        
        # OpenAI 客户端
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def add_task(self, task_id: str, title: str, description: str = None):
        """添加任务到向量数据库"""
        # 组合文本
        text = title
        if description:
            text = f"{title}. {description}"
        
        # 获取向量
        embedding = self._get_embedding(text)
        
        # 添加到集合
        self.collection.add(
            ids=[task_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{"title": title}]
        )
    
    def update_task(self, task_id: str, title: str, description: str = None):
        """更新任务向量"""
        # 先删除旧的
        try:
            self.collection.delete(ids=[task_id])
        except:
            pass
        # 重新添加
        self.add_task(task_id, title, description)
    
    def delete_task(self, task_id: str):
        """从向量数据库删除任务"""
        try:
            self.collection.delete(ids=[task_id])
        except:
            pass
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """语义搜索，返回 [(task_id, score), ...]"""
        # 获取查询向量
        query_embedding = self._get_embedding(query)
        
        # 搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # 返回结果
        if not results['ids'][0]:
            return []
        
        return list(zip(
            results['ids'][0],
            results['distances'][0] if results['distances'] else [0] * len(results['ids'][0])
        ))


# 单例
_vector_service = None

def get_vector_service() -> VectorService:
    """获取向量服务单例"""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
