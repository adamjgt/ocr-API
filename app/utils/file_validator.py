ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

def validate_file(file):
    filename = file.filename.lower()
    ext = filename.split(".")[-1]

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")
