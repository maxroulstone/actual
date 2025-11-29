resource "google_compute_instance" "vm_instance" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["web-server", "ssh-server"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 10
    }
  }

  attached_disk {
    source      = var.data_disk_self_link
    device_name = "budget_data"
  }

  network_interface {
    network = var.network_name
    access_config {
      # Ephemeral public IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e

    # 1. Mount Persistent Disk
    MOUNT_DIR="/mnt/data"
    DEVICE_ID="google-budget_data"
    
    mkdir -p $MOUNT_DIR
    
    if ! blkid /dev/disk/by-id/$DEVICE_ID; then
      mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/disk/by-id/$DEVICE_ID
    fi
    
    mount -o discard,defaults /dev/disk/by-id/$DEVICE_ID $MOUNT_DIR
    
    # Add to fstab
    echo UUID=$(blkid -s UUID -o value /dev/disk/by-id/$DEVICE_ID) $MOUNT_DIR ext4 discard,defaults,nofail 0 2 | tee -a /etc/fstab

    # 2. Install Docker
    if ! command -v docker &> /dev/null; then
      apt-get update
      apt-get install -y ca-certificates curl gnupg
      install -m 0755 -d /etc/apt/keyrings
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
      chmod a+r /etc/apt/keyrings/docker.gpg

      echo \
        "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null
      
      apt-get update
      apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    fi

    # 3. Prepare Directory
    # We create a directory on the persistent disk for the repo
    mkdir -p $MOUNT_DIR/budget
    chown -R $USER:$USER $MOUNT_DIR/budget
  EOF
}
