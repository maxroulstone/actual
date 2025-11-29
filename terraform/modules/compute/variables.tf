variable "instance_name" {
  description = "Name of the VM instance"
  type        = string
  default     = "budget-server"
}

variable "machine_type" {
  description = "Machine type for the VM"
  type        = string
  default     = "e2-micro"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
}

variable "network_name" {
  description = "Name of the network to attach to"
  type        = string
}

variable "data_disk_self_link" {
  description = "Self link of the persistent data disk"
  type        = string
}
