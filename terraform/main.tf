# --- Enable APIs ---
resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudresourcemanager" {
  service            = "cloudresourcemanager.googleapis.com"
  disable_on_destroy = false
}

module "network" {
  source = "./modules/network"
  depends_on = [
    google_project_service.compute,
    google_project_service.cloudresourcemanager
  ]
}

module "storage" {
  source       = "./modules/storage"
  region       = var.region
  zone         = var.zone
  disk_size_gb = var.disk_size_gb
  depends_on = [
    google_project_service.compute
  ]
}

module "compute" {
  source              = "./modules/compute"
  zone                = var.zone
  machine_type        = var.machine_type
  network_name        = module.network.network_name
  data_disk_self_link = module.storage.disk_self_link
  depends_on = [
    google_project_service.compute
  ]
}
