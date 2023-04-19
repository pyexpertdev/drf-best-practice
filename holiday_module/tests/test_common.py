import os

from django.core.files.uploadedfile import SimpleUploadedFile
from dotenv import load_dotenv

from holiday.holiday_module.constants import CONTENT_TYPE

load_dotenv()


def upload_image():
    """test case to upload valid image"""
    with open(os.environ.get('RIGHT_IMAGE_PATH'), 'rb') as holiday_image:
        mock_policy_file = SimpleUploadedFile('test.png', holiday_image.read(), content_type=CONTENT_TYPE)
    return mock_policy_file


def update_image():
    """test case to update valid image"""
    with open(os.environ.get('UPDATE_IMAGE_PATH'), 'rb') as holiday_image:
        mock_policy_file = SimpleUploadedFile('test.png', holiday_image.read(), content_type=CONTENT_TYPE)
    return mock_policy_file


def upload_invalid_image():
    """test case to upload invalid image"""
    with open(os.environ.get('WRONG_IMAGE_PATH'), 'rb') as holiday_image:
        mock_policy_file = SimpleUploadedFile('test.pdf', holiday_image.read(), content_type=CONTENT_TYPE)
    return mock_policy_file


def upload_image_company_logo():
    with open(os.environ.get('RIGHT_IMAGE_PATH_COMPANY_LOGO'), 'rb') as company_logo:
        mock_policy_file = SimpleUploadedFile('default_company_logo.jpeg', company_logo.read(), content_type=CONTENT_TYPE)
    return mock_policy_file

def upload_image_favicon():
    with open(os.environ.get('RIGHT_IMAGE_PATH_FAVICON'), 'rb') as favicon_image:
        mock_policy_file = SimpleUploadedFile('favicon_company_web.png', favicon_image.read(), content_type=CONTENT_TYPE)
    return mock_policy_file
