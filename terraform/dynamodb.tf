resource "aws_dynamodb_table" "installations" {
  name                        = "${local.name}-installations"
  hash_key                    = "team_id"
  billing_mode                = "PAY_PER_REQUEST"
  deletion_protection_enabled = false

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.installations-encryption.arn
  }

  attribute {
    name = "team_id"
    type = "S"
  }

  attribute {
    name = "bot_started"
    type = "N"
  }

  attribute {
    name = "state"
    type = "S"
  }

  global_secondary_index {
    name            = "state-index"
    hash_key        = "state"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "bot_started-index"
    hash_key        = "bot_started"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "alerts" {
  name                        = "${local.name}-alerts"
  hash_key                    = "id"
  billing_mode                = "PAY_PER_REQUEST"
  deletion_protection_enabled = true

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "state"
    type = "S"
  }

  global_secondary_index {
    name            = "state-index"
    hash_key        = "state"
    projection_type = "ALL"
  }
}
