# resolution_handler/llm_classifier.py
from openai import OpenAI, RateLimitError, APIError, APIConnectionError  # Updated imports
import logging
import os
import re
import time

class LLMClassifier:
    """
    Classifies resolution comments using an LLM (OpenAI GPT).
    """

    def __init__(self, api_key, model_name="gpt-3.5-turbo"):
        """
        Initializes the LLM classifier.

        Args:
            api_key (str): Your OpenAI API key.
            model_name (str):  The OpenAI model to use.  Defaults to "gpt-3.5-turbo".
        """
        self.client = OpenAI(api_key=api_key)  # New client initialization
        self.model_name = model_name

    def classify_comment(self, order_id, comment, max_retries=3, retry_delay=5):
        """
        Classifies a comment as "Resolved" or "Unresolved".

        Args:
            order_id (str): The ID of the order.
            comment (str): The resolution comment.
            max_retries (int): Maximum number of retries if the API call fails.
            retry_delay (int): Delay in seconds between retries.

        Returns:
            str: "Resolved" or "Unresolved", or None if classification fails.
        """
        prompt = f"""
        Classify the resolution status for Order ID {order_id} from this comment: "{comment}".
        Options: [Resolved, Unresolved].
        Respond ONLY with one word: Resolved or Unresolved.
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(  # Updated API call
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=5,
                )
                classification = response.choices[0].message.content.strip()

                # Validate the LLM output using regex
                if re.match(r"^(Resolved|Unresolved)$", classification, re.IGNORECASE):
                    return classification.capitalize()
                else:
                    logging.warning(f"Invalid LLM response: {classification}. Retrying...")

            except RateLimitError:  # Direct exception reference
                logging.warning(f"Rate limit exceeded. Waiting {retry_delay} seconds before retrying...")
                time.sleep(retry_delay)
            except (APIConnectionError, APIError) as e:  # Combined network-related errors
                logging.warning(f"API connection issue: {e}. Waiting {retry_delay} seconds...")
                time.sleep(retry_delay)
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return None
        logging.error(f"Failed to classify comment after {max_retries} attempts.")
        return None