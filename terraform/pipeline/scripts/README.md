
## Terraform Scripts

Scripts reference for Terraform deployment

### SageMaker

SageMaker use [Lifecycle Configuration scripts](https://docs.aws.amazon.com/sagemaker/latest/dg/notebook-lifecycle-config.html) to manage the state of Notebook instances and persist changes. These can be deployed via a CI/CD using Terraform.

AWS will automatically look for and run two scripts:
- `on-create`: run once when deploying an instance
- `on-start`: run each time the instance is restarted

In Terraform, script files can be referenced as templates (base64 encoded) and attached to the [aws_sagemaker_notebook_instance](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_notebook_instance).


```tf
resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "models_lifecycle" {
  name      = "sfc-mlops-lifecycle"
  on_create = filebase64("scripts/notebooks-on-create.sh")
  on_start  = filebase64("scripts/notebooks-on-start.sh")
}
```

See [snippets](https://github.com/aws-samples/amazon-sagemaker-notebook-instance-lifecycle-config-samples/tree/master/scripts) for script examples and [Customizing SageMaker Notebook Instances
](https://medium.com/datamindedbe/customizing-sagemaker-notebook-instances-29f919421e24) for futher reading.