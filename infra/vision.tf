resource "azurerm_cognitive_account" "vision" {
  name                  = "vision-${var.project_name}-${local.suffix}"
  location              = azurerm_resource_group.rg.location
  resource_group_name   = azurerm_resource_group.rg.name
  kind                  = "ComputerVision"
  sku_name              = "F0"
  custom_subdomain_name = "vision-${var.project_name}-${local.suffix}"
}

output "vision_endpoint" {
  value = azurerm_cognitive_account.vision.endpoint
}
