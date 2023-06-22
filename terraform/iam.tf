data "aws_iam_policy_document" "ecs-agent" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "allow-dynamodb" {
  statement {
    actions = [
      "dynamodb:BatchGetItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchWriteItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
    ]

    effect = "Allow"

    resources = [
      aws_dynamodb_table.alerts.arn,
      "${aws_dynamodb_table.alerts.arn}/index/*",
      aws_dynamodb_table.installations.arn,
      "${aws_dynamodb_table.installations.arn}/index/*",
    ]
  }
}

data "aws_iam_policy_document" "allow-s3" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]

    effect = "Allow"

    resources = [
      aws_s3_bucket.data.arn,
      "${aws_s3_bucket.data.arn}/*",
    ]
  }
}


data "aws_iam_policy_document" "allow-kms" {
  statement {
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey",
    ]

    effect = "Allow"

    resources = [
      aws_kms_key.installations-encryption.arn,
      aws_kms_key.s3-encryption.arn,
    ]
  }
}

resource "aws_iam_role" "ecs-agent" {
  name               = "${local.name}-ecs-agent"
  assume_role_policy = data.aws_iam_policy_document.ecs-agent.json
}

resource "aws_iam_policy" "dynamodb" {
  name        = "${local.name}-dynamodb"
  path        = "/"
  description = "Allow access to DynamoDB tables"
  policy      = data.aws_iam_policy_document.allow-dynamodb.json
}

resource "aws_iam_policy" "kms" {
  name        = "${local.name}-kms"
  path        = "/"
  description = "Allow access to KMS keys"
  policy      = data.aws_iam_policy_document.allow-kms.json
}

resource "aws_iam_policy" "s3" {
  name        = "${local.name}-s3"
  path        = "/"
  description = "Allow access to S3 buckets"
  policy      = data.aws_iam_policy_document.allow-s3.json
}

resource "aws_iam_role_policy_attachment" "dynamodb" {
  role       = aws_iam_role.ecs-agent.name
  policy_arn = aws_iam_policy.dynamodb.arn
}

resource "aws_iam_role_policy_attachment" "s3" {
  role       = aws_iam_role.ecs-agent.name
  policy_arn = aws_iam_policy.s3.arn
}

resource "aws_iam_role_policy_attachment" "kms" {
  role       = aws_iam_role.ecs-agent.name
  policy_arn = aws_iam_policy.kms.arn
}

resource "aws_iam_role_policy_attachment" "ecs-agent" {
  role       = aws_iam_role.ecs-agent.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ecs-agent.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ecs-agent" {
  name = "${local.name}-ecs-agent"
  role = aws_iam_role.ecs-agent.name
}
