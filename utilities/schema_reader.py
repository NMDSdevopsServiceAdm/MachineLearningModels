import polars as pl
import boto3
from typing import Dict, List, Tuple
from polars import DataType


class GlueSchemaReader:
    """
    Retrieves and parses a schema from an AWS Glue database for use with Polars.
    """

    GLUE_TO_POLARS_MAPPING: dict[str, pl.DataType] = {
        "tinyint": pl.Int8(),
        "smallint": pl.Int16(),
        "int": pl.Int32(),
        "integer": pl.Int32(),
        "bigint": pl.Int64(),
        "float": pl.Float32(),
        "double": pl.Float64(),
        "string": pl.Utf8(),
        "varchar": pl.Utf8(),
        "char": pl.Utf8(),
        "boolean": pl.Boolean(),
        "date": pl.Date(),
        "timestamp": pl.Datetime(),
        "decimal": pl.Decimal(),
        # Add more mappings as needed
    }

    def __init__(self):
        self.glue_client = boto3.client("glue")

    def _get_glue_table_schema(self, database_name: str, table_name: str) -> List[Dict]:
        """
        Retrieves the column schema from an AWS Glue table.

        Args:
            database_name (str): The name of the Glue database.
            table_name (str): The name of the table within the database.

        Returns:
            List[Dict]: A list of dictionaries, each representing a column.

        Raises:
            ValueError: If the Glue table cannot be found or retrieved.
            Exception: If an unknown error occurs.
        """
        try:
            response = self.glue_client.get_table(
                DatabaseName=database_name, Name=table_name
            )
            return response["Table"]["StorageDescriptor"]["Columns"]
        except self.glue_client.exceptions.EntityNotFoundException:
            raise ValueError(f"Glue table '{database_name}.{table_name}' not found.")
        except Exception as e:
            raise Exception(f"Failed to retrieve schema from Glue: {e}")

    def split_by_top_level_comma(self, s: str) -> List[str]:
        """
        Splits a string by commas, but only at the top level, respecting
        nested angle brackets.

        Example: "a,b,c" -> ["a", "b", "c"]
        Example: "a,array<struct<x:int,y:string>>,c" -> ["a", "array<struct<x:int,y:string>>", "c"]
        """
        parts = []
        bracket_count = 0
        start_index = 0
        for i, char in enumerate(s):
            if char == "<":
                bracket_count += 1
            elif char == ">":
                bracket_count -= 1
            elif char == "," and bracket_count == 0:
                parts.append(s[start_index:i].strip())
                start_index = i + 1
        parts.append(s[start_index:].strip())
        return parts

    def parse_type_string(self, type_str: str) -> Tuple[str, str]:
        """
        Parses a Glue type string into a base type and its content.

        Args:
            type_str (str): The type string to parse.

        Returns:
            Tuple[str, str]: The base type and its content.

        Examples:
        'array<string>' -> ('array', 'string')
        'struct<...>' -> ('struct', 'name:string,description:string')
        'string' -> ('string', '')
        """
        if "<" in type_str:
            base_type, content = type_str.split("<", 1)
            content = content.removesuffix(">")
            return base_type.lower(), content
        return type_str.lower(), ""

    def get_polars_type(self, type_str: str) -> DataType:
        """
        Recursively parses a complex Glue type string into a Polars DataType.
        """
        base_type, content = self.parse_type_string(type_str)

        if base_type == "array":
            inner_type = self.get_polars_type(content)
            return pl.List(inner_type)

        elif base_type == "struct":
            fields = self.split_by_top_level_comma(content)
            struct_fields = []
            for field in fields:
                field_name, field_type = field.split(":", 1)
                inner_type = self.get_polars_type(field_type)
                struct_fields.append(pl.Field(field_name, inner_type))
            return pl.Struct(struct_fields)

        elif base_type == "map":
            key_type_str, value_type_str = content.split(",", 1)
            key_type = self.get_polars_type(key_type_str)
            value_type = self.get_polars_type(value_type_str)
            # A Glue map is represented as a list of structs in Polars
            return pl.List(
                pl.Struct([pl.Field("key", key_type), pl.Field("value", value_type)])
            )

        elif base_type in self.GLUE_TO_POLARS_MAPPING:
            return self.GLUE_TO_POLARS_MAPPING[base_type]
        else:
            raise ValueError(f"Unsupported Glue data type: '{base_type}'")

    def get_polars_schema(
        self, database_name: str, table_name: str
    ) -> Dict[str, DataType]:
        """
        Converts a Glue table schema into a Polars schema dictionary, handling complex types.
        """
        glue_schema = self._get_glue_table_schema(database_name, table_name)
        polars_schema = {}
        for column in glue_schema:
            col_name = column["Name"]
            glue_type = column["Type"]
            polars_schema[col_name] = self.get_polars_type(glue_type)

        return polars_schema
