from enum import Enum
import boto3
from botocore.exceptions import ClientError
from sklearn.base import BaseEstimator
import pickle
import io
import json


class ChangeType(Enum):
    MAJOR = 1
    MINOR = 2
    PATCH = 3


class ModelVersionManager:
    """
    Manages semantic versioning for machine learning models using AWS Systems Manager
    Parameter Store.

    Attributes:
        param_store_name (str): The name of the parameter in Parameter Store.
        s3_bucket (str): The S3 bucket where models are stored.
        s3_prefix (str): The base prefix for model files in S3.
        ssm_client: The Boto3 client for Systems Manager.
    """

    def __init__(self, s3_bucket, s3_prefix):
        """
        Initializes the ModelVersionManager.

        Args:
            s3_bucket (str): The S3 bucket where models are stored.
            s3_prefix (str): The base prefix for model files in S3.
        """
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.ssm_client = boto3.client("ssm")
        self.s3_client = boto3.client("s3")
        self.param_store_name = None

    def get_current_version(self):
        """
        Retrieves the current model version from Parameter Store.

        Returns:
            str: The current version string (e.g., "1.2.3").

        Raises:
            ClientError: If there is an error while connecting to the AWS API
        """
        try:
            response = self.ssm_client.get_parameter(
                Name=self.param_store_name, WithDecryption=False
            )
            raw_value = json.loads(response["Parameter"]["Value"])
            return raw_value["Current Version"]
        except ClientError as e:
            print(f"Boto3 Error while retrieving parameter: {e}")
            raise e

    def update_parameter_store(self, new_version: str) -> None:
        """
        Updates the version number in Parameter Store.

        Args:
            new_version (str): The new version string.
        """
        try:
            param_dict = {"Current Version": new_version}
            param_str = json.dumps(param_dict)
            self.ssm_client.put_parameter(
                Name=self.param_store_name,
                Value=param_str,
                Type="String",
                Overwrite=True,
            )
            print(
                f"Successfully updated Parameter Store with new version: {new_version}"
            )
        except Exception as e:
            print(f"Error updating Parameter Store: {e}")
            raise e

    def increment_version(self, current_version: str, change_type: ChangeType) -> str:
        """
        Increments the version number based on the change type.

        Args:
            current_version (str): The current version string.
            change_type (str): 'major', 'minor', or 'patch'.

        Returns:
            str: The new version string.

        Raises:
            ValueError: If the change type is invalid.
        """
        parts = [int(p) for p in current_version.split(".")]
        if change_type == ChangeType.MAJOR:
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif change_type == ChangeType.MINOR:
            parts[1] += 1
            parts[2] = 0
        elif change_type == ChangeType.PATCH:
            parts[2] += 1
        else:
            raise ValueError(
                "Invalid change type. Must be  '1'(major), 'minor', or 'patch'."
            )

        return ".".join(map(str, parts))

    def get_new_version(self, change_type: ChangeType) -> str:
        """
        Calculates and returns the new version number.

        Args:
            change_type (ChangeType): 'MAJOR', 'MINOR', or 'PATCH'.

        Returns:
            str: The new version string.
        """
        try:
            current_version = self.get_current_version()
            new_version = self.increment_version(current_version, change_type)
            return new_version
        except self.ssm_client.exceptions.ParameterNotFound:
            print(
                f"Parameter '{self.param_store_name}' not found. Initializing to 0.1.0."
            )
            return "0.1.0"
        except ValueError as e:
            print(f"Error getting new version: {e}")

    def save_model(self, model: BaseEstimator, new_version: str):
        """
        Saves the trained model to S3 with the version number in the path.

        Args:
            model(BaseEstimator): The trained model object to be saved.
            new_version (str): The new version string.
        """
        prefix = f"{self.s3_prefix}/{new_version}/model.pkl"
        buffer = io.BytesIO()
        pickle.dump(model, buffer)
        buffer.seek(0)

        self.s3_client.upload_fileobj(buffer, self.s3_bucket, prefix)

        print(f"Saving model to s3://{self.s3_bucket}/{prefix}")

    def prompt_change(self, prompt_num=0) -> ChangeType | None:
        selection = input(
            "Is this a \n1. Major?\n2. Minor?\n3. Patch change?\n(1/2/3): "
        ).lower()
        if selection not in ["1", "2", "3"] and prompt_num == 0:
            print("Invalid change type. Try again, choose 1, 2 or 3.")
            repeat_result = self.prompt_change(prompt_num=1)
            return repeat_result
        elif selection not in ["1", "2", "3"]:
            print("Invalid change type. Model not saved.")
            return None
        match selection:
            case "1":
                return ChangeType.MAJOR
            case "2":
                return ChangeType.MINOR
            case "3":
                return ChangeType.PATCH
            case _:
                return None

    def prompt_and_save(self, model: BaseEstimator) -> None:
        """
        Prompts the user for a change type and handles the versioning and saving process.

        Args:
            model: The trained model object.
        """
        should_save = input(
            "Do you want to save this new model version? (only yes to save): "
        ).lower()
        if should_save != "yes":
            print("Model not saved. Exiting.")
            return

        change_type = self.prompt_change()

        new_version = self.get_new_version(change_type)
        self.save_model(model, new_version)
        self.update_parameter_store(new_version)
