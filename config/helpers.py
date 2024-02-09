
import base64
import os


def get_encoded_image():
    DBCA_IMAGE_PATH = os.path.join(os.getcwd(), "files/agencies/dbca.jpg")
    if os.path.exists(DBCA_IMAGE_PATH):
        with open(DBCA_IMAGE_PATH, 'rb') as image_file:
            image_data = image_file.read()
            image_encoded = base64.b64encode(image_data).decode("utf-8")
            return f"data:image/jpeg;base64,{image_encoded}"
    else:
        return None
    