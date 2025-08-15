import pytest
import polars as pl
from utilities.schema_reader import GlueSchemaReader


@pytest.fixture
def glue_schema_reader(glue_client):
    """A pytest fixture to provide a GlueSchemaReader instance."""
    return GlueSchemaReader()


def test_get_polars_schema_correct_for_simple_types(glue_client, glue_db, glue_table_simple, glue_schema_reader):
    """Tests successful retrieval and conversion of a Glue schema with simple types."""

    # Call the method under test
    polars_schema = glue_schema_reader.get_polars_schema('test-db', 'test-table-simple')

    # Define the expected Polars schema
    expected_schema = {
        'user_id': pl.Utf8,
        'transaction_date': pl.Date,
        'amount': pl.Float64,
        'is_fraud': pl.Boolean,
    }

    # Assert that the schemas match
    assert polars_schema == expected_schema

# def test_get_polars_schema_correct_for_complex_types(glue_client, glue_db, glue_table_simple, glue_schema_reader):
#     pass


def test_unsupported_data_type(glue_client, glue_schema_reader, glue_db, glue_table_weird):
    """Tests that the function raises an error for an unsupported Glue data type."""

    with pytest.raises(ValueError, match="Unsupported Glue data type: 'geometry'"):
        glue_schema_reader.get_polars_schema('test-db', 'test-table-weird')


def test_table_not_found(glue_client, glue_schema_reader):
    """Tests that the function handles a 'table not found' error from Glue."""

    with pytest.raises(ValueError, match="Glue table 'my_database.my_table' not found."):
        glue_schema_reader.get_polars_schema('my_database', 'my_table')

@pytest.mark.skip
def test_complex_type_handling(glue_client, glue_schema_reader):
    """Tests that complex types are handled correctly (e.g., array<string>)."""
    glue_client.get_table.return_value = {
        'Table': {
            'StorageDescriptor': {
                'Columns': [
                    {'Name': 'user_tags', 'Type': 'array<string>'},
                    {'Name': 'last_login', 'Type': 'timestamp'}
                ]
            }
        }
    }
    polars_schema = glue_schema_reader.get_polars_schema('my_database', 'my_table')
    assert polars_schema['user_tags'] == pl.Utf8  # The code simplifies to the base type
    assert polars_schema['last_login'] == pl.Datetime