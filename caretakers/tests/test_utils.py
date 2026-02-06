"""
Tests for caretaker utilities

Tests helper functions for caretaker operations.
"""
import pytest
from unittest.mock import Mock, patch

from caretakers.models import Caretaker
from caretakers.utils.helpers import (
    get_all_caretaker_assignments,
    deduplicate_documents,
)
from common.tests.factories import UserFactory


class TestGetAllCaretakerAssignments:
    """Tests for get_all_caretaker_assignments function"""

    @pytest.mark.django_db
    @patch('caretakers.services.task_service.CaretakerTaskService.get_all_caretaker_assignments')
    def test_delegates_to_service(self, mock_service_method):
        """Test function delegates to CaretakerTaskService"""
        # Arrange
        user_id = 123
        mock_service_method.return_value = []
        
        # Act
        result = get_all_caretaker_assignments(user_id)
        
        # Assert
        mock_service_method.assert_called_once_with(123, None)
        assert result == []

    @pytest.mark.django_db
    @patch('caretakers.services.task_service.CaretakerTaskService.get_all_caretaker_assignments')
    def test_passes_processed_users(self, mock_service_method):
        """Test function passes processed_users to service"""
        # Arrange
        user_id = 123
        processed_users = {1, 2, 3}
        mock_service_method.return_value = []
        
        # Act
        result = get_all_caretaker_assignments(user_id, processed_users)
        
        # Assert
        mock_service_method.assert_called_once_with(123, processed_users)
        assert result == []

    @pytest.mark.django_db
    @patch('caretakers.services.task_service.CaretakerTaskService.get_all_caretaker_assignments')
    def test_returns_service_result(self, mock_service_method):
        """Test function returns result from service"""
        # Arrange
        user_id = 123
        expected_result = [Mock(), Mock()]
        mock_service_method.return_value = expected_result
        
        # Act
        result = get_all_caretaker_assignments(user_id)
        
        # Assert
        assert result == expected_result


