import polars as pl
import boto3
from typing import Dict, List


class GlueSchemaReader:
    """
    Retrieves and parses a schema from an AWS Glue database for use with Polars.
    """
    GLUE_TO_POLARS_MAPPING = {
        'tinyint': pl.Int8,
        'smallint': pl.Int16,
        'int': pl.Int32,
        'integer': pl.Int32,
        'bigint': pl.Int64,
        'float': pl.Float32,
        'double': pl.Float64,
        'string': pl.Utf8,
        'varchar': pl.Utf8,
        'char': pl.Utf8,
        'boolean': pl.Boolean,
        'date': pl.Date,
        'timestamp': pl.Datetime,
        'decimal': pl.Decimal
        # Add more mappings as needed
    }

    def __init__(self):
        """Initializes the Boto3 Glue client."""
        self.glue_client = boto3.client('glue')

    def _get_glue_table_schema(self, database_name: str, table_name: str) -> List[Dict]:
        """
        Retrieves the column schema from an AWS Glue table.

        Args:
            database_name (str): The name of the Glue database.
            table_name (str): The name of the table within the database.

        Returns:
            List[Dict]: A list of dictionaries, each representing a column.

        Raises:
            Exception: If the Glue table cannot be found or retrieved.
        """
        try:
            response = self.glue_client.get_table(
                DatabaseName=database_name,
                Name=table_name
            )
            return response['Table']['StorageDescriptor']['Columns']
        except self.glue_client.exceptions.EntityNotFoundException:
            raise ValueError(f"Glue table '{database_name}.{table_name}' not found.")
        except Exception as e:
            raise Exception(f"Failed to retrieve schema from Glue: {e}")

    def get_polars_schema(self, database_name: str, table_name: str) -> Dict[str, pl.DataType]:
        """
        Converts a Glue table schema into a Polars schema dictionary.

        Args:
            database_name (str): The name of the Glue database.
            table_name (str): The name of the table within the database.

        Returns:
            Dict[str, pl.DataType]: A Polars schema dictionary.

        Raises:
            ValueError: If an unsupported Glue data type is encountered.
        """
        glue_schema = self._get_glue_table_schema(database_name, table_name)
        polars_schema = {}
        for column in glue_schema:
            col_name = column['Name']
            glue_type = column['Type'].lower().split('<')[0]  # Handles complex types like 'array<string>'

            if glue_type not in self.GLUE_TO_POLARS_MAPPING:
                raise ValueError(f"Unsupported Glue data type: '{glue_type}' for column '{col_name}'.")

            polars_schema[col_name] = self.GLUE_TO_POLARS_MAPPING[glue_type]

        return polars_schema