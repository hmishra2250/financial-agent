# data_ingestion/sftp_ingestor.py
import paramiko
import os
import logging
from io import StringIO  # For in-memory file handling
import pandas as pd

class SFTPIngestor:
    """
    Handles fetching data from an SFTP server.
    """

    def __init__(self, host, port, username, password, private_key_path=None, private_key_passphrase=None):
        """
        Initializes the SFTP client.

        Args:
            host (str): SFTP server hostname.
            port (int): SFTP server port.
            username (str): SFTP username.
            password (str): SFTP password.  Prefer private key authentication.
            private_key_path (str, optional): Path to the private key file.
            private_key_passphrase (str, optional): Passphrase for the private key.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.private_key_passphrase = private_key_passphrase
        self.transport = None  # Initialize transport to None
        self.sftp = None      # Initialize sftp to None

    def connect(self):
        """
        Establishes an SFTP connection.  Prioritizes key-based authentication.
        """
        try:
            if self.private_key_path:
                private_key = paramiko.RSAKey.from_private_key_file(
                    self.private_key_path, password=self.private_key_passphrase
                )
                self.transport = paramiko.Transport((self.host, self.port))
                self.transport.connect(username=self.username, pkey=private_key)
            else:
                self.transport = paramiko.Transport((self.host, self.port))
                self.transport.connect(username=self.username, password=self.password)

            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            logging.info(f"Successfully connected to SFTP server: {self.host}")

        except Exception as e:
            logging.error(f"Failed to connect to SFTP server: {e}")
            raise

    def fetch_data(self, remote_path, file_type='csv'):
        """
        Fetches data from the specified remote path.

        Args:
            remote_path (str): The path to the file on the SFTP server.
            file_type (str):  'csv' or 'excel'.  Handles basic format validation.

        Returns:
            pandas.DataFrame: The data loaded into a pandas DataFrame.  Returns None on error.

        Raises:
            ValueError: If the file type is not supported.
        """
        try:
            if not self.sftp:
                self.connect()  # Establish connection if not already connected

            if file_type.lower() == 'csv':
                with self.sftp.open(remote_path, 'r') as f:
                    data = pd.read_csv(f)
                    return data
            elif file_type.lower() == 'excel':
                with self.sftp.open(remote_path, 'r') as f:
                    data = pd.read_excel(f)
                    return data
            else:
                raise ValueError("Unsupported file type.  Only 'csv' and 'excel' are supported.")

        except FileNotFoundError:
            logging.error(f"File not found at remote path: {remote_path}")
            return None
        except Exception as e:
            logging.error(f"Error fetching data from SFTP: {e}")
            return None
        finally:
            if self.sftp:
                self.sftp.close()
            if self.transport:
                self.transport.close()


    def disconnect(self):
        """Closes the SFTP connection."""
        if self.sftp:
            self.sftp.close()
        if self.transport:
            self.transport.close()


# Example Usage (and for testing - move to tests/test_data_ingestion.py later)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    #  ---  Normally, you'd get these from config.py or environment variables ---
    host = os.environ.get("SFTP_HOST")
    port = int(os.environ.get("SFTP_PORT", 22))  # Default to 22 if not set
    username = os.environ.get("SFTP_USERNAME")
    password = os.environ.get("SFTP_PASSWORD")
    remote_file = os.environ.get("SFTP_REMOTE_FILE")
    #  ---

    ingestor = SFTPIngestor(host, port, username, password)
    df = ingestor.fetch_data(remote_file)
    if df is not None:
        print(df.head())