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