terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "monitor_rg" {
  name     = "rg-earthquake-monitor"
  location = "East US"
}

# Creates the database to store our earthquake logs
resource "azurerm_log_analytics_workspace" "monitor_law" {
  name                = "law-earthquake-monitor"
  location            = azurerm_resource_group.monitor_rg.location
  resource_group_name = azurerm_resource_group.monitor_rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# 1. Creates a "Robot Account" (Managed Identity) for future Python scripts
resource "azurerm_user_assigned_identity" "monitor_identity" {
  location            = azurerm_resource_group.monitor_rg.location
  name                = "mi-earthquake-monitor"
  resource_group_name = azurerm_resource_group.monitor_rg.name
}

# 2. Give the Robot Account ONLY permission to work with the Log Analytics database
resource "azurerm_role_assignment" "monitor_role" {
  scope                = azurerm_log_analytics_workspace.monitor_law.id
  role_definition_name = "Log Analytics Contributor" 
  principal_id         = azurerm_user_assigned_identity.monitor_identity.principal_id
}