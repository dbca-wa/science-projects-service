import base64, os
from django.contrib.staticfiles import finders
from django.conf import settings


def get_encoded_image():
    # Find the path to the image using Django's staticfiles finders
    image_path = os.path.join(settings.BASE_DIR, "dbca.jpg")
    print(f"DBCA IMAGE PATH: {image_path}")
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_encoded = base64.b64encode(image_data).decode("utf-8")
            return f"data:image/jpeg;base64,{image_encoded}"
    else:
        return None
