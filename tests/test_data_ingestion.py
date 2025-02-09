# tests/test_data_ingestion.py

import pytest
import pandas as pd
from data_ingestion.sftp_ingestor import SFTPIngestor
from data_ingestion.file_upload_ingestor import FileUploadIngestor
from unittest.mock import patch, MagicMock  # Import mock
import io
import os

# --- Tests for SFTPIngestor ---
@patch('paramiko.Transport')
@patch('paramiko.SFTPClient.from_transport')
def test_sftp_ingestor_connect_success(mock_from_transport, mock_transport):
    """Test successful SFTP connection."""
    mock_sftp = MagicMock()
    mock_from_transport.return_value = mock_sftp
    mock_transport_instance = MagicMock()
    mock_transport.return_value = mock_transport_instance

    ingestor = SFTPIngestor('host', 22, 'user', 'pass')
    ingestor.connect()  # Call connect explicitly

    mock_transport.assert_called_once_with(('host', 22))
    mock_transport_instance.connect.assert_called_once_with(username='user', password='pass')
    mock_from_transport.assert_called_once_with(mock_transport_instance)
    assert ingestor.sftp == mock_sftp

@patch('paramiko.Transport')
@patch('paramiko.SFTPClient.from_transport')
def test_sftp_ingestor_connect_failure(mock_from_transport, mock_transport):
    """Test SFTP connection failure."""
    mock_transport.side_effect = Exception("Connection failed")
    ingestor = SFTPIngestor('host', 22, 'user', 'pass')

    with pytest.raises(Exception, match="Connection failed"):
        ingestor.connect()

    mock_transport.assert_called_once_with(('host', 22))
    mock_from_transport.assert_not_called()

@patch('paramiko.Transport')
@patch('paramiko.SFTPClient.from_transport')
def test_sftp_ingestor_fetch_data_success(mock_from_transport, mock_transport):
    """Test fetching data (CSV) successfully."""
    mock_sftp = MagicMock()
    mock_from_transport.return_value = mock_sftp
    mock_transport_instance = MagicMock()
    mock_transport.return_value = mock_transport_instance

    # Mock the open method and the file-like object it returns
    mock_file = MagicMock()
    mock_sftp.open.return_value.__enter__.return_value = mock_file

    # Simulate reading CSV data
    mock_file.read.return_value.decode.return_value = "col1,col2\n1,2\n3,4"

    ingestor = SFTPIngestor('host', 22, 'user', 'pass')
    # ingestor.connect() # Connection is handled within fetch_data if not exists
    df = ingestor.fetch_data('remote_path.csv', 'csv')

    mock_sftp.open.assert_called_once_with('remote_path.csv', 'r')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ['col1', 'col2']

@patch('paramiko.Transport')
@patch('paramiko.SFTPClient.from_transport')
def test_sftp_ingestor_fetch_data_file_not_found(mock_from_transport, mock_transport):
    """Test handling FileNotFoundError."""

    mock_sftp = MagicMock()
    mock_from_transport.return_value = mock_sftp
    mock_transport_instance = MagicMock()
    mock_transport.return_value = mock_transport_instance

    mock_sftp.open.side_effect = FileNotFoundError

    ingestor = SFTPIngestor('host', 22, 'user', 'pass')
    #ingestor.connect()
    df = ingestor.fetch_data('nonexistent_file.csv', 'csv')
    assert df is None

@patch('paramiko.Transport')
@patch('paramiko.SFTPClient.from_transport')
def test_sftp_ingestor_fetch_data_unsupported_file_type(mock_from_transport, mock_transport):
    """Test handling unsupported file type."""

    mock_sftp = MagicMock()
    mock_from_transport.return_value = mock_sftp
    mock_transport_instance = MagicMock()
    mock_transport.return_value = mock_transport_instance
    ingestor = SFTPIngestor('host', 22, 'user', 'pass')
    # ingestor.connect()
    with pytest.raises(ValueError, match="Unsupported file type"):
        ingestor.fetch_data('remote_path.txt', 'txt')

# --- Tests for FileUploadIngestor ---

def test_file_upload_ingestor_csv_success():
  """Test successful file upload ingestion for CSV."""

  # Create some dummy CSV data as bytes
  csv_data = "col1,col2\n1,2\n3,4".encode('utf-8')
  ingestor = FileUploadIngestor()
  df = ingestor.ingest_data(csv_data, 'csv')
  assert isinstance(df, pd.DataFrame)
  assert len(df) == 2
  assert list(df.columns) == ['col1', 'col2']

def test_file_upload_ingestor_excel_success():
    """Test successful file upload ingestion for Excel."""

    # Create a dummy Excel file (using pandas for convenience)
    data = {'col1': [1, 3], 'col2': [2, 4]}
    df = pd.DataFrame(data)

    # Use BytesIO to write to an in-memory byte stream
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)  # Write to the buffer
    excel_buffer.seek(0) # Reset buffer
    excel_data = excel_buffer.read() # Read the data


    ingestor = FileUploadIngestor()
    df_result = ingestor.ingest_data(excel_data, 'excel')

    assert isinstance(df_result, pd.DataFrame)
    pd.testing.assert_frame_equal(df, df_result)  # Compare with original DataFrame
    assert len(df_result) == 2
    assert list(df_result.columns) == ['col1', 'col2']

def test_file_upload_ingestor_unsupported_file_type():
  """Test unsupported file type for file upload."""

  ingestor = FileUploadIngestor()
  with pytest.raises(ValueError, match="Unsupported file type"):
    ingestor.ingest_data(b"some data", 'txt')  # Use bytes directly