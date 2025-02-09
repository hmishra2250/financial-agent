# file_handling/cloud_storage.py

from google.cloud import storage
import logging
import os
from typing import Optional, List, Dict, Union

class CloudStorage:
    """Handles interactions with Google Cloud Storage (GCS)."""

    def __init__(self, bucket_name: str, credentials_path: Optional[str] = None, project_id: Optional[str] = None):
        """
        Initializes the GCS client.

        Args:
            bucket_name (str): The name of the GCS bucket.
            credentials_path (Optional[str]): Path to the service account key file (JSON).
                If None, uses Application Default Credentials (ADC).  ADC is recommended
                for most cases (running on GCP, using workload identity, etc.).
            project_id (Optional[str]): The GCP project ID. Required if using ADC and
                a default project is not set.
        """
        self.bucket_name = bucket_name
        self.logger = logging.getLogger(__name__)

        if credentials_path:
            # Use explicit credentials from the provided path
            self.client = storage.Client.from_service_account_json(credentials_path)
        else:
            # Use Application Default Credentials (ADC)
            try:
                # Pass project_id if provided, otherwise ADC will try to determine it.
                self.client = storage.Client(project=project_id)
            except Exception as e:
                self.logger.error(f"Failed to create GCS client with ADC: {e}")
                raise

        try:
            self.bucket = self.client.bucket(self.bucket_name)
            if not self.bucket.exists():
                raise ValueError(f"Bucket '{self.bucket_name}' does not exist.")
        except Exception as e:
            self.logger.error("Error accessing bucket: %s", e)
            raise

    def upload_file(self, local_file_path: str, gcs_file_path: str) -> bool:
        """
        Uploads a file to GCS.

        Args:
            local_file_path (str): The local path to the file.
            gcs_file_path (str): The desired path in the GCS bucket (blob name).

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            blob.upload_from_filename(local_file_path)
            self.logger.info(f"File '{local_file_path}' uploaded to 'gs://{self.bucket_name}/{gcs_file_path}'")
            return True
        except FileNotFoundError:
            self.logger.error(f"File not found: {local_file_path}")
            return False
        except Exception as e:
            self.logger.exception(f"Error uploading to GCS: {e}")  # Use exception for stack trace
            return False

    def download_file(self, gcs_file_path: str, local_file_path: str) -> bool:
        """
        Downloads a file from GCS.

        Args:
            gcs_file_path (str): The path of the file in the GCS bucket (blob name).
            local_file_path (str): The local path to save the downloaded file.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not self.blob_exists(gcs_file_path):
                self.logger.error(f"Blob does not exist: gs://{self.bucket_name}/{gcs_file_path}")
                return False

            blob = self.bucket.blob(gcs_file_path)
            # Ensure the directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            blob.download_to_filename(local_file_path)
            self.logger.info(f"File downloaded from 'gs://{self.bucket_name}/{gcs_file_path}' to '{local_file_path}'")
            return True
        except Exception as e:
            self.logger.exception(f"Error downloading from GCS: {e}")
            return False

    def list_files(self, prefix: str = '') -> List[Dict[str, Union[str, int]]]:
        """
        Lists files (blobs) in the bucket, optionally filtered by a prefix.

        Args:
            prefix (str):  Optional.  A prefix to filter the files (e.g., 'folder/').

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries, where each dictionary
                represents a file (blob) and contains information like 'name' and 'size'.
                Returns an empty list if no files are found or on error.
        """
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            file_list = []
            for blob in blobs:
                file_list.append({'name': blob.name, 'size': blob.size})
            return file_list
        except Exception as e:
            self.logger.exception(f"Error listing files in GCS: {e}")
            return []


    def blob_exists(self, gcs_file_path: str) -> bool:
        """
        Checks if a blob exists in the bucket.

        Args:
            gcs_file_path: Path

        Returns:
            bool: True/False
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            return blob.exists()
        except Exception as e:
            self.logger.exception("Exception Occurred: %s", e)
            return False

    def delete_blob(self, gcs_file_path: str) -> bool:
        """Deletes a blob from the bucket.

        Args:
            gcs_file_path: The path to the blob in GCS.

        Returns:
            bool: True if the blob was deleted successfully, False otherwise.
        """
        try:
            if not self.blob_exists(gcs_file_path):
                self.logger.warning(f"Blob does not exist: gs://{self.bucket_name}/{gcs_file_path}")
                return False # Indicate that deletion didn't happen (because it didn't exist)

            blob = self.bucket.blob(gcs_file_path)
            blob.delete()
            self.logger.info(f"Blob deleted: gs://{self.bucket_name}/{gcs_file_path}")
            return True
        except Exception as e:
            self.logger.exception(f"Error deleting blob from GCS: {e}")
            return False

# Example Usage (and for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # ---  Normally, you'd get these from config.py or environment variables ---
    bucket_name = os.environ.get("GCS_BUCKET_NAME")  #  Set this in your .env or environment
    credentials_path = os.environ.get("GCS_CREDENTIALS_PATH")  # Optional, for service account key
    project_id = os.environ.get("GCS_PROJECT_ID")  # Required if not using credentials_path and ADC isn't set up
    # ---

    storage = CloudStorage(bucket_name, credentials_path, project_id)

    # Create a dummy file for testing
    with open("test_upload.txt", "w") as f:
        f.write("This is a test file for GCS.")

    if storage.upload_file("test_upload.txt", "test/test_upload.txt"):
        print("Upload successful")

    if storage.blob_exists("test/test_upload.txt"):
        print("File exists")

    # Download the file
    if storage.download_file("test/test_upload.txt", "test_download.txt"):
        print("Download successful")

    # List files in the bucket
    files = storage.list_files(prefix="test/")  # List files in the 'test/' directory
    for file_info in files:
        print(f"File Name: {file_info['name']}, Size: {file_info['size']} bytes")

    # Delete the test file
    if storage.delete_blob("test/test_upload.txt"):
        print("Test blob deleted successfully.")

    # Clean up the dummy files
    os.remove("test_upload.txt")
    if os.path.exists("test_download.txt"):
        os.remove("test_download.txt")