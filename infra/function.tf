resource "azurerm_storage_account" "func_storage" {
  name                     = "stfunc${local.suffix}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
}

resource "azurerm_service_plan" "func_plan" {
  name                = "plan-${var.project_name}-${local.suffix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "func" {
  name                       = "func-${var.project_name}-${local.suffix}"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  service_plan_id            = azurerm_service_plan.func_plan.id
  storage_account_name       = azurerm_storage_account.func_storage.name
  storage_account_access_key = azurerm_storage_account.func_storage.primary_access_key
  https_only                 = true

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"  = "python"
    "STORAGE_CONNECTION_STRING" = azurerm_storage_account.storage.primary_connection_string
    "COSMOS_ENDPOINT"           = azurerm_cosmosdb_account.cosmos.endpoint
    "COSMOS_KEY"                = azurerm_cosmosdb_account.cosmos.primary_key
    "COSMOS_DB"                 = "smartstorage"
    "DOCINT_ENDPOINT"           = azurerm_cognitive_account.docint.endpoint
    "DOCINT_KEY"                = azurerm_cognitive_account.docint.primary_access_key
  }
}

output "function_app_name" {
  value = azurerm_linux_function_app.func.name
}
