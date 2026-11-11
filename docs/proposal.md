# Smart Storage Manager - Project Proposal

## 1. Problem

Small businesses and teams receive many invoices, delivery notes and product photos. Finding the relevant information later means opening each file by hand. The goal is a simple inventory app where uploaded documents are stored, processed automatically and listed in one place.

## 2. Goals

- Upload images, invoices and delivery notes through a web UI.
- Extract text from documents automatically with a managed AI service.
- Store raw files and structured results in cloud services.
- Run the app locally with Docker Compose and in Azure Container Apps.
- Provision all Azure resources with Terraform.
- Provide basic monitoring with Log Analytics and Application Insights.

## 3. Solution overview

The user uploads a file in the Streamlit frontend. The FastAPI backend stores the file in Azure Blob Storage and creates an inventory item in Cosmos DB with status `uploaded`. A blob-triggered Azure Function reads the new file, sends it to Azure AI Document Intelligence and updates the item with the result (`processed`) or an error (`failed`).

## 4. Architecture

- **Frontend:** Streamlit, Azure Container Apps.
- **Backend:** FastAPI, Azure Container Apps (autoscaling on HTTP concurrency, 1 to 5 replicas).
- **Raw file storage:** Azure Blob Storage, container `raw-uploads`.
- **Event processing:** Azure Functions (Python 3.11, Consumption plan), blob trigger.
- **AI extraction:** Azure AI Document Intelligence (F0 tier), model `prebuilt-invoice` with fallback to `prebuilt-read`.
- **Database:** Azure Cosmos DB (free tier), containers `items` (partition key `/sku`) and `transactions` (partition key `/id`).
- **Container registry:** Azure Container Registry (Basic).
- **Monitoring:** Log Analytics workspace, Application Insights (workspace-based).
- **Infrastructure as code:** Terraform (azurerm provider).

## 5. Key design decisions

| Decision | Reason |
|---|---|
| Blob trigger (polling) instead of Event Grid | Simpler setup, fewer moving parts for a student project. |
| `prebuilt-invoice` first, `prebuilt-read` as fallback | Invoices yield structured fields (InvoiceId as SKU); other files still get their text. |
| Cosmos partition key `/sku` | Natural key for inventory items. |
| Region `swedencentral` | `westeurope` and `northeurope` were blocked by the subscription policy for the required services. |
| Local image builds and push to ACR | ACR Tasks are not allowed in the student subscription. |
| Container Apps instead of AKS | Managed scaling and ingress without cluster administration. |

## 6. Implementation status

- Local app with Docker Compose: done.
- Azure infrastructure with Terraform: done (resource group, storage, Cosmos DB, Document Intelligence, Function App, ACR, Log Analytics, Container Apps environment).
- Event pipeline (blob trigger to Cosmos DB): done and verified in the cloud.
- Container Apps for backend and frontend: running.
- Monitoring: Log Analytics and Application Insights connected; KQL queries verified.
- Load test: done (see README).

## 7. Evaluation

- A single request to `GET /items` takes about 0.17 s without load.
- Under 50 parallel clients the throughput stays at about 18 to 20 requests per second, with a small number of 502 responses at higher replica counts.
- Autoscaling works: the backend scaled from 1 to 3 replicas during the test.
- Cosmos DB reported no 429 (throttling) responses.
- The main bottleneck is the cross-partition query that reads the whole `items` container.

## 8. Limitations and future work

- Pagination or a narrower query for `/items`.
- Authentication for the web app (currently open).
- CI/CD pipeline (GitHub Actions) for build and deploy.
- Retry and dead-letter handling for failed Document Intelligence calls.
- Better field mapping from invoice results to inventory attributes.

## 9. Cost

The solution uses free or low-cost tiers (Cosmos DB free tier, Document Intelligence F0, Container Apps and Functions on consumption pricing). Resources are removed with `terraform destroy` after the evaluation.
