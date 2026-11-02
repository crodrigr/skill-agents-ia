# MyAgent AI — proyecto terminado

Código final del curso. Guías en [`../../README.md`](../../README.md).

```bash
python3.12 -m venv .venv && source .venv/bin/activate   # Python 3.11 o superior
pip install -r requirements.txt
cp .env.example .env
pytest                                    # 55 pruebas, sin internet
uvicorn app.main:app --reload             # http://localhost:8000/docs
docker compose up -d --build              # API + PostgreSQL + Redis
```

Por defecto usa Ollama (`ollama pull llama3.2` y `ollama pull nomic-embed-text`). Cambia `LLM_PROVIDER` en `.env` para usar `openai` o `claude`.
