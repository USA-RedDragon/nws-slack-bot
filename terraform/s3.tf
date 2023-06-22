resource "aws_s3_bucket" "data" {
  bucket = "${local.name}-data"

  tags = {
    Name = "${local.name}-data"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.s3-encryption.arn
      sse_algorithm     = "aws:kms"
    }
  }
}
