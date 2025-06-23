import chromadb
import requests


class MyEmbeddingFunction:
    def __init__(self, embed_func):
        self.embed_func = embed_func
    def __call__(self, input):
        # Debug: 检查 embed_func 类型
        if not callable(self.embed_func):
            raise TypeError(f"MyEmbeddingFunction.embed_func 不是可调用对象，而是 {type(self.embed_func)}，值为 {self.embed_func}")
        if isinstance(input, str):
            input = [input]
        return [self.embed_func(t) for t in input]
    def name(self):
        return "MyEmbeddingFunction"

class FinancialSituationMemory:
    def __init__(self, collection_name, config):
        self.config = config
        self.chroma_client = chromadb.PersistentClient(path=self.config.get('db_path', ".chromadb"))
        self.base_url = self.config.get("backend_url")
        self.api_key = self.config.get("openai_api_key", "")
        self.embedding_model = self.config.get("embedding_model", "text-embedding-3-small")
        if not self.base_url or not self.base_url.startswith("http"):
            raise ValueError("backend_url 未配置或格式错误，请检查 config['backend_url']")
        # 先强制删除旧的collection，确保embedding_function生效
        try:
            self.chroma_client.delete_collection(collection_name)
        except Exception:
            pass
        self.situation_collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=MyEmbeddingFunction(self.get_embedding)
        )

    def get_embedding(self, text):
        url = self.base_url.rstrip("/")
        if not url.endswith("/embeddings"):
            url = url + "/embeddings"
        headers = {"Content-Type": "application/json"}
        # 只用 Authorization: Bearer <API_KEY>
        print(f"[Embedding] 当前使用的 api_key: {self.api_key!r}")
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        print(f"[Embedding请求] headers: {headers}")
        data = {
            "input": text,
            "model": self.embedding_model
        }
        print(f"[Embedding请求] url: {url}")
        print(f"[Embedding请求] data: {data}")
        response = requests.post(url, headers=headers, json=data)
        print(f"[Embedding响应] status: {response.status_code}")
        print(f"[Embedding响应] text: {response.text}")
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]
        else:
            raise RuntimeError(f"Embedding API调用失败: {response.status_code} {response.text}")

    def add_memory(self, memory_dict: dict):
        """Add a single memory entry from a dictionary."""
        situation = memory_dict.get("situation")
        recommendation = memory_dict.get("recommendation")
        
        if not situation or not recommendation:
            print("Warning: 'situation' or 'recommendation' not in memory_dict")
            return
            
        count = self.situation_collection.count()
        doc_id = str(count + 1)
        
        embedding = self.get_embedding(situation)
        self.situation_collection.add(
            documents=[situation],
            metadatas=[{"recommendation": recommendation}],
            embeddings=[embedding],
            ids=[doc_id]
        )

    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations."""
        query_embedding = self.get_embedding(current_situation)
        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                matched_results.append(
                    {
                        "matched_situation": results["documents"][0][i],
                        "recommendation": results["metadatas"][0][i]["recommendation"],
                        "similarity_score": 1 - results["distances"][0][i],
                    }
                )
        return matched_results


if __name__ == "__main__":
    # Example usage
    config = {
        "openai_api_key": "YOUR_OPENAI_API_KEY", # IMPORTANT: Replace with your key
        "backend_url": "https://api.openai.com/v1"
    }
    matcher = FinancialSituationMemory("example_memory", config)

    # Example data
    example_data = [
        {
            "situation": "High inflation rate with rising interest rates and declining consumer spending",
            "recommendation": "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        },
        {
            "situation": "Tech sector showing high volatility with increasing institutional selling pressure",
            "recommendation": "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        }
    ]

    # Add the example situations and recommendations
    for data in example_data:
        matcher.add_memory(data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
