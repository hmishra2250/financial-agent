# tests/test_preprocessing.py
import pytest
import pandas as pd
from preprocessing.data_cleaner import DataCleaner
from preprocessing.categorizer import Categorizer
import logging
import os
from unittest.mock import MagicMock

# --- Tests for DataCleaner ---

def test_data_cleaner_empty_dataframe():
    """Test cleaning an empty DataFrame."""
    cleaner = DataCleaner()
    empty_df = pd.DataFrame()
    cleaned_df = cleaner.clean_data(empty_df)
    assert cleaned_df.empty

def test_data_cleaner_drop_duplicates():
    """Test dropping duplicate rows."""
    cleaner = DataCleaner()
    data = {'col1': [1, 1, 2], 'col2': ['a', 'a', 'b']}
    df = pd.DataFrame(data)
    cleaned_df = cleaner.clean_data(df)
    assert len(cleaned_df) == 2
    assert list(cleaned_df['col1']) == [1, 2]

def test_data_cleaner_fill_na_numeric():
    """Test filling NaN values in numeric columns."""
    cleaner = DataCleaner()
    data = {'col1': [1, None, 2], 'col2': ['a', 'b', 'c']}
    df = pd.DataFrame(data)
    cleaned_df = cleaner.clean_data(df)
    assert cleaned_df['col1'].isnull().sum() == 0
    assert list(cleaned_df['col1']) == [1.0, 0.0, 2.0]

def test_data_cleaner_fill_na_string():
    """Test filling NaN values in string columns."""
    cleaner = DataCleaner()
    data = {'col1': [1, 2, 3], 'col2': ['a', None, 'c']}
    df = pd.DataFrame(data)
    cleaned_df = cleaner.clean_data(df)
    assert cleaned_df['col2'].isnull().sum() == 0
    assert list(cleaned_df['col2']) == ['a', 'Unknown', 'c']

def test_data_cleaner_mixed_na():
    """Test handling mixed NaN values (numeric and string)."""
    cleaner = DataCleaner()
    data = {'col1': [1, None, 2], 'col2': ['a', None, 'c']}
    df = pd.DataFrame(data)
    cleaned_df = cleaner.clean_data(df)
    assert cleaned_df.isnull().sum().sum() == 0  # No NaN values left

def test_data_cleaner_date_conversion_success():
    """Test successful date column conversion."""
    cleaner = DataCleaner()
    data = {'date_col': ['2023-01-01', '2023-02-01', '2023-03-01']}
    df = pd.DataFrame(data)
    cleaned_df = cleaner.clean_data(df, date_columns=['date_col'])
    assert pd.api.types.is_datetime64_any_dtype(cleaned_df['date_col'])
    assert str(cleaned_df['date_col'].dtype) == 'datetime64[ns]'

def test_data_cleaner_date_conversion_invalid_date():
    """Test handling invalid date strings."""
    cleaner = DataCleaner()
    data = {'date_col': ['2023-01-01', 'invalid_date', '2023-03-01']}
    df = pd.DataFrame(data)
    cleaned_df = cleaner.clean_data(df, date_columns=['date_col'])
    assert pd.api.types.is_datetime64_any_dtype(cleaned_df['date_col'])  # Still datetime
    assert cleaned_df['date_col'].isnull().sum() == 1  # One NaT value

def test_data_cleaner_date_conversion_nonexistent_column():
    """Test handling a nonexistent date column."""
    cleaner = DataCleaner()
    data = {'col1': [1, 2, 3]}
    df = pd.DataFrame(data)
    cleaned_df = cleaner.clean_data(df, date_columns=['nonexistent_col'])
    # Should not raise an error; just does nothing to that column
    assert 'nonexistent_col' not in cleaned_df.columns


# --- Tests for Categorizer ---

def test_categorizer_empty_dataframe():
    """Test categorizing an empty DataFrame."""
    categorizer = Categorizer()
    empty_df = pd.DataFrame()
    result_df = categorizer.categorize_data(empty_df, 'system_b_status')
    assert result_df is None

def test_categorizer_column_not_found():
    """Test handling a missing categorization column."""
    categorizer = Categorizer()
    data = {'col1': [1, 2, 3]}
    df = pd.DataFrame(data)
    result_df = categorizer.categorize_data(df, 'nonexistent_col')
    assert result_df is None

def test_categorizer_filter_success():
    """Test successful filtering of 'Not Found Sys B' records."""
    categorizer = Categorizer()
    data = {'system_b_status': ['Found', 'Not Found Sys B', 'Found']}
    df = pd.DataFrame(data)
    result_df = categorizer.categorize_data(df, 'system_b_status')
    assert len(result_df) == 1
    assert list(result_df['system_b_status']) == ['Not Found Sys B']

def test_categorizer_filter_no_matching_records():
    """Test filtering when no records match the criteria."""
    categorizer = Categorizer()
    data = {'system_b_status': ['Found', 'Found', 'Found']}
    df = pd.DataFrame(data)
    result_df = categorizer.categorize_data(df, 'system_b_status')
    assert len(result_df) == 0

def test_categorizer_filter_custom_not_found_value():
    """Test filtering with a custom 'not found' value."""
    categorizer = Categorizer()
    data = {'system_b': ['OK', 'Missing', 'OK']}
    df = pd.DataFrame(data)
    result_df = categorizer.categorize_data(df, 'system_b', 'Missing')
    assert len(result_df) == 1
    assert list(result_df['system_b']) == ['Missing']

def test_categorizer_export_to_csv_success(tmpdir):
    """Test successful export to CSV (using pytest's tmpdir fixture)."""
    categorizer = Categorizer()
    data = {'col1': [1, 2], 'col2': ['a', 'b']}
    df = pd.DataFrame(data)
    file_path = os.path.join(tmpdir, 'test.csv')
    categorizer.export_to_csv(df, file_path)
    assert os.path.exists(file_path)
    loaded_df = pd.read_csv(file_path)
    pd.testing.assert_frame_equal(df, loaded_df)

def test_categorizer_export_to_csv_empty_dataframe(tmpdir):
    """Test exporting an empty DataFrame to CSV."""
    categorizer = Categorizer()
    empty_df = pd.DataFrame()
    file_path = os.path.join(tmpdir, 'test.csv')
    # Should not raise an error, but also not create a file.
    categorizer.export_to_csv(empty_df, file_path)
    assert os.path.exists(file_path) == False

def test_categorizer_export_to_csv_selected_columns(tmpdir):
    """Test exporting to CSV with only selected columns"""
    categorizer = Categorizer()
    data = {'col1': [1, 2], 'col2': ['a', 'b'], "col3": [3, 4]}
    df = pd.DataFrame(data)
    file_path = os.path.join(tmpdir, "test.csv")
    categorizer.export_to_csv(df, file_path, columns=["col1", "col2"])
    assert os.path.exists(file_path)
    loaded_df = pd.read_csv(file_path)
    assert "col3" not in loaded_df.columns
    assert list(loaded_df.columns) == ["col1", "col2"]

def test_categorizer_export_to_csv_error_handling(tmpdir, caplog):
    """Test the error handling while saving a CSV file"""
    categorizer = Categorizer()
    data = {'col1': [1, 2], 'col2': ['a', 'b']}
    df = pd.DataFrame(data)
    file_path = os.path.join(tmpdir, "nonexistent_dir/test.csv")  # Nonexistent directory

    with caplog.at_level(logging.ERROR):
        categorizer.export_to_csv(df, file_path)

    assert "Error exporting data to CSV" in caplog.text