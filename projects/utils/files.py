"""
Project file handling utilities
"""
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def handle_project_image(image):
    """
    Handle project image upload
    
    Args:
        image: Uploaded image file or string path
        
    Returns:
        File path string or None
    """
    if isinstance(image, str):
        return image
    
    if image is None:
        return None
    
    # Get original filename
    original_filename = image.name
    subfolder = "projects"
    file_path = f"{subfolder}/{original_filename}"
    
    # Check if file already exists with same size
    if default_storage.exists(file_path):
        full_file_path = default_storage.path(file_path)
        if os.path.exists(full_file_path):
            existing_file_size = os.path.getsize(full_file_path)
            new_file_size = image.size
            if existing_file_size == new_file_size:
                # File already exists with same size, reuse it
                return file_path
    
    # Save new file
    content = ContentFile(image.read())
    file_path = default_storage.save(file_path, content)
    return file_path
