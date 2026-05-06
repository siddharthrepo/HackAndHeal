terraform {
  backend "s3" {
    bucket         = "healthmeter-terraform-state"
    key            = "dev/infra.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
