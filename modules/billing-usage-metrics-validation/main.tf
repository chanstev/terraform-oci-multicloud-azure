terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
    }
  }
}
data "azurerm_subscription" "current" {
}

data "azurerm_resources" "resource" {
  resource_group_name = var.azure_resource_group_name
  name                = var.azure_resource_name
}

resource "null_resource" "resource-json" {

  provisioner "local-exec" {
    environment = {
      "PYTHONPATH" : "${path.module}/../../../"
      "OCI_CLI_AUTH" : "security_token"
    }
    working_dir = "${path.module}/scripts"
    command     = <<EOT
      python -m venv venv
      source venv/bin/activate
      pip3 install -r requirements.txt
      export AZ_AUTH_TOKEN=$(az account get-access-token --output json --query 'accessToken')
      python3 billing_usage_metrics_validation.py -p '${var.config_file_profile}' -s '${data.azurerm_subscription.current.subscription_id}' -g '${var.azure_resource_group_name}' -n '${var.azure_resource_name}' -t '${var.oci_compartment_ocid}'
EOT
  }
}
