resource "google_compute_disk" "data_disk" {
  name = var.disk_name
  type = "pd-standard"
  size = var.disk_size_gb
  zone = var.zone
}

resource "google_compute_resource_policy" "daily_snapshot" {
  name   = "daily-snapshot-policy"
  region = var.region
  snapshot_schedule_policy {
    schedule {
      daily_schedule {
        days_in_cycle = 1
        start_time    = "04:00"
      }
    }
    retention_policy {
      max_retention_days    = 7
      on_source_disk_delete = "KEEP_AUTO_SNAPSHOTS"
    }
  }
}

resource "google_compute_disk_resource_policy_attachment" "attachment" {
  name = google_compute_resource_policy.daily_snapshot.name
  disk = google_compute_disk.data_disk.name
  zone = var.zone
}
