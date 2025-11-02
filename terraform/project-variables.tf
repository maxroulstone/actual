variable "gcp_project_name" {
  type        = string
  description = "Name of GCP project."
}

variable "gcp_billing_project_name" {
  type        = string
  description = "Name of GCP Billing Project."
}

variable "gcp_region" {
  type        = string
  description = "GCP region to operate in."
}

variable "gcp_zone" {
  type        = string
  description = "GCP Regional Zone to use."
}

variable "project_enabled_services" {
  type        = list(string)
  description = "List of services to enable."
}