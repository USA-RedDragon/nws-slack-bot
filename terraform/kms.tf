resource "aws_kms_key" "log-encryption" {
  description             = "${local.name}-cloudwatch"
  deletion_window_in_days = 30
}

resource "aws_kms_key" "s3-encryption" {
  description             = "${local.name}-s3"
  deletion_window_in_days = 30
}

resource "aws_kms_key" "installations-encryption" {
  description             = "${local.name}-installations"
  deletion_window_in_days = 30
}

