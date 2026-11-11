resource "azurerm_log_analytics_workspace" "law" {
  name                = "log-${var.project_name}-${local.suffix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}
resource "azurerm_container_registry" "acr" {
  name                = "acr${var.project_name}${local.suffix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = true
}
resource "azurerm_container_app_environment" "cae" {
  name                       = "cae-${var.project_name}-${local.suffix}"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id
}
output "acr_name" {
  value = azurerm_container_registry.acr.name
}
output "container_app_environment_name" {
  value = azurerm_container_app_environment.cae.name
}