class TestDeduplicateDocuments:
    """Tests for deduplicate_documents function"""

    def test_deduplicate_empty_list(self):
        """Test deduplicating empty list returns empty list"""
        # Act
        result = deduplicate_documents([])
        
        # Assert
        assert result == []

    def test_deduplicate_single_document(self):
        """Test deduplicating single document returns same document"""
        # Arrange
        doc = Mock(pk=1, kind='concept')
        
        # Act
        result = deduplicate_documents([doc])
        
        # Assert
        assert len(result) == 1
        assert result[0] == doc

    def test_deduplicate_unique_documents(self):
        """Test deduplicating unique documents returns all documents"""
        # Arrange
        doc1 = Mock(pk=1, kind='concept')
        doc2 = Mock(pk=2, kind='project')
        doc3 = Mock(pk=3, kind='progress')
        
        # Act
        result = deduplicate_documents([doc1, doc2, doc3])
        
        # Assert
        assert len(result) == 3
        assert doc1 in result
        assert doc2 in result
        assert doc3 in result

    def test_deduplicate_duplicate_documents(self):
        """Test deduplicating removes duplicate documents"""
        # Arrange
        doc1 = Mock(pk=1, kind='concept')
        doc2 = Mock(pk=1, kind='concept')  # Duplicate
        doc3 = Mock(pk=2, kind='project')
        
        # Act
        result = deduplicate_documents([doc1, doc2, doc3])
        
        # Assert
        assert len(result) == 2
        assert doc1 in result
        assert doc3 in result

    def test_deduplicate_same_id_different_kind(self):
        """Test documents with same ID but different kind are kept"""
        # Arrange
        doc1 = Mock(pk=1, kind='concept')
        doc2 = Mock(pk=1, kind='project')  # Same ID, different kind
        
        # Act
        result = deduplicate_documents([doc1, doc2])
        
        # Assert
        assert len(result) == 2
        assert doc1 in result
        assert doc2 in result

    def test_deduplicate_serialized_documents(self):
        """Test deduplicating serialized documents (dicts)"""
        # Arrange
        doc1 = {'id': 1, 'kind': 'concept', 'title': 'Doc 1'}
        doc2 = {'id': 2, 'kind': 'project', 'title': 'Doc 2'}
        doc3 = {'id': 1, 'kind': 'concept', 'title': 'Doc 1 Duplicate'}
        
        # Act
        result = deduplicate_documents([doc1, doc2, doc3], is_serialized=True)
        
        # Assert
        assert len(result) == 2
        assert doc1 in result
        assert doc2 in result

    def test_deduplicate_serialized_unique_documents(self):
        """Test deduplicating unique serialized documents"""
        # Arrange
        doc1 = {'id': 1, 'kind': 'concept'}
        doc2 = {'id': 2, 'kind': 'project'}
        doc3 = {'id': 3, 'kind': 'progress'}
        
        # Act
        result = deduplicate_documents([doc1, doc2, doc3], is_serialized=True)
        
        # Assert
        assert len(result) == 3

    def test_deduplicate_serialized_same_id_different_kind(self):
        """Test serialized documents with same ID but different kind are kept"""
        # Arrange
        doc1 = {'id': 1, 'kind': 'concept'}
        doc2 = {'id': 1, 'kind': 'project'}
        
        # Act
        result = deduplicate_documents([doc1, doc2], is_serialized=True)
        
        # Assert
        assert len(result) == 2

    def test_deduplicate_handles_missing_kind_attribute(self):
        """Test deduplication handles documents without kind attribute"""
        # Arrange
        doc1 = Mock(pk=1)
        del doc1.kind  # Remove kind attribute
        doc2 = Mock(pk=2, kind='project')
        
        # Act
        result = deduplicate_documents([doc1, doc2])
        
        # Assert
        # Should handle gracefully and include both
        assert len(result) == 2

    def test_deduplicate_handles_missing_id_key_serialized(self):
        """Test deduplication handles serialized docs without id key"""
        # Arrange
        doc1 = {'kind': 'concept'}  # Missing id
        doc2 = {'id': 2, 'kind': 'project'}
        
        # Act
        result = deduplicate_documents([doc1, doc2], is_serialized=True)
        
        # Assert
        # Should handle gracefully - doc1 skipped due to KeyError
        assert len(result) == 1
        assert doc2 in result

    def test_deduplicate_handles_missing_kind_key_serialized(self):
        """Test deduplication handles serialized docs without kind key"""
        # Arrange
        doc1 = {'id': 1}  # Missing kind
        doc2 = {'id': 2, 'kind': 'project'}
        
        # Act
        result = deduplicate_documents([doc1, doc2], is_serialized=True)
        
        # Assert
        # Should handle gracefully - doc1 skipped due to KeyError
        assert len(result) == 1
        assert doc2 in result

    def test_deduplicate_preserves_order(self):
        """Test deduplication preserves order of first occurrence"""
        # Arrange
        doc1 = Mock(pk=1, kind='concept')
        doc2 = Mock(pk=2, kind='project')
        doc3 = Mock(pk=1, kind='concept')  # Duplicate of doc1
        doc4 = Mock(pk=3, kind='progress')
        
        # Act
        result = deduplicate_documents([doc1, doc2, doc3, doc4])
        
        # Assert
        assert len(result) == 3
        # First occurrence of each unique document is kept
        assert result[0] == doc1
        assert result[1] == doc2
        assert result[2] == doc4

    def test_deduplicate_multiple_duplicates(self):
        """Test deduplication with multiple duplicates"""
        # Arrange
        doc1 = Mock(pk=1, kind='concept')
        doc2 = Mock(pk=1, kind='concept')  # Duplicate
        doc3 = Mock(pk=1, kind='concept')  # Duplicate
        doc4 = Mock(pk=2, kind='project')
        
        # Act
        result = deduplicate_documents([doc1, doc2, doc3, doc4])
        
        # Assert
        assert len(result) == 2
        assert doc1 in result
        assert doc4 in result

    def test_deduplicate_mixed_valid_and_invalid_documents(self):
        """Test deduplication with mix of valid and invalid documents"""
        # Arrange
        doc1 = Mock(pk=1, kind='concept')
        doc2 = Mock(pk=2)  # Missing kind
        del doc2.kind
        doc3 = Mock(pk=3, kind='project')
        
        # Act
        result = deduplicate_documents([doc1, doc2, doc3])
        
        # Assert
        # All should be included (invalid ones handled gracefully)
        assert len(result) == 3
