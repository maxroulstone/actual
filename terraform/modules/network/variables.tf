variable "network_name" {
  description = "The name of the VPC network"
  type        = string
  default     = "budget-network"
}

variable "region" {
  description = "GCP Region"
  type        = string
}

variable "allowed_ssh_ip" {
  description = "CIDR block allowed for SSH access (e.g. '203.0.113.0/32' for a single IP)"
  type        = string
}
