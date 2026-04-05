output "instance_name" {
  value = google_compute_instance.vm_instance.name
}

output "public_ip" {
  value       = var.static_ip_address
  description = "The static public IP address of the server"
}
