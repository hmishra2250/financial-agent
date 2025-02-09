import gradio as gr
import pandas as pd
import os
import re
from data_ingestion.sftp_ingestor import SFTPIngestor
from data_ingestion.file_upload_ingestor import FileUploadIngestor
from preprocessing.data_cleaner import DataCleaner
from preprocessing.categorizer import Categorizer
from file_handling.cloud_storage import CloudStorage
from resolution_handler.llm_classifier import LLMClassifier
from resolution_handler.resolution_actions import ResolutionActions
from reporting.report_generator import ReportGenerator
from reporting.logger import setup_logger
from config import Config
import asyncio

# Load configuration and set up logging (same as before)
config = Config()
logger = setup_logger(config.log_file_path)
logger.info("Starting Gradio application...")


def purge(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
            file_path = os.path.join(dir, f)
            print(f"Deleting: {file_path}")  # Debugging statement
            os.remove(file_path)

# --- Helper Functions (for Gradio) ---

async def ingest_data(file_obj, method="file_upload"):
    """Ingests data from a file upload or SFTP."""
    try:
        if method == "file_upload":
            if file_obj is None:
                raise ValueError("Please upload a file.")
            # Gradio File objects have a .name attribute which is the path to the temp file
            file_type = file_obj.name.split('.')[-1].lower()
            with open(file_obj.name, 'rb') as f:
                file_content = f.read()
            ingestor = FileUploadIngestor()
            raw_data_df = ingestor.ingest_data(file_content, file_type)

        elif method == "sftp":
            ingestor = SFTPIngestor(config.sftp_host, config.sftp_port, config.sftp_username,
                                     config.sftp_password, config.sftp_private_key_path,
                                     config.sftp_private_key_passphrase)
            raw_data_df = ingestor.fetch_data(config.sftp_remote_file, config.sftp_file_type)

        else:
            raise ValueError("Invalid ingestion method selected.")

        if raw_data_df is None or raw_data_df.empty:
            raise ValueError("Failed to ingest data or data is empty.")

        logger.info("Data ingested successfully.")
        return raw_data_df, "Data ingested successfully."

    except Exception as e:
        logger.error(f"Data ingestion error: {e}")
        return None, str(e)

async def preprocess_data(raw_data_df):
    """Cleans and categorizes the ingested data."""
    if raw_data_df is None or raw_data_df.empty:
        return None, "No data to preprocess. Please ingest data first."
    try:
        cleaner = DataCleaner()
        cleaned_df = cleaner.clean_data(raw_data_df, date_columns=config.date_columns)

        categorizer = Categorizer()
        not_found_df = categorizer.categorize_data(cleaned_df, config.system_b_column, config.not_found_value)
        not_found_df = not_found_df[['txn_ref_id', 'sys_a_amount_attribute_1', 'sys_a_date']]  # Keep only required columns
        not_found_df = not_found_df.rename(columns={'txn_ref_id': 'Transaction ID', 'sys_a_amount_attribute_1': 'Amount', 'sys_a_date': 'Date'})
        categorizer.export_to_csv(not_found_df, os.path.join(config.local_temp_dir, "temp_categorized_data.csv"), config.csv_export_columns)
        logger.info("Data preprocessed successfully.")
        return not_found_df, "Data preprocessed successfully."

    except Exception as e:
        logger.error(f"Data preprocessing error: {e}")
        return None, str(e)

async def upload_to_gcs(df, progress=gr.Progress()):
    """Uploads the categorized data to GCS."""
    if df is None or df.empty:
        return "No data to upload. Please preprocess data first."
    try:
        progress(0.5, desc="Starting Upload")
        storage = CloudStorage(config.gcs_bucket_name, config.gcs_credentials_path, config.gcs_project_id)
        local_file_path = os.path.join(config.local_temp_dir, "temp_categorized_data.csv")
        df.to_csv(local_file_path, index=False)

        storage.upload_file(local_file_path, config.gcs_categorized_file_path)
        os.remove(local_file_path)
        progress(1, desc="Finishing Upload")
        logger.info("Data uploaded to GCS successfully.")
        return "Data uploaded to GCS successfully."

    except Exception as e:
        logger.error(f"GCS upload error: {e}")
        return str(e)

async def ingest_comments(comments_file):
  """Ingest the comments file"""
  try:
    if comments_file is None:
      raise ValueError("Please upload a file")
    file_type = comments_file.name.split(".")[-1].lower()
    with open(comments_file.name, 'rb') as f:
      file_content = f.read()
    ingestor = FileUploadIngestor()
    comments_df = ingestor.ingest_data(file_content, file_type)

    if comments_df is None or comments_df.empty:
      raise ValueError("Failed to ingest data or the file is empty")

    if 'Transaction ID' not in comments_df.columns or 'Comments' not in comments_df.columns:
      raise ValueError("Comments DataFrame must contain 'Transaction ID' and 'Comments' columns.")

    logger.info("Comments Data Ingested successfully")
    print(comments_df.head())
    return comments_df, "Comments Data Ingested Successfully"
  except Exception as e:
    logger.error(f"Data Ingestion Error: {e}")
    return None, str(e)

async def handle_resolution(processed_df, comments_df, progress=gr.Progress()):
    """Handles the resolution logic using LLM and performs actions."""
    if comments_df is None or comments_df.empty:
        return None, None, "No comments data available."

    try:
        progress(0, desc="Starting Resolution")
        classifier = LLMClassifier(config.openai_api_key, config.openai_model_name)

        storage = CloudStorage(config.gcs_bucket_name, config.gcs_credentials_path, config.gcs_project_id)
        actions = ResolutionActions(storage, progress, config.model_path)
        processed_data = []

        total_comments = len(comments_df)
        print('Total comments to process:', total_comments)
        for index, row in comments_df.iterrows():
          progress(index / total_comments, desc=f"Processing Resolution: {index + 1} / {total_comments}")
          order_id = row['Transaction ID']
          comment = row['Comments']
          classification = await asyncio.to_thread(classifier.classify_comment, order_id, comment) # Run in a separate thread
          if classification:
            await asyncio.to_thread(actions.handle_resolution, order_id, classification, comment,
                                     config.gcs_resolved_folder, config.gcs_unresolved_folder, config.local_temp_dir)
            processed_data.append({'order_id': order_id, 'comment': comment, 'status': classification})

        processed_data_df = pd.DataFrame(processed_data)

        # --- Pattern Identification ---
        resolved_comments_df = processed_data_df[processed_data_df['status'] == 'Resolved'].copy()
        pattern_analysis_results = actions.identify_patterns(resolved_comments_df, n_clusters=config.num_clusters)

        purge(config.local_temp_dir, r".*_(resolved|unresolved)\.txt$")

        logger.info("Resolution handling complete.")
        progress(1, desc="Finishing Resolution")
        return processed_data_df, pattern_analysis_results, "Resolution handling complete."

    except Exception as e:
        logger.error(f"Resolution handling error: {e}")
        return None, None, str(e)

async def generate_reports(processed_data_df, pattern_analysis_results):
    """Generates summary report and visualizations."""
    if processed_data_df is None or processed_data_df.empty:
        return None, None, "No processed data available for reporting."

    try:
        report_generator = ReportGenerator(config.local_temp_dir)
        # Summary Report
        summary_report_path = os.path.join(config.local_temp_dir, "summary_report.csv")
        report_generator.generate_summary_report(processed_data_df, filename="summary_report.csv")

        # Visualization
        report_generator.generate_visualization(processed_data_df, "status", "order_id", "bar", filename="visualization.png")
        visualization_path = os.path.join(config.local_temp_dir, "visualization.png") # Provide full path

        # Pattern Analysis Report
        if pattern_analysis_results is not None and not pattern_analysis_results.empty:
            report_generator.generate_pattern_report(pattern_analysis_results, filename="pattern_report.txt")
            pattern_report_path = os.path.join(config.local_temp_dir, "pattern_report.txt") # Provide the full path
        else:
          pattern_report_path = None


        logger.info("Reports generated.")
        return summary_report_path, visualization_path, pattern_report_path, "Reports generated."

    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return None, None, None, str(e)


# --- Gradio Interface ---

with gr.Blocks() as demo:
    gr.Markdown("# Financial Discrepancy Resolution Agent")

    with gr.Tab("Ingest Data"):
        with gr.Row():
            data_file_input = gr.File(label="Upload Data File (CSV/Excel)")
            sftp_radio = gr.Radio(["file_upload", "sftp"], label="Data Source", value="file_upload")
        ingest_button = gr.Button("Ingest Data")
        raw_data_output = gr.Dataframe(label="Raw Data")
        ingest_status = gr.Textbox(label="Ingestion Status")

    with gr.Tab("Preprocess Data"):
        preprocess_button = gr.Button("Preprocess Data")
        processed_data_output = gr.Dataframe(label="Preprocessed Data (Not Found Sys B)")
        preprocess_status = gr.Textbox(label="Preprocessing Status")

    with gr.Tab("Upload to GCS"):
        upload_button = gr.Button("Upload to GCS")
        upload_status = gr.Textbox(label="Upload Status")

    with gr.Tab("Resolution Handling"):
      with gr.Row():
        comments_file_input = gr.File(label="Upload comments Data file (CSV/Excel)")
        comments_ingest_button = gr.Button("Ingest Comments")
      comments_data_output = gr.Dataframe(label="Comments Data")
      comment_ingest_status = gr.Textbox(label="Comment Ingestion Status")
      resolution_button = gr.Button("Handle Resolution")
      resolution_output = gr.Dataframe(label="Resolution Results")
      pattern_output = gr.Dataframe(label="Pattern Analysis")
      resolution_status = gr.Textbox(label="Resolution Status")

    with gr.Tab("Reports"):
        report_button = gr.Button("Generate Reports")
        summary_report_output = gr.File(label="Summary Report (CSV)")
        visualization_output = gr.Image(label="Visualization")
        pattern_report_output = gr.File(label="Pattern Report")
        report_status = gr.Textbox(label="Report Status")


    # State variables to store data across tabs
    raw_data_state = gr.State()
    processed_data_state = gr.State()
    comments_data_state = gr.State()

    # Event Handlers
    ingest_button.click(ingest_data, [data_file_input, sftp_radio], [raw_data_state, ingest_status])
    ingest_button.click(lambda df: gr.Dataframe(value=df), raw_data_state, raw_data_output)  # Update the visible Dataframe

    preprocess_button.click(preprocess_data, raw_data_state, [processed_data_state, preprocess_status])
    preprocess_button.click(lambda df: gr.Dataframe(value=df), processed_data_state, processed_data_output)

    upload_button.click(upload_to_gcs, processed_data_state, upload_status)

    comments_ingest_button.click(ingest_comments, comments_file_input, [comments_data_state, comment_ingest_status])
    comments_ingest_button.click(lambda df: gr.Dataframe(value=df), comments_data_state, comments_data_output)


    resolution_button.click(handle_resolution, [processed_data_state, comments_data_state], [resolution_output, pattern_output, resolution_status])
    report_button.click(generate_reports, [resolution_output, pattern_output], [summary_report_output, visualization_output, pattern_report_output, report_status])



if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=8080) 