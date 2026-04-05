variable "instance_name" {
  description = "Name of the VM instance"
  type        = string
  default     = "budget-server"
}

variable "machine_type" {
  description = "Machine type for the VM"
  type        = string
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

variable "static_ip_address" {
  description = "The static IP address to assign to the VM"
  type        = string
}
