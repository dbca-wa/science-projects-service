import base64
import os


def get_encoded_image():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Define the path to the dbca.jpg file
    DBCA_IMAGE_PATH = os.path.join(script_dir, "dbca.jpg")
    # DBCA_IMAGE_PATH = os.path.join(os.getcwd(), "files/agencies/dbca.jpg")
    if os.path.exists(DBCA_IMAGE_PATH):
        with open(DBCA_IMAGE_PATH, "rb") as image_file:
            image_data = image_file.read()
            image_encoded = base64.b64encode(image_data).decode("utf-8")
            return f"data:image/jpeg;base64,{image_encoded}"
    else:
        return None
