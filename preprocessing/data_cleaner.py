# preprocessing/data_cleaner.py
import pandas as pd
import logging

class DataCleaner:
    """
    Cleans the input DataFrame.
    """

    def __init__(self):
        pass

    def clean_data(self, df, date_columns=None):
        """
        Performs data cleaning operations.

        Args:
            df (pd.DataFrame): The input DataFrame.
            date_columns: list of date columns

        Returns:
            pd.DataFrame: The cleaned DataFrame.
        """
        if df is None or df.empty:
            logging.warning("Input DataFrame is empty.  Returning empty DataFrame.")
            return pd.DataFrame()

        # Drop duplicate rows
        df = df.drop_duplicates()

        # Handle missing values (example: fill with a default value)
        # Customize this based on your specific needs.
        for col in df.columns:
            if df[col].isnull().any():
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(0)  # Fill numeric NaNs with 0
                else:
                    df[col] = df[col].fillna('Unknown')  # Fill other NaNs with 'Unknown'

        # Convert date columns to datetime objects
        if date_columns:
          for col in date_columns:
            if col in df.columns:
              try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
              except Exception as e:
                logging.error("error in converting to date: %s", e)
        return df