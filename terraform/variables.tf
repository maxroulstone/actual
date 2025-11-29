variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-east1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-east1-b"
}

variable "machine_type" {
  description = "VM Machine Type"
  type        = string
  default     = "e2-micro" # Free tier eligible
}

variable "disk_size_gb" {
  description = "Size of the persistent data disk in GB"
  type        = number
  default     = 20
}
