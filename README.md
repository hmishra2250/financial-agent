# Financial Discrepancy Processing and Resolution Framework

This project implements an agentic framework to process financial discrepancies, categorize data, automate resolutions using a Large Language Model (LLM), and store results in Google Cloud Storage (GCS).  It is designed for scalability, maintainability, and security. 

- Watch a demo of the project here: [https://drive.google.com/file/d/1PYRkHI3DIi8RELYNhjmgEDDzaTQ8bMX5/view?usp=sharing](https://drive.google.com/file/d/1PYRkHI3DIi8RELYNhjmgEDDzaTQ8bMX5/view?usp=sharing)
- Linked to the demo webapp here: [https://financial-agent-app-891407508879.asia-southeast1.run.app/](https://financial-agent-app-891407508879.asia-southeast1.run.app/)

## Table of Contents

1.  [Problem Analysis & Requirements Gathering](#1-problem-analysis--requirements-gathering)
2.  [Modular Design](#2-modular-design)
    *   [Module 1: Data Ingestion](#module-1-data-ingestion)
    *   [Module 2: Preprocessing & Categorization](#module-2-preprocessing--categorization)
    *   [Module 3: File Upload/Email Service](#module-3-file-uploademail-service)
    *   [Module 4: Resolution Handler (LLM Integration)](#module-4-resolution-handler-llm-integration)
    *   [Module 5: Reporting & Analytics](#module-5-reporting--analytics)
3.  [Integration into a Full-Fledged Solution](#3-integration-into-a-full-fledged-solution)
    *   [Workflow Pipeline](#workflow-pipeline)
    *   [Deployment](#deployment)
    *   [Security & Compliance](#security--compliance)
    *   [Testing Strategy](#testing-strategy)
4.  [Final Solution Architecture](#4-final-solution-architecture)
5.  [Tech Stack](#tech-stack)
6.  [Deliverables](#5-deliverables)
7.  [Setup and Usage](#setup-and-usage)
    *   [Prerequisites](#prerequisites)
    *    [Installation](#installation)
    *   [Configuration](#configuration)
    *   [Running the Application](#running-the-application)
    *  [Testing](#testing)

## 1. Problem Analysis & Requirements Gathering

*   **Objective**: Build an agentic framework to process financial discrepancies, categorize data, and automate resolutions.
*   **Key Requirements**:
    *   Preprocess data, focusing on "Not Found Sys B" records, and generate a CSV file.
    *   Upload categorized data to Google Cloud Storage.  *(Email functionality not implemented)*
    *   Process resolution comments using an LLM, handling four distinct use cases.
    *   Deploy on a cloud platform (specifically Google Cloud Platform) with scalability.

## 2. Modular Design

### Module 1: Data Ingestion

*   **Purpose**: Fetch data from various sources.  *(Manual Upload is tried and tested properly. SFTP and API are implemented but aren't tested thoroughly)*
*   **Best Practices**:
    *   Error handling for connection issues and invalid credentials.
    *   Validation of file formats (CSV, with potential future extension to Excel/JSON).

### Module 2: Preprocessing & Categorization

*   **Purpose**: Clean the ingested data, handle missing values, and categorize records based on specific criteria.
*   **Steps**:
    1.  Load data using `pandas`.
    2.  Filter for records identified as "Not Found Sys B".
    3.  Export a CSV file containing `order_id`, `amount`, and `date` columns.
*   **Best Practices**:
    *   Log any missing or invalid entries for auditing purposes.
    *   Utilize `pandas` vectorized operations for efficient processing.

### Module 3: File Upload/Email Service

*   **Purpose**: Upload the categorized CSV file to Google Cloud Storage. *(Email sending functionality is NOT implemented.)*
*   **Tools**:
    *   **Cloud**: `google-cloud-storage` (Google Cloud Storage)
*   **Best Practices**:
    *   Use environment variables (loaded via `python-dotenv`) to store sensitive credentials (GCS bucket name, project ID, optional service account key path).
    *   Implement robust error handling and retries for failed upload attempts.

### Module 4: Resolution Handler (LLM Integration)

*   **Purpose**: Process comments associated with discrepancies to determine the resolution status and trigger appropriate actions.
*   **Steps**:
    1.  Utilize an LLM (OpenAI GPT-3.5 Turbo or GPT-4) to classify comments:
        *   **Prompt Example**:

            ```python
            prompt = f"""
            Classify the resolution status for Order ID {order_id} from this comment: "{comment}".
            Options: [Resolved, Unresolved].
            Respond ONLY with one word: Resolved or Unresolved.
            """
            ```
    2.  Handle the following use cases:
        *   **Resolved**: Upload the record to a designated "resolved" folder in GCS.
        *   **Unresolved**: Generate a summary and suggest next steps (future implementation).
        *   **Pattern Identification**: Cluster resolved cases (e.g., using `scikit-learn`) to identify patterns for potential automation of future resolutions (future implementation).
*   **Tools**:
    *   `openai` API for interacting with OpenAI models.
    *   `langchain` (potential future use for more sophisticated prompt engineering).
*   **Best Practices**:
    *   Cache LLM responses (consider using a caching library) to reduce costs and API calls.
    *   Implement validation checks on LLM outputs using regular expressions or rule-based systems to ensure accuracy.

### Module 5: Reporting & Analytics

*   **Purpose**: Generate summaries, logs, and (in the future) pattern reports to provide insights into the discrepancy resolution process.
*   **Tools**:
    *   `logging` for creating detailed audit trails.
    *   `matplotlib`/`seaborn` (for future visualization of trends and patterns).
*  **Best Practices**:
    *  Configure log levels appropriately (e.g. DEBUG, INFO, ERROR).

## 3. Integration into a Full-Fledged Solution

### Workflow Pipeline

1.  **Trigger**: Currently, the process is manually triggered.  (Future: trigger on new file detection in a GCS bucket or via an API call).
2.  **Preprocessing**:
    *   Clean the ingested data.
    *   Categorize records based on "Not Found Sys B" status.
    *   Export the relevant data to a CSV file.
3.  **Upload**: Upload the generated CSV file to the `processed/not_found_sys_b` folder in the designated GCS bucket.
4.  **Resolution Handling**:
    *   Fetch the associated comments dataset.
    *   Use the LLM to classify each comment as "Resolved" or "Unresolved."
    *   Execute the corresponding actions based on the classification:
        *   Upload resolved cases to the `processed/resolved` folder in GCS.
        *   Generate summaries and next steps for unresolved cases (future implementation).
5.  **Pattern Analysis**: Cluster resolved cases using all-MiniLM-L6-v2 model embeddings to identify patterns and automate the closure of similar cases in the future.

### Deployment

*   **Cloud Integration**: Designed for deployment on Google Cloud Platform (GCP).  Consider using:
    *   Cloud Functions for serverless execution.
    *   Cloud Run for containerized deployments.
    *   Compute Engine for more control over the environment.
*   **Scalability**:
    *   Parallelize data processing using tools like Cloud Dataflow (future implementation).
    *  Consider using Pub/Sub for task distribution.

### Security & Compliance

*   **Data Encryption**: Ensure data is encrypted at rest within GCS using server-side encryption (default) or customer-managed encryption keys (CMEK).
*   **Access Control**: Use IAM roles to implement the principle of least privilege, granting only necessary permissions to service accounts and users.
* **.env file**: Use the .env file to securely store sensitive information. *Never* commit the .env file to github.

### Testing Strategy

*   **Unit Tests**: Validate the functionality of individual modules (e.g., using `pytest` for the preprocessing and GCS interaction modules).
*   **Integration Tests**: Test the end-to-end pipeline using synthetic data to ensure all components work together correctly.
*   **Edge Cases**: Include tests for edge cases, such as empty files, invalid comments, and potential network or API failures.

## 4. Final Solution Architecture

```
┌──────────────────┐       ┌─────────────────────┐       ┌────────────────────────┐
│   Data Ingestion │──────▶│ Preprocessing &     │──────▶│ File Upload (GCS)      │
│      (SFTP)      │       │ Categorization      │       │                        │
└──────────────────┘       └─────────────────────┘       └─────────┬──────────────┘
                                                                   │
                                                                   ▼
┌──────────────────┐       ┌─────────────────────┐       ┌─────────┴──────────────┐
│Resolution Handler│◀──────│  Comments Dataset   │──────▶│ Reporting & Analytics │
│   (LLM + Logic)  │       │                     │       │                        │
└──────────────────┘       └─────────────────────┘       └────────────────────────┘
```

## 5. Tech Stack

*   **Language**: Python 3.10+
*   **Libraries**: `pandas`, `openai`, `google-cloud-storage`, `paramiko`, `python-dotenv`
*   **Cloud**: Google Cloud Platform (GCS, potentially Cloud Functions/Cloud Run/Compute Engine)
*   **DevOps**:  Docker (Future: GitHub Actions/Cloud Build)

## 6. Setup and Usage

### Prerequisites

*   **Google Cloud Account**: You need a Google Cloud Platform (GCP) account with billing enabled.
*   **GCS Bucket**: Create a GCS bucket to store the processed data.
*   **Service Account (Recommended)**:
    *   Create a service account in the IAM & Admin section of the GCP console.
    *   Grant this service account the "Storage Object Admin" role (or a custom role with equivalent permissions) on your GCS bucket.
    *   Download the service account key file (JSON format) and keep it secure.
* **SFTP Server:** Ensure SFTP Server is setup with credentials for access.
*   **OpenAI API Key**: Obtain an API key from OpenAI ([https://platform.openai.com/](https://platform.openai.com/)).
*   **Python 3.10+**: Install Python 3.10 or a later version.
*   **pip**: Ensure you have `pip`, the Python package installer.

### Running and Deploying using Docker

This section describes how to build, push, and deploy the application using Docker and Google Cloud Run.

**Prerequisites:**

*   [Docker](https://www.docker.com/get-started) installed and running on your system.
*   [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured.
    *   Make sure you are authenticated: `gcloud auth login`
    *   Set your project: `gcloud config set project YOUR_PROJECT_ID` (Replace `YOUR_PROJECT_ID` with your actual project ID.)
*   Access to the Artifact Registry repository (`asia-southeast1-docker.pkg.dev/coral-sanctuary-450107-b3/financial-agent-images`).
* Ensure you are in the same directory with Dockerfile.

**Steps:**

1.  **Build the Docker Image:**

    This command builds a Docker image from your application's source code using the `Dockerfile` in the current directory (`.`).  The image is tagged with the provided repository path and the `latest` tag.

    ```bash
    docker build -t asia-southeast1-docker.pkg.dev/coral-sanctuary-450107-b3/financial-agent-images/finagent-app:latest .
    ```
     *  `-t`:  Tags the image.  The format is `[REGION]-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME]:[TAG]`.
     *  `.`:  Specifies the build context (the current directory).

2.  **Push the Docker Image to Artifact Registry:**

    This command pushes the locally built Docker image to your Google Cloud Artifact Registry repository. This makes the image available for deployment to Cloud Run.

    ```bash
    docker push asia-southeast1-docker.pkg.dev/coral-sanctuary-450107-b3/financial-agent-images/finagent-app:latest
    ```

3.  **Deploy to Google Cloud Run:**

    This command deploys the image from Artifact Registry to Google Cloud Run.

    ```bash
    gcloud run deploy financial-agent-app \
      --image asia-southeast1-docker.pkg.dev/coral-sanctuary-450107-b3/financial-agent-images/finagent-app:latest \
      --platform managed \
      --region asia-southeast1 \
      --allow-unauthenticated \
      --memory=1Gi \
      --timeout 300
    ```

    *   `financial-agent-app`:  The name of your Cloud Run service.
    *   `--image`:  Specifies the image to deploy (from Artifact Registry).
    *   `--platform managed`:  Deploys to the fully managed Cloud Run environment.
    *   `--region asia-southeast1`:  Specifies the region for deployment.
    *   `--allow-unauthenticated`:  Allows unauthenticated access to the service (for public-facing services).  **Important:** Consider carefully whether your service should allow unauthenticated access.  If it should be private, remove this flag.
    *   `--memory=1Gi`:  Sets the memory limit for the service instances.
    *   `--timeout 300`: Sets the request timeout to 300 seconds (5 minutes).


### Running as python app locally

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/hmishra2250/financial-agent.git
    cd financial-agent
    ```

2.  **Create a Virtual Environment (Recommended)**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  
    ```

3.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```
    (Make sure `requirements.txt` contains `pandas`, `openai`, `google-cloud-storage`, `paramiko`, `python-dotenv`)

### Configuration

1.  **Create a `.env` file**:  Create a file named `.env` in the root directory of your project.

2.  **Populate `.env`**: Add the following environment variables to your `.env` file, replacing the placeholder values with your actual credentials:

    ```dotenv
    # --- Data Ingestion (SFTP) ---
    INGESTION_METHOD=sftp
    SFTP_HOST=your_sftp_host
    SFTP_PORT=22
    SFTP_USERNAME=your_sftp_username
    SFTP_PASSWORD=your_sftp_password
    SFTP_PRIVATE_KEY_PATH=  # Optional
    SFTP_PRIVATE_KEY_PASSPHRASE=  # Optional
    SFTP_REMOTE_FILE=path/to/your/remote/file.csv
    SFTP_FILE_TYPE=csv
    SFTP_COMMENTS_FILE=path/to/your/remote/comments.csv
    SFTP_COMMENTS_FILE_TYPE=csv

    # --- Preprocessing ---
    SYSTEM_B_COLUMN=recon_sub_status
    NOT_FOUND_VALUE="Not Found-SysB"

    # --- Google Cloud Storage (GCS) ---
    GCS_BUCKET_NAME=your-gcs-bucket-name
    GCS_PROJECT_ID=your-gcp-project-id
    GCS_CREDENTIALS_PATH=  # Optional: path/to/your/service_account_key.json
    GCS_CATEGORIZED_FILE_PATH=processed/not_found_sys_b/categorized_data.csv
    GCS_RESOLVED_FOLDER=processed/resolved
    GCS_UNRESOLVED_FOLDER=processed/unresolved
    LOCAL_TEMP_DIR=temp

    # --- Resolution Handler (OpenAI) ---
    OPENAI_API_KEY=your_openai_api_key
    OPENAI_MODEL_NAME=gpt-3.5-turbo
    NUM_CLUSTERS=3

    # --- Reporting ---
    LOG_FILE_PATH=logs/app.log
    ```

    *   **Important**: If you're *not* using a service account key file, you can leave `GCS_CREDENTIALS_PATH` blank.  In this case, the application will attempt to use Application Default Credentials (ADC). Make sure your environment is set up for ADC (e.g., you've run `gcloud auth application-default login`).

3. **Directory structure** Create the directories referred to in the `.env` file. For instance, create `logs` folder in the root directory.

### Running the Application
Run the main script (replace with your actual script name):

```bash
python main.py
```
### Testing (Not completely adapted to the latest code)
Run the test (assuming you are using `pytest`):

```bash
pytest
```