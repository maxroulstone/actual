provider "google" {
  project               = var.gcp_project_name
  region                = var.gcp_region
  zone                  = var.gcp_zone
  user_project_override = true
  billing_project       = var.gcp_billing_project_name
}