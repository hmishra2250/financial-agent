# reporting/report_generator.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os
from typing import Optional

class ReportGenerator:
    """
    Generates reports and visualizations for the financial discrepancy analysis.
    """

    def __init__(self, output_dir: str = "reports"):
        """
        Initializes the ReportGenerator.

        Args:
            output_dir (str): The directory where reports and visualizations will be saved.
                Defaults to "reports".  Creates the directory if it doesn't exist.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)  # Ensure the directory exists
        self.logger = logging.getLogger(__name__)  # Use the module's name for logging


    def generate_summary_report(self, processed_data_df: pd.DataFrame, filename: str = "summary_report.csv",
                                 custom_aggregations: Optional[dict] = None) -> None:
        """
        Generates a summary report of processed data, saved as a CSV file.

        Args:
            processed_data_df (pd.DataFrame): DataFrame with processed data.
            filename (str):  Name of the output CSV file (within the output directory).
                Defaults to "summary_report.csv".
            custom_aggregations (Optional[dict]): A dictionary specifying custom aggregations
                to perform.  Keys are column names, and values are aggregation functions
                (e.g., 'mean', 'sum', 'count', a custom function, or a list of functions).
                Example:  {'amount': ['sum', 'mean'], 'order_id': 'count'}

        Returns:
            None
        """
        if processed_data_df is None or processed_data_df.empty:
            self.logger.warning("No processed data to generate a report.")
            return

        output_path = os.path.join(self.output_dir, filename)

        try:
            # Default aggregation: Count of resolved vs. unresolved cases
            report_df = processed_data_df['status'].value_counts().reset_index()
            report_df.columns = ['status', 'count']

            # Apply custom aggregations if provided
            if custom_aggregations:
                agg_df = processed_data_df.groupby('status').agg(custom_aggregations)
                # Flatten MultiIndex columns (if multiple aggregations are used)
                agg_df.columns = ['_'.join(col).strip() for col in agg_df.columns.values]
                agg_df = agg_df.reset_index()
                report_df = pd.merge(report_df, agg_df, on='status', how='left')

            report_df.to_csv(output_path, index=False)
            self.logger.info(f"Summary report saved to {output_path}")

        except Exception as e:
            self.logger.exception(f"Error saving summary report: {e}")


    def generate_visualization(self, data: pd.DataFrame, x_column: str, y_column: Optional[str] = None,
                                plot_type: str = "bar", filename: str = "visualization.png",
                                hue_column: Optional[str] = None, title: Optional[str] = None,
                                xlabel: Optional[str] = None, ylabel: Optional[str] = None,
                                **kwargs) -> None:
        """
        Generates various visualizations and saves them as image files.

        Args:
            data (pd.DataFrame): Input DataFrame.
            x_column (str): Column name for the x-axis.
            y_column (Optional[str]): Column name for the y-axis. Required for most plot types
                except 'hist' and 'kde'.
            plot_type (str): Type of plot.  Supported types: 'bar', 'line', 'scatter', 'hist',
                'kde', 'box', 'violin', 'heatmap'.  Case-insensitive.
            filename (str): Name of the output image file (within the output directory).
                Defaults to "visualization.png".
            hue_column (Optional[str]):  Column name for color encoding (hue).
            title (Optional[str]):  Custom plot title.
            xlabel (Optional[str]): Custom x-axis label.
            ylabel (Optional[str]): Custom y-axis label.
            **kwargs:  Additional keyword arguments passed to the underlying Seaborn plotting function.
                This allows for customization (e.g., setting `kde=True` for `histplot`).

        Returns:
            None
        """
        if data.empty:
            self.logger.warning("Data is empty. Cannot generate visualization.")
            return

        output_path = os.path.join(self.output_dir, filename)
        plt.figure(figsize=(10, 6))  # Adjust figure size as needed
        plot_type = plot_type.lower()

        try:
            if plot_type == "bar":
                if y_column is None:
                    raise ValueError("y_column must be specified for bar plots.")
                sns.barplot(x=x_column, y=y_column, data=data, hue=hue_column, **kwargs)
            elif plot_type == 'line':
                if y_column is None:
                    raise ValueError("y_column must be specified for line plots.")
                sns.lineplot(x=x_column, y=y_column, data=data, hue=hue_column, **kwargs)
            elif plot_type == 'scatter':
                if y_column is None:
                    raise ValueError("y_column must be specified for scatter plots.")
                sns.scatterplot(x=x_column, y=y_column, data=data, hue=hue_column, **kwargs)
            elif plot_type == "hist":
                sns.histplot(data=data, x=x_column, hue=hue_column, **kwargs)  # kde handled via kwargs
            elif plot_type == "kde":
                sns.kdeplot(data=data, x=x_column, hue=hue_column, **kwargs)
            elif plot_type == "box":
                if y_column is None:
                    sns.boxplot(x=x_column, data=data, hue=hue_column, **kwargs)
                else:
                    sns.boxplot(x=x_column, y=y_column, data=data, hue=hue_column, **kwargs)
            elif plot_type == "violin":
                if y_column is None:
                    sns.violinplot(x=x_column, data=data, hue=hue_column, **kwargs)
                else:
                    sns.violinplot(x=x_column, y=y_column, data=data, hue=hue_column, **kwargs)
            elif plot_type == "heatmap":
                # For heatmaps, we typically need a correlation matrix or a pivot table.
                if 'corr' in kwargs and kwargs['corr']:
                    corr_matrix = data.corr(numeric_only=True) # calculate the correlation matrix
                    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", **kwargs)
                else: # create a pivot table
                    if y_column is None:
                        raise ValueError("y_column and a valid aggregation method must be specified for heatmap (pivot table).")
                    # Check if an aggregation function is provided in kwargs
                    if 'aggfunc' not in kwargs:
                      raise ValueError("aggfunc must be specified within kwargs")
                    pivot_table = pd.pivot_table(data, values=y_column, index=x_column, columns=hue_column, aggfunc=kwargs['aggfunc'])
                    sns.heatmap(pivot_table, annot=True, cmap="viridis", **kwargs)
            else:
                raise ValueError(f"Invalid plot_type: {plot_type}")

            # Set title and labels (use provided values or defaults)
            plt.title(title or f"{plot_type.capitalize()} Plot of {y_column or x_column} vs. {x_column}")
            plt.xlabel(xlabel or x_column)
            plt.ylabel(ylabel or y_column)
            plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
            plt.tight_layout()  # Adjust layout to prevent labels from overlapping
            plt.savefig(output_path)
            plt.close()  # Close the figure to free memory
            self.logger.info(f"Visualization saved to {output_path}")

        except ValueError as ve:
            self.logger.error(str(ve))
        except Exception as e:
            self.logger.exception(f"Error generating visualization: {e}")


    def generate_pattern_report(self, clustered_data: pd.DataFrame, filename: str = "pattern_report.txt") -> None:
        """
        Generates a report summarizing the identified patterns (clusters) in the data.

        Args:
            clustered_data (pd.DataFrame): DataFrame with cluster assignments (from ResolutionActions).
            filename (str): Name of the output text file (within the output directory).
                Defaults to "pattern_report.txt".

        Returns:
            None
        """
        if clustered_data is None or clustered_data.empty:
            self.logger.warning("No clustered data to generate a pattern report.")
            return
        if 'cluster' not in clustered_data.columns:
            self.logger.warning("Clustered data does not contain a 'cluster' column.")
            return

        output_path = os.path.join(self.output_dir, filename)

        try:
            with open(output_path, 'w') as f:
                f.write("Pattern Analysis Report\n\n")
                for cluster_id in sorted(clustered_data['cluster'].unique()):
                    cluster_data = clustered_data[clustered_data['cluster'] == cluster_id]
                    f.write(f"Cluster {cluster_id}:\n")
                    f.write(f"  Number of records: {len(cluster_data)}\n")
                    # Example: Show average comment length (if available)
                    if 'comment_length' in cluster_data.columns:
                        avg_length = cluster_data['comment_length'].mean()
                        f.write(f"  Average comment length: {avg_length:.2f}\n")
                    # Example: Show some sample comments (first 3)
                    sample_comments = cluster_data['comment'].head(3).tolist()
                    f.write("  Sample comments:\n")
                    for comment in sample_comments:
                        f.write(f"    - {comment}\n")
                    f.write("\n")

            self.logger.info(f"Pattern report saved to {output_path}")

        except Exception as e:
            self.logger.exception(f"Error saving pattern report: {e}")