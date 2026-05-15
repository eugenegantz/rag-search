def get_resource_type(filepath_or_url: str) -> str:
    lowered = filepath_or_url.lower().strip()

    if lowered.endswith((".html", ".txt", ".md", ".docx", ".pdf")):
        return "text"

    elif lowered.endswith(('.jpg', '.jpeg', '.png')):
        return "image"

    else:
        return ""