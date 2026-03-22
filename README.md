curl http://localhost:6333/collections

curl -X POST http://localhost:8000/ingest

curl 'http://localhost:8000/ask?q=Xe+VinFast+VF5+có+những+màu+nào?'

curl -G "http://localhost:8000/ask" --data-urlencode "q=Xe VinFast VF5 có những màu nào?"

docker exec -it rag-app llama-cli -m /app/models/qwen.gguf -p "Xe VinFast VF5 có mấy chỗ ngồi?" -n 50
