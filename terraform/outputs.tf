output "public_ip" {
  value       = module.compute.public_ip
  description = "The public IP address of the server"
}

output "ssh_command" {
  value = "gcloud compute ssh ${module.compute.instance_name} --zone ${var.zone}"
}
