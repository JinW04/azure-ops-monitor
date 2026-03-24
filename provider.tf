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

# Output the Database ID
output "workspace_id" {
  value = azurerm_log_analytics_workspace.monitor_law.workspace_id
}

# Output the Database Password (SENSITIVE)
output "workspace_key" {
  value     = azurerm_log_analytics_workspace.monitor_law.primary_shared_key
  sensitive = true
}

# "Emergency Contact List" for alerts
resource "azurerm_monitor_action_group" "email_alert" {
  name                = "ag-earthquake-alerts"
  resource_group_name = azurerm_resource_group.monitor_rg.name
  short_name          = "QuakeAlert"

  email_receiver {
    name                    = "SendToAdminEmail"
    email_address           = "jinwongsurin@gmail.com" 
    use_common_alert_schema = true
  }

  sms_receiver {
    name         = "SendToAdminText"
    country_code = "47"            # 47 = Norge
    phone_number = "46310668"
  }
}

# "Trigger" that looks for earthquakes in database
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "quake_alert_rule" {
  name                = "High-Magnitude-Earthquake-Alert"
  resource_group_name = azurerm_resource_group.monitor_rg.name
  location            = azurerm_resource_group.monitor_rg.location
  scopes              = [azurerm_log_analytics_workspace.monitor_law.id]
  description         = "Fires when an earthquake > 7.0 is detected"
  severity            = 1
  evaluation_frequency= "PT5M" # Checks the database every 5 minutes
  window_duration     = "PT5M" # Looks at the last 5 minutes of data

  criteria {
    # KQL query asking the database for earthquakes >= 7.0
    query                   = <<-QUERY
      EarthquakeData_CL
      | where Magnitude_d >= 7.0
    QUERY
    time_aggregation_method = "Count"
    threshold               = 0
    operator                = "GreaterThan"
  }

  action {
    # Connects the Rule to the Action Group
    action_groups = [azurerm_monitor_action_group.email_alert.id]
  }
}