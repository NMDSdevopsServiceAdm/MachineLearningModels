import os

import pytest
from unittest.mock import Mock, patch
from utilities.version import ModelVersionManager, ChangeType, BaseEstimator
from moto import mock_aws
import boto3
import pickle
import io


PATCH_STEM = 'utilities.version.ModelVersionManager'
BUCKET = 'my-model-bucket'

class DummyModel(BaseEstimator):
    def __init__(self, version: str, param1: int, param2: int):
        self.version = version
        self.param1 = param1
        self.param2 = param2

    def fit(self, *args, **kwargs):
        pass

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture
def mocked_aws(aws_credentials):
    """
    Mock all AWS interactions
    """
    with mock_aws():
        yield

@pytest.fixture()
def s3_client(mocked_aws):
    """Mocked AWS S3 Client for moto."""
    with mock_aws():
        yield boto3.client('s3')


@pytest.fixture
def ssm_client(mocked_aws):
    """Mocked AWS SSM Client for moto."""
    with mock_aws():
        yield boto3.client('ssm')


@pytest.fixture
def s3_bucket(s3_client):
    """Mocked S3 Bucket for moto."""
    s3_client.create_bucket(Bucket=BUCKET, CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})


@pytest.fixture
def ssm_parameter(ssm_client):
    """Mocked SSM Parameter for moto."""
    ssm_client.put_parameter(Name='model/test/version', Value = '{"Current Version": "5.6.7"}', Type='String')


@pytest.fixture
def version_manager(s3_client, s3_bucket, ssm_client, ssm_parameter):
    """A pytest fixture to provide a ModelVersionManager instance."""
    return ModelVersionManager(
        s3_bucket=BUCKET,
        s3_prefix='model/test/version'
    )

@pytest.fixture
def fitted_model():
    """ A dummy model instance with parameters set."""
    return DummyModel(version='1.2.3', param1=17, param2=26)

def test_increment_major(version_manager):
    assert version_manager.increment_version("1.2.3", ChangeType.MAJOR) == "2.0.0"

def test_increment_minor(version_manager):
    assert version_manager.increment_version("1.2.3", ChangeType.MINOR) == "1.3.0"

def test_increment_patch(version_manager):
    assert version_manager.increment_version("1.2.3", ChangeType.PATCH) == "1.2.4"

def test_invalid_change_type(version_manager):
    with pytest.raises(ValueError):
        version_manager.increment_version("1.0.0", 4)


def test_get_current_version_gets_data_from_ssm(version_manager, ssm_client):
    version_manager.param_store_name = 'model/test/version'
    assert version_manager.get_current_version() == "5.6.7"

def test_get_current_version_raises_error_if_no_parameter(version_manager, ssm_client):
    version_manager.param_store_name = 'model/new/version'
    with pytest.raises(version_manager.ssm_client.exceptions.ParameterNotFound):
        version_manager.get_current_version()


@patch(f'{PATCH_STEM}.get_current_version', return_value="1.2.3")
def test_get_new_version_given_existing(mock_get_current, version_manager):
    new_version = version_manager.get_new_version(ChangeType.MINOR)
    assert new_version == "1.3.0"
    mock_get_current.assert_called_once()

@patch(f'{PATCH_STEM}.get_current_version')
def test_get_new_version_given_no_existing(mock_get_current, version_manager):
    version_manager.param_store_name = 'model/new/version'

    def raise_error():
        raise version_manager.ssm_client.exceptions.ParameterNotFound({}, 'test')

    mock_get_current.side_effect = raise_error
    new_version = version_manager.get_new_version(ChangeType.MINOR)
    assert new_version == "0.1.0"
    mock_get_current.assert_called_once()

@patch('builtins.input', side_effect=['4', '5'])
def test_prompt_change_when_incorrect_inputs(mock_input, version_manager):
    result = version_manager.prompt_change()
    assert result is None
    assert mock_input.call_count == 2

@patch('builtins.input', side_effect=['4', '3'])
def test_prompt_change_when_single_incorrect_input(mock_input, version_manager):
    result = version_manager.prompt_change()
    assert result == ChangeType.PATCH
    assert mock_input.call_count == 2

def test_save_model_writes_to_s3(version_manager, s3_client, s3_bucket, fitted_model):
    version_manager.save_model(fitted_model, '1.2.3')
    response1 = version_manager.s3_client.list_objects_v2(Bucket=BUCKET)
    assert response1['KeyCount'] == 1
    assert response1['Contents'][0]['Key'] == 'model/test/version/1.2.3/model.pkl'
    download = io.BytesIO()
    version_manager.s3_client.download_fileobj(BUCKET, 'model/test/version/1.2.3/model.pkl', download)
    download.seek(0)
    loaded_model = pickle.load(download)
    assert loaded_model.version == '1.2.3'
    assert loaded_model.param1 == 17
    assert loaded_model.param2 == 26

def test_update_parameter_store(version_manager, ssm_client, ssm_parameter):
    version_manager.param_store_name = 'model/test/version'
    version_manager.update_parameter_store('7.8.9')
    assert version_manager.get_current_version() == "7.8.9"

@patch('builtins.input', side_effect=['yes', '2'])
@patch(f'{PATCH_STEM}.get_new_version', return_value='1.3.0')
@patch(f'{PATCH_STEM}.save_model')
@patch(f'{PATCH_STEM}.update_parameter_store')
def test_prompt_and_save_success(mock_update, mock_save, mock_get_new, mock_input, version_manager):
    mock_model = Mock()
    version_manager.prompt_and_save(mock_model)
    mock_get_new.assert_called_with(ChangeType.MINOR)
    mock_save.assert_called_with(mock_model, '1.3.0')
    mock_update.assert_called_with('1.3.0')

@patch('builtins.input', side_effect=['no'])
@patch(f'{PATCH_STEM}.get_new_version')
def test_prompt_and_save_no_save(mock_get_new, mock_input, version_manager):
    mock_model = Mock()
    version_manager.prompt_and_save(mock_model)
    mock_get_new.assert_not_called()