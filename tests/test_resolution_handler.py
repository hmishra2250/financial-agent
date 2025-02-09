# tests/test_resolution_handler.py

import pytest
from resolution_handler.llm_classifier import LLMClassifier
from resolution_handler.resolution_actions import ResolutionActions
from unittest.mock import patch, MagicMock
import openai
import os
import pandas as pd
from sklearn.cluster import KMeans

# --- Tests for LLMClassifier ---

@patch('openai.ChatCompletion.create')
def test_llm_classifier_classify_comment_success(mock_create):
    """Test successful comment classification."""
    mock_response = MagicMock()
    mock_response.choices[0].message = {'content': 'Resolved'}
    mock_create.return_value = mock_response

    classifier = LLMClassifier('test_api_key')
    classification = classifier.classify_comment('order123', 'Issue resolved.')
    assert classification == 'Resolved'
    mock_create.assert_called_once()


@patch('openai.ChatCompletion.create')
def test_llm_classifier_classify_comment_unresolved(mock_create):
    """Test classifying a comment as 'Unresolved'."""
    mock_response = MagicMock()
    mock_response.choices[0].message = {'content': 'Unresolved'}
    mock_create.return_value = mock_response

    classifier = LLMClassifier('test_api_key')
    classification = classifier.classify_comment('order456', 'Still pending.')
    assert classification == 'Unresolved'

@patch('openai.ChatCompletion.create')
def test_llm_classifier_classify_comment_invalid_response(mock_create):
    """Test handling an invalid LLM response (not 'Resolved' or 'Unresolved')."""
    mock_response = MagicMock()
    mock_response.choices[0].message = {'content': 'Invalid response'}
    mock_create.return_value = mock_response

    classifier = LLMClassifier('test_api_key')
    classification = classifier.classify_comment('order789', 'Some comment.')
    assert classification is None  # Should return None after retries

@patch('openai.ChatCompletion.create')
def test_llm_classifier_classify_comment_api_error(mock_create):
    """Test handling an OpenAI API error."""
    mock_create.side_effect = openai.error.APIError("Test API Error")

    classifier = LLMClassifier('test_api_key')
    classification = classifier.classify_comment('order123', 'Some comment.')
    assert classification is None  # Should return None after retries

@patch('openai.ChatCompletion.create')
def test_llm_classifier_classify_comment_rate_limit_error(mock_create):
    """Test handling rate limit error with retries."""
    mock_create.side_effect = [
        openai.error.RateLimitError("Rate limit exceeded"),
        openai.error.RateLimitError("Rate limit exceeded"),
        MagicMock(choices=[MagicMock(message={'content': 'Resolved'})])
    ]
    classifier = LLMClassifier("test_api_key")
    with patch("time.sleep", return_value=None):  # Mock time.sleep
      classification = classifier.classify_comment("order123", "Issue resolved.")
    assert classification == "Resolved"
    assert mock_create.call_count == 3

# --- Tests for ResolutionActions ---
@pytest.fixture
def mock_cloud_storage():
    """Fixture to provide a mocked CloudStorage instance."""
    return MagicMock()


def test_resolution_actions_handle_resolution_resolved(mock_cloud_storage, tmpdir):
    """Test handling a 'Resolved' classification."""
    actions = ResolutionActions(mock_cloud_storage)
    temp_dir = str(tmpdir)  # Use pytest's tmpdir fixture
    actions.handle_resolution('order123', 'Resolved', 'Issue fixed.', 'resolved_folder', 'unresolved_folder', temp_dir)

    # Assert that the correct upload method was called with the correct arguments.
    assert mock_cloud_storage.upload_file.called
    # Get the arguments that upload_file was called with
    upload_args, upload_kwargs = mock_cloud_storage.upload_file.call_args
    local_file_path, s3_file_path = upload_args # get the paths
    assert s3_file_path == os.path.join("resolved_folder", "order123_resolved.txt")
    assert "order123_resolved.txt" in local_file_path

    assert os.path.basename(local_file_path) == "order123_resolved.txt" # Check the file
    with open(local_file_path, "r") as f: # Check file content
        content = f.read()
    assert "Order ID: order123" in content
    assert "Comment: Issue fixed." in content
    assert "Status: Resolved" in content


