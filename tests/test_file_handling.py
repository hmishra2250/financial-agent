# tests/test_file_handling.py

import pytest
from file_handling.cloud_storage import CloudStorage
from unittest.mock import patch, MagicMock, ANY, mock_open
import os
from google.cloud import storage
from google.cloud.storage import Bucket, Blob
from typing import List

# --- Tests for CloudStorage (GCS) ---

# Fixture for a mocked GCS client
@pytest.fixture
def mock_gcs_client():
    with patch('google.cloud.storage.Client') as MockClient:
        yield MockClient

# Fixture for a mocked GCS bucket
@pytest.fixture
def mock_bucket(mock_gcs_client):
    mock_bucket = MagicMock(spec=Bucket)
    mock_gcs_client.return_value.bucket.return_value = mock_bucket
    return mock_bucket

# Fixture for a mocked GCS blob
@pytest.fixture
def mock_blob():
    return MagicMock(spec=Blob)

def test_cloud_storage_init_with_credentials(mock_gcs_client):
    """Test initialization with explicit credentials."""
    CloudStorage('test-bucket', credentials_path='path/to/creds.json')
    mock_gcs_client.from_service_account_json.assert_called_once_with('path/to/creds.json')

def test_cloud_storage_init_with_adc(mock_gcs_client):
    """Test initialization with Application Default Credentials."""
    CloudStorage('test-bucket')
    mock_gcs_client.assert_called_once() # No args = ADC

def test_cloud_storage_upload_file_success(mock_gcs_client, mock_bucket, mock_blob):
    """Test successful file upload."""
    mock_bucket.blob.return_value = mock_blob  # Return the mock blob
    storage = CloudStorage('test-bucket')
    storage.bucket = mock_bucket # Mock bucket

    with patch("builtins.open", mock_open(read_data="test data")):# Mock opening the file
        success = storage.upload_file('local_file.txt', 'gcs_file.txt')

    assert success
    mock_bucket.blob.assert_called_once_with('gcs_file.txt')
    mock_blob.upload_from_filename.assert_called_once_with('local_file.txt')

def test_cloud_storage_upload_file_not_found(mock_gcs_client, mock_bucket):
    """Test uploading a nonexistent file."""
    storage = CloudStorage('test-bucket')
    storage.bucket = mock_bucket # mock the bucket
    success = storage.upload_file('nonexistent.txt', 'gcs_file.txt')
    assert not success

def test_cloud_storage_download_file_success(mock_gcs_client, mock_bucket, mock_blob):
    """Test successful file download."""
    mock_bucket.blob.return_value = mock_blob
    storage = CloudStorage('test-bucket')
    storage.bucket = mock_bucket

    success = storage.download_file('gcs_file.txt', 'local_file.txt')

    assert success
    mock_bucket.blob.assert_called_once_with('gcs_file.txt')
    mock_blob.download_to_filename.assert_called_once_with('local_file.txt')

def test_cloud_storage_download_file_error(mock_gcs_client, mock_bucket, mock_blob):
    """Test download failure (e.g., blob doesn't exist)."""
    mock_bucket.blob.return_value = mock_blob
    mock_blob.download_to_filename.side_effect = Exception("Download error") # Simulate error
    storage = CloudStorage('test-bucket')
    storage.bucket = mock_bucket

    success = storage.download_file('gcs_file.txt', 'local_file.txt')

    assert not success
    mock_bucket.blob.assert_called_once_with('gcs_file.txt')
    mock_blob.download_to_filename.assert_called_once_with('local_file.txt')


def test_cloud_storage_list_files_success(mock_gcs_client, mock_bucket):
    """Test listing files with a prefix."""
    # Mock the list_blobs method to return a list of mock blobs
    mock_blob1 = MagicMock(spec=Blob, name='file1.txt', size=100)
    mock_blob2 = MagicMock(spec=Blob, name='file2.txt', size=200)
    mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]

    storage = CloudStorage('test-bucket')
    storage.bucket = mock_bucket
    files = storage.list_files(prefix='test/')

    assert len(files) == 2
    assert files[0] == {'name': 'file1.txt', 'size': 100}
    assert files[1] == {'name': 'file2.txt', 'size': 200}
    mock_bucket.list_blobs.assert_called_once_with(prefix='test/')

def test_cloud_storage_list_files_empty(mock_gcs_client, mock_bucket):
    """Test listing files when the bucket/prefix is empty."""
    mock_bucket.list_blobs.return_value = []  # Return an empty list
    storage = CloudStorage('test-bucket')
    storage.bucket = mock_bucket
    files = storage.list_files(prefix='empty/')
    assert len(files) == 0
    mock_bucket.list_blobs.assert_called_once_with(prefix='empty/')

def test_cloud_storage_list_files_error(mock_gcs_client, mock_bucket):
    """Test error during file listing."""
    mock_bucket.list_blobs.side_effect = Exception("Listing error")  # Simulate an error
    storage = CloudStorage('test-bucket')
    storage.bucket = mock_bucket
    files = storage.list_files()  # No prefix
    assert len(files) == 0  # Should return an empty list on error
    mock_bucket.list_blobs.assert_called_once_with(prefix='')

def test_cloud_storage_blob_exists_true(mock_gcs_client, mock_bucket, mock_blob):
    """Test blob_exists method when blob exists."""
    mock_bucket.blob.return_value = mock_blob
    mock_blob.exists.return_value = True
    storage = CloudStorage("test-bucket")
    storage.bucket = mock_bucket

    exists = storage.blob_exists("test_file.txt")
    assert exists is True
    mock_bucket.blob.assert_called_once_with("test_file.txt")
    mock_blob.exists.assert_called_once()

def test_cloud_storage_blob_exists_false(mock_gcs_client, mock_bucket, mock_blob):
    """Test blob_exists method when the blob doesn't exist"""
    mock_bucket.blob.return_value = mock_blob
    mock_blob.exists.return_value = False

    storage = CloudStorage("test-bucket")
    storage.bucket = mock_bucket

    exists = storage.blob_exists("nonexistent_file.txt")
    assert exists is False
    mock_bucket.blob.assert_called_once_with("nonexistent_file.txt")
    mock_blob.exists.assert_called_once()

def test_cloud_storage_blob_exists_exception(mock_gcs_client, mock_bucket, mock_blob):
    """Test blob_exists method when exception is raised"""
    mock_bucket.blob.return_value = mock_blob
    mock_blob.exists.side_effect = Exception("Blob Error")
    storage = CloudStorage("test-bucket")
    storage.bucket = mock_bucket

    exists = storage.blob_exists("test_file.txt")
    assert exists is False
    mock_bucket.blob.assert_called_once_with("test_file.txt")
    mock_blob.exists.assert_called_once()