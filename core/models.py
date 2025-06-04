from django.db import models
import os
from django.core.exceptions import ValidationError

# Create your models here.


def validate_svg_or_image(value):
    ext = os.path.splitext(value.name)[1].lower()
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".svg"]

    if ext not in allowed_extensions:
        raise ValidationError("Only JPG, PNG, GIF, and SVG files are allowed.")
