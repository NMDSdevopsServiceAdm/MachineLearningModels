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


def test_split_by_top_level_comma_splits_simple_and_complex(glue_schema_reader):
    """Tests that split function works for both simple and complex types."""
    type1 = 'a:int,b:string,c:float'
    type2 = 'a:int,b:array<struct<x:int,y:string>>,c:float'
    assert glue_schema_reader.split_by_top_level_comma(type1) == ['a:int', 'b:string', 'c:float']
    assert glue_schema_reader.split_by_top_level_comma(type2) == ['a:int', 'b:array<struct<x:int,y:string>>','c:float']

def test_parse_type_string_handles_simple_types(glue_schema_reader):
    """Tests that the function handles simple types correctly."""
    type_str = 'string'
    assert glue_schema_reader.parse_type_string(type_str) == (type_str, '')

def test_parse_type_string_handles_complex_types(glue_schema_reader):
    """Tests that the function handles simple types correctly."""
    type_str = 'array<string>'
    assert glue_schema_reader.parse_type_string(type_str) == ('array', 'string')

def test_parse_type_string_handles_very_complex_types(glue_schema_reader):
    """Tests that the function handles very complex types correctly."""
    type_str = 'struct<name:string,code:string,contacts:array<struct<personFamilyName:string,personGivenName:string,personRoles:array<string>,personTitle:string,col3:array<string>>>,score:int'
    expected_base = 'struct'
    expected_content = 'name:string,code:string,contacts:array<struct<personFamilyName:string,personGivenName:string,personRoles:array<string>,personTitle:string,col3:array<string>>>,score:int'
    assert glue_schema_reader.parse_type_string(type_str) == (expected_base, expected_content)

def test_get_polars_schema_handles_complex_types(glue_client, glue_schema_reader, glue_db, glue_table_complex):
    """Tests that complex types are handled correctly (e.g., array<string>)."""
    polars_schema = glue_schema_reader.get_polars_schema('test-db', 'test-table-complex')
    expected_schema = {
        'user_tags': pl.List(pl.Utf8),
        'user_profile': pl.Struct([
            pl.Field('name', pl.Utf8),
            pl.Field('age', pl.Int32)
        ]),
        'metadata': pl.List(pl.Struct([
            pl.Field('key', pl.Utf8),
            pl.Field('value', pl.Int64)
        ]))
    }

    assert str(polars_schema) == str(expected_schema)

def test_get_polars_schema_handles_very_complex_types(glue_client, glue_schema_reader, glue_db, glue_table_very_complex):
    """Tests that complex types are handled correctly (e.g., array<string>)."""
    polars_schema = glue_schema_reader.get_polars_schema('test-db', 'test-table-very-complex')
    expected_type = pl.List(
        pl.Struct([
            pl.Field('name', pl.Utf8),
            pl.Field('code', pl.Utf8),
            pl.Field('contacts', pl.List(
                pl.Struct([
                    pl.Field('personFamilyName', pl.Utf8),
                    pl.Field('personGivenName', pl.Utf8),
                    pl.Field('personRoles', pl.List(pl.Utf8)),
                    pl.Field('personTitle', pl.Utf8),
                    pl.Field('jobs', pl.List(pl.Utf8))
                ])
            )),
            pl.Field('score', pl.Int32)
        ])
    )
    expected_schema = {
        'user_tags': pl.List(pl.Utf8),
        'user_profile': pl.Struct([
            pl.Field('name', pl.Utf8),
            pl.Field('age', pl.Int32)
        ]),
        'metadata': pl.List(pl.Struct([
            pl.Field('key', pl.Utf8),
            pl.Field('value', pl.Int64)
        ])),
        'crazy': expected_type
    }

    assert str(polars_schema) == str(expected_schema)

def test_get_polars_type_correctly_parses_complex_nested_type(glue_schema_reader):
    type_str = 'array<struct<personFamilyName:string,personGivenName:string,personRoles:array<string>,personTitle:string,privileges:array<string>>>'
    result = glue_schema_reader.get_polars_type(type_str)
    expected_type = pl.List(
                pl.Struct([
                    pl.Field('personFamilyName', pl.Utf8),
                    pl.Field('personGivenName', pl.Utf8),
                    pl.Field('personRoles', pl.List(pl.Utf8)),
                    pl.Field('personTitle', pl.Utf8),
                    pl.Field('privileges', pl.List(pl.Utf8))
                ])
            )
    assert result == expected_type


def test_get_polars_type_correctly_parses_very_complex_nested_type(glue_schema_reader):
    type_str = 'array<struct<name:string,code:string,contacts:array<struct<personFamilyName:string,personGivenName:string,personRoles:array<string>,personTitle:string,privileges:array<string>>>>>'
    result = glue_schema_reader.get_polars_type(type_str)
    expected_type = pl.List(
        pl.Struct([
            pl.Field('name', pl.Utf8),
            pl.Field('code', pl.Utf8),
            pl.Field('contacts', pl.List(
                pl.Struct([
                    pl.Field('personFamilyName', pl.Utf8),
                    pl.Field('personGivenName', pl.Utf8),
                    pl.Field('personRoles', pl.List(pl.Utf8)),
                    pl.Field('personTitle', pl.Utf8),
                    pl.Field('privileges', pl.List(pl.Utf8))
                ])
            ))
        ])
    )
    assert result == expected_type