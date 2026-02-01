"""
Helper utilities for caretaker operations
"""


def get_all_caretaker_assignments(user_id, processed_users=None):
    """
    Recursively gather all caretaker assignments, including nested relationships
    
    Args:
        user_id: ID of user to check
        processed_users: Set of already processed user IDs (for recursion)
        
    Returns:
        List of Caretaker objects
        
    Note:
        This function is kept here for backward compatibility but delegates
        to CaretakerTaskService for the actual implementation
    """
    from ..services import CaretakerTaskService
    return CaretakerTaskService.get_all_caretaker_assignments(user_id, processed_users)


def deduplicate_documents(docs, is_serialized=False):
    """
    Remove duplicate documents from list
    
    Args:
        docs: List of documents (objects or serialized dicts)
        is_serialized: Whether docs are already serialized
        
    Returns:
        List of unique documents
    """
    doc_dict = {}
    
    for doc in docs:
        try:
            if is_serialized:
                key = f"{doc['id']}_{doc['kind']}"
            else:
                key = f"{doc.pk}_{getattr(doc, 'kind', '')}"
            
            if key in doc_dict:
                continue
            
            doc_dict[key] = doc
            
        except (KeyError, AttributeError) as e:
            print(f"Error processing document: {e}")
            continue
    
    return list(doc_dict.values())
