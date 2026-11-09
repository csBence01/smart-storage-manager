import datetime
import logging
import os

import azure.functions as func
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient

app = func.FunctionApp()


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_containers():
    client = CosmosClient(os.environ["COSMOS_ENDPOINT"], credential=os.environ["COSMOS_KEY"])
    database = client.get_database_client(os.getenv("COSMOS_DB", "smartstorage"))
    return database.get_container_client("items"), database.get_container_client("transactions")


def analyze(content: bytes) -> dict:
    client = DocumentIntelligenceClient(
        os.environ["DOCINT_ENDPOINT"], AzureKeyCredential(os.environ["DOCINT_KEY"])
    )

    # 1. Try the invoice model (extracts the invoice number)
    try:
        result = client.begin_analyze_document(
            "prebuilt-invoice", AnalyzeDocumentRequest(bytes_source=content)
        ).result()
        if result.documents:
            invoice_id = result.documents[0].fields.get("InvoiceId")
            if invoice_id and invoice_id.content:
                return {"sku": invoice_id.content, "text": result.content or ""}
    except Exception as error:
        logging.warning("Invoice model failed, falling back to read: %s", error)

    # 2. Fallback: plain text read
    result = client.begin_analyze_document(
        "prebuilt-read", AnalyzeDocumentRequest(bytes_source=content)
    ).result()
    return {"sku": "UNCLASSIFIED", "text": result.content or ""}


@app.blob_trigger(arg_name="blob", path="raw-uploads/{name}", connection="STORAGE_CONNECTION_STRING")
def process_upload(blob: func.InputStream):
    name = blob.name.split("/", 1)[-1]
    item_id = name[:36]
    logging.info("Processing blob %s (item %s)", name, item_id)

    items, transactions = get_containers()
    found = list(
        items.query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": item_id}],
            enable_cross_partition_query=True,
        )
    )
    if not found:
        logging.error("No item found for %s", item_id)
        return
    doc = found[0]

    try:
        result = analyze(blob.read())
        updates = {"sku": result["sku"], "status": "processed", "extracted_text": result["text"][:2000]}
    except Exception as error:
        logging.exception("Analysis failed for %s", item_id)
        updates = {"status": "failed", "error": str(error)[:500]}

    # Cosmos DB cannot change a partition key in place: delete and recreate.
    clean = {key: value for key, value in doc.items() if not key.startswith("_")}
    new_doc = {**clean, **updates, "processed_at": now_iso()}
    items.delete_item(item=doc["id"], partition_key=doc["sku"])
    items.create_item(new_doc)

    transactions.create_item(
        {
            "id": str(__import__("uuid").uuid4()),
            "type": "process",
            "item_id": item_id,
            "status": updates["status"],
            "timestamp": now_iso(),
        }
    )
    logging.info("Finished %s with status %s", item_id, updates["status"])
