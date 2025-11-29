output "disk_self_link" {
  value = google_compute_disk.data_disk.self_link
}

output "disk_name" {
  value = google_compute_disk.data_disk.name
}
