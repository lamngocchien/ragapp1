from fastapi import FastAPI, BackgroundTasks, Query
import os, subprocess, glob
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

app = FastAPI()
client = QdrantClient(host=os.getenv("QDRANT_HOST", "qdrant"), port=6333)
COLLECTION_NAME = "vf5_docs"
LLAMA_CLI = "/usr/local/bin/llama-cli"
embed_model = None

try:
    if os.path.exists("/app/models/bge-small"):
        embed_model = SentenceTransformer("/app/models/bge-small")
        print("✅ Embedding model loaded!")
except Exception as e:
    print(f"❌ Load error: {e}")

@app.get("/")
async def root():
    return {"status": "Online", "llama_cli_found": os.path.exists(LLAMA_CLI), "model_ready": embed_model is not None}

@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):
    def run_ingestion():
        try:
            client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )
            files = glob.glob("/app/data/*.pdf")
            pid = 0
            for f in files:
                reader = PdfReader(f)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if not text or len(text.strip()) < 10: continue
                    vector = embed_model.encode(text).tolist()
                    client.upsert(
                        collection_name=COLLECTION_NAME,
                        points=[models.PointStruct(id=pid, vector=vector, payload={"text": text, "page": i+1})]
                    )
                    pid += 1
            print(f"✅ Đã nạp {pid} trang.")
        except Exception as e:
            print(f"❌ Ingest error: {e}")
    background_tasks.add_task(run_ingestion)
    return {"message": "Đang nạp dữ liệu..."}

@app.get("/ask")
async def ask(q: str = Query(...)):
    if not os.path.exists(LLAMA_CLI) or not embed_model:
        return {"error": "Hệ thống chưa sẵn sàng"}
    try:
        v = embed_model.encode(q).tolist()
        res = client.search(collection_name=COLLECTION_NAME, query_vector=v, limit=3)
        context = "\n---\n".join([r.payload.get("text", "") for r in res])
        prompt = f"<|im_start|>system\nTrả lời dựa trên ngữ cảnh:\n{context}<|im_end|>\n<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n"
        result = subprocess.run(
            [LLAMA_CLI, "-m", "/app/models/qwen.gguf", "-p", prompt, "-n", "256", "--quiet"],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
        )
        return {"answer": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}
