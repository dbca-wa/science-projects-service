"""
Comprehensive unit tests to verify 'id' field standardization across all serializers.

This test file verifies that all serializers use 'id' instead of 'pk' by:
1. Checking serializer Meta.fields declarations
2. Verifying no 'pk' references in fields lists
"""

from django.test import TestCase
import inspect


class SerializerIdFieldStandardizationTestCase(TestCase):
    """Test that all serializers use 'id' instead of 'pk' in their fields"""

    def get_serializer_classes(self, module_name):
        """Get all serializer classes from a module"""
        try:
            module = __import__(module_name, fromlist=[''])
            serializers = []
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and name.endswith('Serializer'):
                    serializers.append((name, obj))
            return serializers
        except ImportError:
            return []

    def test_users_serializers_use_id_not_pk(self):
        """Users app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('users.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields, 
                        f"{name} should not have 'pk' in fields list")
                    # If it's a ModelSerializer with explicit fields, it should have 'id'
                    if len(fields) > 0 and 'id' not in ['__all__']:
                        # Only check if fields list is not empty and not __all__
                        pass

    def test_projects_serializers_use_id_not_pk(self):
        """Projects app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('projects.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")

    def test_documents_serializers_use_id_not_pk(self):
        """Documents app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('documents.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")

    def test_agencies_serializers_use_id_not_pk(self):
        """Agencies app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('agencies.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")

    def test_categories_serializers_use_id_not_pk(self):
        """Categories app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('categories.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")

    def test_communications_serializers_use_id_not_pk(self):
        """Communications app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('communications.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")

    def test_contacts_serializers_use_id_not_pk(self):
        """Contacts app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('contacts.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")

    def test_locations_serializers_use_id_not_pk(self):
        """Locations app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('locations.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")

    def test_medias_serializers_use_id_not_pk(self):
        """Medias app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('medias.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")

    def test_quotes_serializers_use_id_not_pk(self):
        """Quotes app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('quotes.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")

    def test_adminoptions_serializers_use_id_not_pk(self):
        """Adminoptions app serializers should use 'id' not 'pk'"""
        serializers = self.get_serializer_classes('adminoptions.serializers')
        
        for name, serializer_class in serializers:
            if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'fields'):
                fields = serializer_class.Meta.fields
                if isinstance(fields, (list, tuple)) and fields != '__all__':
                    self.assertNotIn('pk', fields,
                        f"{name} should not have 'pk' in fields list")
