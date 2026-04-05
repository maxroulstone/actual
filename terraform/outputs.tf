output "public_ip" {
  value       = module.compute.public_ip
  description = "The static public IP address of the server"
}

output "static_ip_address" {
  value       = module.network.static_ip_address
  description = "The static IP address for stable DNS and cost optimization"
}

output "ssh_command" {
  value       = "gcloud compute ssh ${module.compute.instance_name} --zone ${var.zone}"
  description = "Command to SSH into the instance"
}

output "domain_ip" {
  value       = "Point budget.maxroulstone.com DNS A record to: ${module.network.static_ip_address}"
  description = "DNS configuration for the domain"
}
