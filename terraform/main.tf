
###Provider###
provider "google" {
  project     = "ae-terraform-2025"
  region      = "europe-west4"
}

###storage bucket###
resource "google_storage_bucket" "nico-ae-bucket" {
  name          = var.bucket_name
  location      = var.location
  force_destroy = true

  public_access_prevention = "enforced"
}

###docker image###
data "google_artifact_registry_docker_image" "my_image" {
  location      = var.location
  repository_id = var.registry
  image_name    = "nico-roman-converter"
}

###db instance###
resource "google_sql_database_instance" "nico-db" {
    name             = "nico-db-instance"
    database_version = "POSTGRES_15"
    region           = var.location
    deletion_protection = false

    settings {
        tier = "db-custom-1-3840"
    }
}

###roman db###
resource "google_sql_database" "roman_database" {
    name     = "roman_db"
    instance = google_sql_database_instance.nico-db.name
}

###roman-api service image###
resource "google_cloud_run_v2_service" "roman-api" {
  name                = "roman-api"
  location            = var.location
  deletion_protection = false
  ingress            = "INGRESS_TRAFFIC_ALL"

  template {

    annotations = {
      "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.nico-db.connection_name
    }

    containers {
      image = "${var.location}-docker.pkg.dev/ae-terraform-2025/ae-2025-registry/nico-roman-converter:latest"

    env {
      name  = "INSTANCE_UNIX_SOCKET"
      value = "/cloudsql/${google_sql_database_instance.nico-db.connection_name}"
    }

    env {
      name  = "DB_USER"
      value = var.db_user
    }

    env {
      name  = "DB_PASSWORD"
      value = var.db_password
    }

    env {
      name  = "DB_NAME"
      value = google_sql_database.roman_database.name
    }

    env {
      name  = "BUCKET_URL"
      value = google_storage_bucket.nico-ae-bucket.url
    }

      
      env {
        name  = "BUCKET_URL"
        value = google_storage_bucket.nico-ae-bucket.url
      }
    }
  }
}
