import uuid

from fastapi import FastAPI, File, UploadFile

app = FastAPI(title="Smart Storage Manager API")

items = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items")
def list_items():
    return items


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    item = {
        "id": str(uuid.uuid4()),
        "filename": file.filename,
        "size_bytes": len(content),
    }
    items.append(item)
    return item
