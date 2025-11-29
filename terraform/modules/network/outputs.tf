output "network_name" {
  value = google_compute_network.vpc_network.name
}

output "network_self_link" {
  value = google_compute_network.vpc_network.self_link
}
