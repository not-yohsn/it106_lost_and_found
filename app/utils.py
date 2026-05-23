import os
import uuid

from flask import current_app
from PIL import Image

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_DIMENSION = 1200
THUMBNAIL_DIMENSION = 256


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file_storage):
    """Save an uploaded image (resized to max 1200px) and return its path
    relative to the static folder, or None if no/invalid file was given."""
    if not file_storage or not file_storage.filename:
        return None
    if not _allowed(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    if ext == "jpeg":
        ext = "jpg"
    new_name = f"{uuid.uuid4().hex}.{ext}"

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    full_path = os.path.join(upload_dir, new_name)

    img = Image.open(file_storage.stream)
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

    save_kwargs = {}
    if ext == "jpg":
        if img.mode != "RGB":
            img = img.convert("RGB")
        save_kwargs.update(quality=85, optimize=True)

    img.save(full_path, **save_kwargs)

    # Generate a small thumbnail next to the original for fast list-view
    # rendering. Same filename, "_thumb" suffix before the extension.
    thumb_name = f"{new_name.rsplit('.', 1)[0]}_thumb.{ext}"
    thumb_path = os.path.join(upload_dir, thumb_name)
    img.thumbnail((THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION))
    img.save(thumb_path, **save_kwargs)

    return f"uploads/{new_name}"


def thumbnail_path_for(photo_path):
    """Given 'uploads/abc.jpg', return 'uploads/abc_thumb.jpg'.

    Returns the original path if no thumbnail was generated (legacy uploads).
    """
    if not photo_path:
        return photo_path
    base, _, ext = photo_path.rpartition(".")
    if not base:
        return photo_path
    return f"{base}_thumb.{ext}"
