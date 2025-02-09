# data_ingestion/api_ingestor.py
import requests
import pandas as pd
import logging
import json

class APIIngestor:
    """
    Fetches data from a REST API.
    """

    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    def fetch_data(self, endpoint, params=None):
        """
        Fetches data from a specific API endpoint.

        Args:
            endpoint (str): The API endpoint (e.g., '/transactions').
            params (dict, optional): Query parameters for the API request.

        Returns:
            pandas.DataFrame: The data loaded into a DataFrame.
            None: If there is an error or the response is not valid JSON.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            try:
                data = response.json()
                # Handle different JSON structures (list of dicts, nested data, etc.)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    # Example: If the data is nested under a key like 'results'
                    if 'results' in data and isinstance(data['results'], list):
                        df = pd.DataFrame(data['results'])
                    else:
                        df = pd.DataFrame([data])  # Convert single dict to DataFrame
                else:
                    logging.error(f"Unexpected JSON structure: {data}")
                    return None
                return df
            except json.JSONDecodeError:
                logging.error(f"Failed to decode JSON from response: {response.text}")
                return None


        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from API: {e}")
            return None