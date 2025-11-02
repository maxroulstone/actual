resource "google_compute_firewall" "allow_https" {
  name        = "allow-https"
  description = "Allows HTTPS traffic."
  network     = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
  direction   = "INGRESS"
  target_tags = ["https-server"]

  source_ranges = ["0.0.0.0/0"]
  priority      = "1000"
}

resource "google_compute_firewall" "allow_http" {
  name        = "allow-http"
  description = "Allows HTTP traffic."
  network     = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
  direction   = "INGRESS"
  target_tags = ["http-server"]

  source_ranges = ["0.0.0.0/0"]
  priority      = "1000"
}

resource "google_compute_firewall" "allow_ssh_proxy" {
  name        = "allow-ssh-proxy"
  description = "Allows SSH from Google's Identity Aware Proxy (IAP)"
  network     = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  direction   = "INGRESS"
  target_tags = ["allow-ssh-proxy"]

  source_ranges = ["35.235.240.0/20"]
  priority      = "1000"
}

resource "google_compute_firewall" "allow_ssh" {
  name        = "allow-ssh"
  description = "Allows SSH from anywhere. Recommended to use only when absolutely necessary."
  network     = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  direction   = "INGRESS"
  target_tags = ["allow-ssh"]

  source_ranges = ["0.0.0.0/0"]
  priority      = "1000"
}