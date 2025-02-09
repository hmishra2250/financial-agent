# config.py
import os
from dotenv import load_dotenv

class Config:
    """
    Configuration settings for the application.  Handles defaults,
    type conversions, and basic validation.
    """

    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # --- Data Ingestion ---
        self.ingestion_method = self._get_env('INGESTION_METHOD', 'sftp')
        self.sftp_host = self._get_env('SFTP_HOST', '0.0.0.0')
        self.sftp_port = self._get_env('SFTP_PORT', 22, int)
        self.sftp_username = self._get_env('SFTP_USERNAME', 'admin')
        self.sftp_password = self._get_env('SFTP_PASSWORD', 'admin')
        self.sftp_private_key_path = self._get_env('SFTP_PRIVATE_KEY_PATH', '~/.ssh/id_rsa')
        self.sftp_private_key_passphrase = self._get_env('SFTP_PRIVATE_KEY_PASSPHRASE', '')
        self.sftp_remote_file = self._get_env('SFTP_REMOTE_FILE', '')
        self.sftp_file_type = self._get_env('SFTP_FILE_TYPE', 'csv')
        self.sftp_comments_file = self._get_env("SFTP_COMMENTS_FILE", '')
        self.sftp_comments_file_type = self._get_env("SFTP_COMMENTS_FILE_TYPE", "csv")

        # --- Preprocessing ---
        self.system_b_column = self._get_env('SYSTEM_B_COLUMN', 'recon_sub_status')
        self.not_found_value = self._get_env('NOT_FOUND_VALUE', 'Not Found-SysB')
        self.csv_export_columns = ['txn_ref_id', 'sys_a_amount_attribute_1', 'sys_a_date']  # Keep as list, no need for env var
        self.date_columns = ['date']  # Keep as list

        # --- File Handling (Google Cloud Storage) ---
        self.gcs_bucket_name = self._get_env('GCS_BUCKET_NAME')
        # Use Application Default Credentials (ADC) or a service account key file.
        self.gcs_credentials_path = self._get_env('GCS_CREDENTIALS_PATH')  # Optional: Path to JSON key file
        self.gcs_project_id = self._get_env('GCS_PROJECT_ID')  # REQUIRED if not using ADC with a project set.
        self.gcs_categorized_file_path = self._get_env('GCS_CATEGORIZED_FILE_PATH', 'processed/not_found_sys_b/categorized_data.csv')
        self.gcs_resolved_folder = self._get_env('GCS_RESOLVED_FOLDER', 'processed/resolved')
        self.gcs_unresolved_folder = self._get_env('GCS_UNRESOLVED_FOLDER', 'processed/unresolved')
        self.local_temp_dir = self._get_env("LOCAL_TEMP_DIR", "temp")

        # --- Resolution Handler ---
        self.openai_api_key = self._get_env('OPENAI_API_KEY')
        self.openai_model_name = self._get_env('OPENAI_MODEL_NAME', 'gpt-3.5-turbo')
        self.num_clusters = self._get_env("NUM_CLUSTERS", 3, int)

        # --- Reporting ---
        self.log_file_path = self._get_env('LOG_FILE_PATH', 'logs/app.log')

        # ---Sentence Transformer---
        self.model_path = self._get_env("MODEL_PATH", "model/")

    def _get_env(self, var_name, default=None, type_cast=str):
        """
        Retrieves an environment variable, providing a default value and
        optional type casting.  Raises ValueError if required and not found.

        Args:
            var_name: The name of the environment variable.
            default:  The default value if the variable is not found.
            type_cast: A callable (e.g., int, float, bool) to convert the value.

        Returns:
            The environment variable value (converted if type_cast is provided),
            or the default value.

        Raises:
            ValueError: If the environment variable is not found and no default
                is provided.
        """
        value = os.environ.get(var_name)
        if value is None:
            if default is not None:
                return default
            else:
                raise ValueError(f"Required environment variable '{var_name}' not found.")
        try:
            return type_cast(value)
        except ValueError as e:
            raise ValueError(f"Invalid value for environment variable '{var_name}': {e}")


    def validate(self):
        """
        Performs additional validation checks on configuration settings.
        This is a good place to check for things like valid file paths
        (if they are expected to exist), or relationships between settings.
        """

        # Example: Check if local_temp_dir is a valid directory
        if not os.path.isdir(self.local_temp_dir):
            os.makedirs(self.local_temp_dir, exist_ok=True) #optionally create the directory
            # raise ValueError(f"LOCAL_TEMP_DIR '{self.local_temp_dir}' is not a valid directory.")

        # GCS Validation:  Check for *either* ADC working *or* credentials file
        if self.gcs_credentials_path and not os.path.exists(self.gcs_credentials_path):
            raise ValueError(f"GCS_CREDENTIALS_PATH '{self.gcs_credentials_path}' does not exist.")

        if not self.gcs_credentials_path and not self.gcs_project_id:
            #If not provided a credentials path, must at least have a project id
            raise ValueError("Either GCS_CREDENTIALS_PATH or GCS_PROJECT_ID must be set.")

        # Add more validation as needed.  For example, you could check if
        # SFTP_HOST is a valid hostname using a library like `validators`.
        return True  #if we make it here we are valid.



# Example usage (at the end of the file, or in another module):
config = Config()
config.validate()  # Important: Call validate() after creating the Config object.

# Now you can access the configuration settings:
# print(f"GCS Bucket Name: {config.gcs_bucket_name}")
# print(f"SFTP Host: {config.sftp_host}")