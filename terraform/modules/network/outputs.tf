output "network_name" {
  value = google_compute_network.vpc_network.name
}

output "network_self_link" {
  value = google_compute_network.vpc_network.self_link
}

output "static_ip_address" {
  value       = google_compute_address.vm_static_ip.address
  description = "The static public IP address"
}

output "static_ip_self_link" {
  value       = google_compute_address.vm_static_ip.self_link
  description = "Self link of the static IP address resource"
}
