# preprocessing/categorizer.py
import pandas as pd
import logging

class Categorizer:
    """
    Categorizes records based on specific criteria.
    """

    def __init__(self):
        pass

    def categorize_data(self, df, system_b_column, not_found_value="Not Found-SysB"):
        """
        Filters data for "Not Found Sys B" records and exports to CSV.

        Args:
            df (pd.DataFrame): The input DataFrame.
            system_b_column (str): The column name indicating System B status.
            not_found_value (str): The value indicating "Not Found Sys B".

        Returns:
            pd.DataFrame:  DataFrame containing only the "Not Found Sys B" records.
            None: If the input DataFrame is empty or the specified column doesn't exist.
        """
        if df is None or df.empty:
            logging.warning("Input DataFrame is empty.  Returning None.")
            return None

        if system_b_column not in df.columns:
            logging.error(f"Column '{system_b_column}' not found in DataFrame.")
            return None

        # Filter for "Not Found Sys B" records
        not_found_df = df[df[system_b_column].str.contains(not_found_value)]
        return not_found_df

    def export_to_csv(self, df, file_path, columns=None):
        """
        Exports a DataFrame to a CSV file.

        Args:
          df: Dataframe to export
          file_path: File path
          columns: List of columns. Defaults to None.
        """

        if df is None or df.empty:
            logging.warning("DataFrame is empty.  Not exporting to CSV.")
            return
        if columns:
          df = df[columns]

        try:
            df.to_csv(file_path, index=False)
            logging.info(f"Data successfully exported to {file_path}")
        except Exception as e:
            logging.error(f"Error exporting data to CSV: {e}")