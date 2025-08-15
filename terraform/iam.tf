resource "aws_iam_role" "sagemaker_execution_role" {
  for_each = var.env

  name = "${each.key}-sagemaker-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "sagemaker.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "additional_access_policy" {
  for_each = var.env
  name     = "${each.key}-sagemaker-additional-access-policy"
  policy   = templatefile("policy-documents/sagemaker-notebooks-${each.key}.json", { account_id = data.aws_caller_identity.current.account_id })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  for_each   = var.env
  role       = aws_iam_role.sagemaker_execution_role[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "sagemaker_additional_access" {
  for_each   = var.env
  role       = aws_iam_role.sagemaker_execution_role[each.key].name
  policy_arn = aws_iam_policy.additional_access_policy[each.key].arn
}
