import mimetypes
import base64, os
from django.contrib.staticfiles import finders
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage


# def get_encoded_image():
#     """
#     Encodes the DBCA logo image as a base64 string for email embedding.
#     """
#     try:
#         image_path = os.path.join(settings.BASE_DIR, "documents", "dbca.jpg")
#         with open(image_path, "rb") as img:
#             import base64

#             return (
#                 f"data:image/jpeg;base64,{base64.b64encode(img.read()).decode('utf-8')}"
#             )
#     except Exception as e:
#         settings.LOGGER.error(f"Error encoding image: {e}")
#         return ""


def get_encoded_image():
    """
    Return a filename or empty string (for template compatibility)
    """
    try:
        return "dbca.jpg"
    except Exception as e:
        settings.LOGGER.error(f"Error getting image: {e}")
        return ""


def send_email_with_embedded_image(
    recipient_email, subject, html_content, from_email=None
):
    """
    Send an email with an embedded image and HTML content.

    :param recipient_email: Email address of the recipient
    :param subject: Email subject line
    :param html_content: HTML content of the email
    :param from_email: Sender's email (defaults to settings.DEFAULT_FROM_EMAIL)
    """
    # Use default from email if not provided
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    # Create message
    msg = EmailMultiAlternatives(
        subject,
        # Plain text fallback
        "Please view this email in an HTML-compatible email client.",
        from_email,
        # [recipient_email],
        recipient_email,
    )

    # Attach HTML alternative
    msg.attach_alternative(html_content, "text/html")

    # Attach image if exists
    try:
        image_path = os.path.join(settings.BASE_DIR, "documents", "dbca.jpg")

        # Determine the correct MIME type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"  # Default to JPEG if can't guess

        with open(image_path, "rb") as img:
            image = MIMEImage(img.read(), _subtype=mime_type.split("/")[-1])
            image.add_header("Content-ID", "<dbca_logo>")
            msg.attach(image)
    except Exception as e:
        settings.LOGGER.error(f"Error attaching image: {e}")
        settings.LOGGER.error(f"Image path: {image_path}")
        # Continue sending email even if image attachment fails

    # Send the message
    msg.send()


# def get_encoded_image():
#     # Find the path to the image using Django's staticfiles finders
#     image_path = os.path.join(settings.BASE_DIR, "dbca.jpg")
#     print(f"DBCA IMAGE PATH: {image_path}")
#     if image_path and os.path.exists(image_path):
#         with open(image_path, "rb") as image_file:
#             image_data = image_file.read()
#             image_encoded = base64.b64encode(image_data).decode("utf-8")
#             return f"data:image/jpeg;base64,{image_encoded}"
#     else:
#         return None


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