def test_resolution_actions_handle_resolution_unresolved(mock_cloud_storage, tmpdir):
    """Test handling an 'Unresolved' classification."""
    actions = ResolutionActions(mock_cloud_storage)
    temp_dir = str(tmpdir)
    actions.handle_resolution('order456', 'Unresolved', 'Still an issue.', 'resolved_folder', 'unresolved_folder', temp_dir)
    assert mock_cloud_storage.upload_file.called

    upload_args, upload_kwargs = mock_cloud_storage.upload_file.call_args
    local_file_path, s3_file_path = upload_args  # get the paths
    assert s3_file_path == os.path.join("unresolved_folder", "order456_unresolved.txt")
    assert os.path.basename(local_file_path) == "order456_unresolved.txt" # check file
    with open(local_file_path, "r") as f: # check the content
        content = f.read()
    assert "Order ID: order456" in content
    assert "Comment: Still an issue." in content
    assert "Status: Unresolved" in content
    assert "Next Steps: Manual review required." in content

def test_resolution_actions_handle_resolution_invalid_classification(mock_cloud_storage, tmpdir):
    """Test handling an invalid classification."""
    actions = ResolutionActions(mock_cloud_storage)
    temp_dir = str(tmpdir)
    actions.handle_resolution('order789', 'Invalid', 'Some comment.', 'resolved', 'unresolved', temp_dir)

def test_resolution_actions_generate_unresolved_summary():
    """Test generating the summary for unresolved cases."""
    actions = ResolutionActions(MagicMock())
    summary = actions.generate_unresolved_summary('order123', 'Problem persists.')
    assert 'Order ID: order123' in summary
    assert 'Comment: Problem persists.' in summary
    assert 'Status: Unresolved' in summary
    assert 'Next Steps: Manual review required.' in summary

def test_resolution_actions_identify_patterns_success():
    """Test pattern identification (clustering)."""
    actions = ResolutionActions(MagicMock())
    data = {
        'order_id': ['order1', 'order2', 'order3', 'order4'],
        'comment': ['short', 'very long comment', 'short', 'another long one'],
        'comment_length': [5, 18, 5, 16]  # Pre-calculated lengths
    }
    df = pd.DataFrame(data)

    # Mock KMeans to control its behavior in a predictable way
    mock_kmeans = MagicMock(spec=KMeans)
    mock_kmeans.fit_predict.return_value = [0, 1, 0, 1] # Mocked cluster assignments

    # Use patch to replace KMeans with our mock
    with patch('resolution_handler.resolution_actions.KMeans', return_value=mock_kmeans):
      result_df = actions.identify_patterns(df.copy(), n_clusters=2)
      assert 'cluster' in result_df.columns
      assert list(result_df['cluster']) == [0, 1, 0, 1] # Check the mocked values
      mock_kmeans.fit_predict.assert_called()

def test_resolution_actions_identify_patterns_empty_dataframe():
    """Test pattern identification with an empty DataFrame."""
    actions = ResolutionActions(MagicMock())
    empty_df = pd.DataFrame()
    result_df = actions.identify_patterns(empty_df)
    assert result_df.empty

def test_resolution_actions_identify_patterns_no_resolved_comments(mock_cloud_storage):
  """Test identify patterns with no resolved comments"""
  actions = ResolutionActions(mock_cloud_storage)
  data = {"order_id": [], "comment": [], "comment_length": []}
  df = pd.DataFrame(data)
  result_df = actions.identify_patterns(df)

  assert result_df.empty

def test_resolution_actions_identify_pattern_missing_values():
    """Test identify patterns with missing values in comments"""
    actions = ResolutionActions(MagicMock())
    data = {
        "order_id": ["order1", "order2", "order3"],
        "comment": ["short comment", None, "long comment"],
        'comment_length': [10, None, 15]
    }
    df = pd.DataFrame(data)
    mock_kmeans = MagicMock(spec=KMeans)
    mock_kmeans.fit_predict.return_value = [0, 0]  # Mocked cluster assignments

    with patch('resolution_handler.resolution_actions.KMeans', return_value=mock_kmeans):
        result_df = actions.identify_patterns(df.copy(), n_clusters=2)
        assert result_df.shape[0] == 2 # One row should be dropped.
        assert 'cluster' in result_df.columns
        assert list(result_df['cluster']) == [0, 0]  # Check the mocked values
        mock_kmeans.fit_predict.assert_called()