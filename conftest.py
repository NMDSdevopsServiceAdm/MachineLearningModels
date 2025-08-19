import pytest
import os
from moto import mock_aws
import boto3


@pytest.fixture(scope="session")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_REGION"] = "eu-west-2"


@pytest.fixture
def mocked_aws(aws_credentials):
    """
    Mock all AWS interactions
    """
    with mock_aws():
        yield


@pytest.fixture
def s3_client(mocked_aws):
    """Mocked AWS S3 Client for moto."""
    yield boto3.client("s3")


@pytest.fixture
def model_bucket():
    return "my-model-bucket"


@pytest.fixture
def ssm_client(mocked_aws):
    """Mocked AWS SSM Client for moto."""
    yield boto3.client("ssm")


@pytest.fixture
def s3_bucket(s3_client, model_bucket):
    """Mocked S3 Bucket for moto."""
    s3_client.create_bucket(
        Bucket=model_bucket,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )


@pytest.fixture
def ssm_parameter(ssm_client):
    """Mocked SSM Parameter for moto."""
    ssm_client.put_parameter(
        Name="model/test/version", Value='{"Current Version": "5.6.7"}', Type="String"
    )


@pytest.fixture
def glue_client(mocked_aws):
    """Mocked AWS Glue Client for moto."""
    yield boto3.client("glue")


@pytest.fixture
def glue_db(glue_client):
    """Mocked Glue DB for moto."""
    glue_client.create_database(
        DatabaseInput={
            "Name": "test-db",
        }
    )


@pytest.fixture
def glue_table_simple(glue_client, glue_db):
    """Mocked Glue Table for simple types"""
    glue_client.create_table(
        DatabaseName="test-db",
        TableInput={
            "Name": "test-table-simple",
            "StorageDescriptor": {
                "Columns": [
                    {"Name": "user_id", "Type": "string"},
                    {"Name": "transaction_date", "Type": "date"},
                    {"Name": "amount", "Type": "double"},
                    {"Name": "is_fraud", "Type": "boolean"},
                ]
            },
        },
    )


@pytest.fixture
def glue_table_weird(glue_client, glue_db):
    """Mocked Glue Table for simple types"""
    glue_client.create_table(
        DatabaseName="test-db",
        TableInput={
            "Name": "test-table-weird",
            "StorageDescriptor": {
                "Columns": [
                    {"Name": "id", "Type": "int"},
                    {"Name": "location", "Type": "geometry"},  # Unsupported type
                ]
            },
        },
    )


@pytest.fixture
def glue_table_complex(glue_client, glue_db):
    """Mocked Glue Table for simple types"""
    glue_client.create_table(
        DatabaseName="test-db",
        TableInput={
            "Name": "test-table-complex",
            "StorageDescriptor": {
                "Columns": [
                    {"Name": "user_tags", "Type": "array<string>"},
                    {"Name": "user_profile", "Type": "struct<name:string,age:int>"},
                    {"Name": "metadata", "Type": "map<string,bigint>"},
                ]
            },
        },
    )


@pytest.fixture
def glue_table_very_complex(glue_client, glue_db):
    """Mocked Glue Table for simple types"""
    glue_client.create_table(
        DatabaseName="test-db",
        TableInput={
            "Name": "test-table-very-complex",
            "StorageDescriptor": {
                "Columns": [
                    {"Name": "user_tags", "Type": "array<string>"},
                    {"Name": "user_profile", "Type": "struct<name:string,age:int>"},
                    {"Name": "metadata", "Type": "map<string,bigint>"},
                    {
                        "Name": "crazy",
                        "Type": "array<struct<name:string,code:string,contacts:array<struct<personFamilyName:string,personGivenName:string,personRoles:array<string>,personTitle:string,jobs:array<string>>>,score:int>>",
                    },
                ]
            },
        },
    )
