resource "azurerm_cognitive_account" "docint" {
  name                  = "docint-${var.project_name}-${local.suffix}"
  location              = azurerm_resource_group.rg.location
  resource_group_name   = azurerm_resource_group.rg.name
  kind                  = "FormRecognizer"
  sku_name              = "F0"
  custom_subdomain_name = "docint-${var.project_name}-${local.suffix}"
}

output "document_intelligence_endpoint" {
  value = azurerm_cognitive_account.docint.endpoint
}
