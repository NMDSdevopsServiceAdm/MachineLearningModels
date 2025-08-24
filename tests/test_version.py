import pytest
from unittest.mock import Mock, patch
from utilities.version import ModelVersionManager, EnumChangeType, BaseEstimator
import pickle
import io


PATCH_STEM = "utilities.version.ModelVersionManager"


class DummyModel(BaseEstimator):
    def __init__(self, name: str, param1: int, param2: int):
        self.name = name
        self.param1 = param1
        self.param2 = param2

    def fit(self, *args, **kwargs):
        pass


@pytest.fixture
def version_manager(mocked_aws, s3_client, s3_bucket, ssm_client, model_bucket):
    """A pytest fixture to provide a ModelVersionManager instance."""
    return ModelVersionManager(
        s3_bucket=model_bucket,
        s3_prefix="model/test/version",
        param_store_name="model/test/version",
    )


@pytest.fixture
def fitted_model():
    """A dummy model instance with parameters set."""
    return DummyModel(name="clever_model", param1=17, param2=26)


def test_increment_major(mocked_aws, version_manager):
    assert version_manager.increment_version("1.2.3", EnumChangeType.MAJOR) == "2.0.0"


def test_increment_minor(mocked_aws, version_manager):
    assert version_manager.increment_version("1.2.3", EnumChangeType.MINOR) == "1.3.0"


def test_increment_patch(mocked_aws, version_manager):
    assert version_manager.increment_version("1.2.3", EnumChangeType.PATCH) == "1.2.4"


def test_invalid_change_type(mocked_aws, version_manager):
    with pytest.raises(ValueError):
        version_manager.increment_version("1.0.0", 4)


def test_get_current_version_gets_data_from_ssm(
    mocked_aws, version_manager, ssm_client, ssm_parameter
):
    assert version_manager.get_current_version() == "5.6.7"


def test_get_current_version_raises_error_if_no_parameter(
    mocked_aws, version_manager, ssm_client
):
    version_manager.param_store_name = "model/new/version"
    with pytest.raises(version_manager.ssm_client.exceptions.ParameterNotFound):
        version_manager.get_current_version()


@patch(f"{PATCH_STEM}.get_current_version", return_value="1.2.3")
def test_get_new_version_given_existing(mock_get_current, mocked_aws, version_manager):
    new_version = version_manager.get_new_version(EnumChangeType.MINOR)
    assert new_version == "1.3.0"
    mock_get_current.assert_called_once()


@patch(f"{PATCH_STEM}.get_current_version")
def test_get_new_version_given_no_existing(
    mock_get_current, mocked_aws, version_manager
):
    version_manager.param_store_name = "model/new/version"

    def raise_error():
        raise version_manager.ssm_client.exceptions.ParameterNotFound({}, "test")

    mock_get_current.side_effect = raise_error
    new_version = version_manager.get_new_version(EnumChangeType.MINOR)
    assert new_version == "0.1.0"
    mock_get_current.assert_called_once()


@patch("builtins.input", side_effect=["4", "5"])
def test_prompt_change_when_incorrect_inputs(mock_input, mocked_aws, version_manager):
    with pytest.raises(ValueError):
        result = version_manager.prompt_change()
    assert mock_input.call_count == 2


@patch("builtins.input", side_effect=["4", "3"])
def test_prompt_change_when_single_incorrect_input(
    mock_input, mocked_aws, version_manager
):
    result = version_manager.prompt_change()
    assert result == EnumChangeType.PATCH
    assert mock_input.call_count == 2


def test_save_model_writes_to_s3(
    mocked_aws, version_manager, s3_client, s3_bucket, fitted_model, model_bucket
):
    version_manager.save_model(fitted_model, "1.2.3")
    response1 = version_manager.s3_client.list_objects_v2(Bucket=model_bucket)
    assert response1["KeyCount"] == 1
    assert response1["Contents"][0]["Key"] == "model/test/version/1.2.3/model.pkl"
    download = io.BytesIO()
    version_manager.s3_client.download_fileobj(
        model_bucket, "model/test/version/1.2.3/model.pkl", download
    )
    download.seek(0)
    loaded_model = pickle.load(download)
    assert loaded_model.name == "clever_model"
    assert loaded_model.param1 == 17
    assert loaded_model.param2 == 26


def test_update_parameter_store(mocked_aws, version_manager, ssm_client, ssm_parameter):
    version_manager.update_parameter_store("7.8.9")
    assert version_manager.get_current_version() == "7.8.9"


@patch("builtins.input", side_effect=["yes", "2"])
@patch(f"{PATCH_STEM}.get_new_version", return_value="1.3.0")
@patch(f"{PATCH_STEM}.save_model")
@patch(f"{PATCH_STEM}.update_parameter_store")
def test_prompt_and_save_success(
    mock_update, mock_save, mock_get_new, mock_input, mocked_aws, version_manager
):
    mock_model = Mock()
    version_manager.prompt_and_save(mock_model)
    mock_get_new.assert_called_with(EnumChangeType.MINOR)
    mock_save.assert_called_with(mock_model, "1.3.0")
    mock_update.assert_called_with("1.3.0")


@patch("builtins.input", side_effect=["no"])
@patch(f"{PATCH_STEM}.get_new_version")
def test_prompt_and_save_no_save(mock_get_new, mock_input, mocked_aws, version_manager):
    mock_model = Mock()
    version_manager.prompt_and_save(mock_model)
    mock_get_new.assert_not_called()


@patch("builtins.input", side_effect=["yes", "2"])
def test_puts_new_version_if_none_available(
    mock_input, fitted_model, s3_bucket, s3_client, ssm_client, version_manager
):
    response1 = version_manager.ssm_client.describe_parameters()
    names1 = [p["Name"] for p in response1["Parameters"]]
    assert len(names1) == 0
    version_manager.prompt_and_save(fitted_model)
    assert version_manager.get_current_version() == "0.1.0"
    response2 = version_manager.ssm_client.describe_parameters()
    names2 = [p["Name"] for p in response2["Parameters"]]
    assert "model/test/version" in names2
    assert len(names2) == 1
