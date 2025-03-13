import base64, os
from django.contrib.staticfiles import finders
from django.conf import settings


def get_encoded_image():
    # Find the path to the image using BASE_DIR
    print(f"BASE_DIR is: {settings.BASE_DIR}")

    # Try multiple possible locations
    possible_paths = [
        os.path.join(settings.BASE_DIR, "documents", "dbca.jpg"),
        os.path.join(settings.BASE_DIR, "backend", "documents", "dbca.jpg"),
        # For Docker environment
        "/usr/src/app/backend/documents/dbca.jpg",
    ]

    for path in possible_paths:
        print(f"Trying path: {path}")
        if os.path.exists(path):
            print(f"Found image at: {path}")
            with open(path, "rb") as image_file:
                try:
                    image_data = image_file.read()
                    image_encoded = base64.b64encode(image_data).decode("utf-8")
                    return f"data:image/jpeg;base64,{image_encoded}"
                except Exception as e:
                    print(f"Error encoding image {path}: {str(e)}")

    print("Image not found in any of the tried paths")
    return None


def get_encoded_ar_dbca_image():
    # Find the path to the image using Django's staticfiles finders
    image_path = os.path.join(settings.BASE_DIR, "documents", "BCSTransparent.png")
    print(f"AR DBCA IMAGE PATH: {image_path}")
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_encoded = base64.b64encode(image_data).decode("utf-8")
            return f"data:image/png;base64,{image_encoded}"
    else:
        return None
