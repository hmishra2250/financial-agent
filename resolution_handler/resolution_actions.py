# resolution_handler/resolution_actions.py
import logging
import os
from sklearn.cluster import KMeans  # For pattern identification
import pandas as pd
from sentence_transformers import SentenceTransformer
class ResolutionActions:
    """
    Handles actions based on the LLM classification.
    """

    def __init__(self, cloud_storage, progress, model_path='all-MiniLM-L6-v2'):
        """
        Initializes with a CloudStorage instance for file handling.

        Args:
            cloud_storage (CloudStorage): Instance for managing files.
        """
        self.cloud_storage = cloud_storage
        self.progress = progress
        self.model = SentenceTransformer(model_path, device='cpu')

    def handle_resolution(self, order_id, classification, comment, resolved_folder, unresolved_folder, local_temp_dir):
        """
        Performs actions based on the classification.

        Args:
            order_id (str): The order ID.
            classification (str): "Resolved" or "Unresolved".
            comment (str): The resolution comment.
            resolved_folder (str): S3 folder for resolved cases.
            unresolved_folder (str): S3 folder for unresolved cases.
            local_temp_dir (str): local temp directory

        Returns:
            None
        """

        if classification == "Resolved":
            # Move to resolved folder
            file_name = f"{order_id}_resolved.txt"
            local_file_path = os.path.join(local_temp_dir, file_name)
            s3_file_path = os.path.join(resolved_folder, file_name)

            # Create a simple text file with the order ID and comment
            with open(local_file_path, "w") as f:
                f.write(f"Order ID: {order_id}\nComment: {comment}\nStatus: Resolved")
            self.progress(0.5, desc="Starting Upload")
            self.cloud_storage.upload_file(local_file_path, s3_file_path)
            self.progress(1, desc="Finishing Upload")
            
        elif classification == "Unresolved":
          # Generate summary and next steps
          file_name = f"{order_id}_unresolved.txt"
          local_file_path = os.path.join(local_temp_dir, file_name)
          s3_file_path = os.path.join(unresolved_folder, file_name)
          summary = self.generate_unresolved_summary(order_id, comment)
          with open(local_file_path, "w") as f:
              f.write(summary)
          self.progress(0.5, desc="Starting Upload")
          self.cloud_storage.upload_file(local_file_path, s3_file_path)
          self.progress(1, desc="Finishing Upload")
          

        else:
            logging.error(f"Invalid classification: {classification} for order {order_id}")

    def generate_unresolved_summary(self, order_id, comment):
        """
        Generates a summary for unresolved cases.

        Args:
            order_id: Order Id
            comment: comments

        Returns:
            str: A summary string.
        """
        # Basic summary;  You could use the LLM here for a more sophisticated summary.
        summary = f"Order ID: {order_id}\nComment: {comment}\nStatus: Unresolved\nNext Steps: Manual review required."
        return summary
    

    def identify_patterns(self, resolved_comments_df, n_clusters=3):
        """
        Identify patterns in resolved comments using BERT embeddings and K-Means clustering.

        Args:
            resolved_comments_df (pd.DataFrame): DataFrame with 'order_id' and 'comment'
            n_clusters (int): The number of clusters to form.

        Returns:
            pd.DataFrame: Original data with cluster assignments.
        """
        if resolved_comments_df.empty:
            logging.warning("No resolved comments to analyze.")
            return pd.DataFrame()

        # Drop rows with missing comments
        resolved_comments_df = resolved_comments_df.dropna(subset=['comment'])

        if resolved_comments_df.empty:
            logging.warning("No resolved comments to analyze after dropping missing values")
            return pd.DataFrame()

        # Generate sentence embeddings using BERT
        comments = resolved_comments_df['comment'].tolist()
        embeddings = self.model.encode(comments, convert_to_numpy=True)

        # Perform K-Means clustering on embeddings
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(embeddings)

        # Assign clusters to DataFrame
        resolved_comments_df['cluster'] = clusters
        return resolved_comments_df
