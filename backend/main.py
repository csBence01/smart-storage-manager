from fastapi import FastAPI

app = FastAPI(title="Smart Storage Manager API")

items = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items")
def list_items():
    return items
