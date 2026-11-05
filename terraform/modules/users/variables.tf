variable "project_id" {
  description = "The GCP Project ID passed by the root module"
  type        = string
}

variable "iap_ssh_users" {
  description = "Email addresses of users allowed to open IAP tunnels."
  type        = set(string)
}
