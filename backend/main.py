import datetime
import os
import uuid

from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import FastAPI, File, UploadFile

STORAGE_CONNECTION_STRING = os.environ["STORAGE_CONNECTION_STRING"]
COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
COSMOS_DB = os.getenv("COSMOS_DB", "smartstorage")
BLOB_CONTAINER = os.getenv("BLOB_CONTAINER", "raw-uploads")

blob_container = BlobServiceClient.from_connection_string(
    STORAGE_CONNECTION_STRING
).get_container_client(BLOB_CONTAINER)

database = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY).get_database_client(COSMOS_DB)
items_container = database.get_container_client("items")
transactions_container = database.get_container_client("transactions")

app = FastAPI(title="Smart Storage Manager API")


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items")
def list_items():
    query = (
        "SELECT c.id, c.sku, c.filename, c.size_bytes, c.status, c.created_at "
        "FROM c ORDER BY c.created_at DESC"
    )
    return list(items_container.query_items(query=query, enable_cross_partition_query=True))


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    item_id = str(uuid.uuid4())
    blob_name = f"{item_id}-{file.filename}"
    timestamp = now_iso()

    blob_container.upload_blob(
        name=blob_name,
        data=content,
        overwrite=True,
        content_settings=ContentSettings(content_type=file.content_type),
    )

    item = {
        "id": item_id,
        "sku": "UNCLASSIFIED",
        "filename": file.filename,
        "size_bytes": len(content),
        "blob_name": blob_name,
        "status": "uploaded",
        "created_at": timestamp,
    }
    items_container.create_item(item)

    transactions_container.create_item(
        {
            "id": str(uuid.uuid4()),
            "type": "upload",
            "item_id": item_id,
            "timestamp": timestamp,
        }
    )
    return item
