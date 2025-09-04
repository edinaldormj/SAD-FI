from pathlib import Path

def save_upload(uploaded_file, dest_path: str) -> str:
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(uploaded_file.read())
    return str(dest)
