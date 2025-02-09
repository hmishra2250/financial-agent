# data_ingestion/file_upload_ingestor.py
import pandas as pd
import logging
import io

class FileUploadIngestor:
    """Handles data ingestion from a direct file upload (e.g., from a web form)."""

    def __init__(self):
        pass

    def ingest_data(self, file_content, file_type='csv'):
        """
        Ingests data from an in-memory file-like object.

        Args:
            file_content (bytes): The file content as bytes.
            file_type (str): 'csv' or 'excel'.

        Returns:
            pandas.DataFrame: The loaded DataFrame.
            None: If there's an error.

        Raises:
            ValueError: For unsupported file types.
        """
        try:
            if file_type.lower() == 'csv':
                # Use io.StringIO to treat the bytes as a file
                df = pd.read_csv(io.StringIO(file_content.decode('ISO-8859-1')))
                return df
            elif file_type.lower() == 'excel':
                df = pd.read_excel(io.BytesIO(file_content))
                return df
            else:
                raise ValueError("Unsupported file type.  Only 'csv' and 'excel' are supported.")
        except Exception as e:
            logging.error(f"Error ingesting file: {e}")
            return None