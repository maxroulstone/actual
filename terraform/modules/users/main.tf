resource "google_project_iam_member" "iap_ssh" {
  for_each = var.iap_ssh_users

  project = var.project_id
  role    = "roles/iap.tunnelResourceAccessor"
  member  = "user:${each.value}"
}
