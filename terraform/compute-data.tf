data "google_compute_image" "container_optimized" {
  family  = var.vm_image_family
  project = var.vm_image_project
}