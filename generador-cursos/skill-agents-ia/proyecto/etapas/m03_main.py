from fastapi import FastAPI

app = FastAPI(title="MyAgent AI", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
