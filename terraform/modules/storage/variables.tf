variable "disk_name" {
  description = "Name of the persistent disk"
  type        = string
  default     = "budget-data-disk"
}

variable "disk_size_gb" {
  description = "Size of the disk in GB"
  type        = number
  default     = 10
}

variable "zone" {
  description = "GCP Zone"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
}
