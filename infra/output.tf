output "ec2_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.app.public_ip
}

output "backup_bucket_name" {
  description = "S3 bucket for DB + media backups"
  value       = aws_s3_bucket.backups.bucket
}
