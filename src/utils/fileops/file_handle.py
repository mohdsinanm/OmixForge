import os

def ensure_directory(path: str) -> None:    
    """Ensure that a directory exists; create it if it doesn't."""
    if not os.path.exists(path):
        os.makedirs(path)

def write_to_file(file_path: str, content: str) -> None:
    """Write content to a file."""
    with open(file_path, 'w') as f:
        f.write(content)

def read_from_file(file_path: str) -> str:
    """Read content from a file."""
    with open(file_path, 'r') as f:
        return f.read() 

def append_to_file(file_path: str, content: str) -> None:
    """Append content to a file."""
    with open(file_path, 'a') as f:
        f.write(content)

def delete_file(file_path: str) -> None:
    """Delete a file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)

def list_files_in_directory(directory_path: str) -> list:
    """List all files in a given directory."""
    if os.path.exists(directory_path):
        return os.listdir(directory_path)
    return []   

def file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return os.path.exists(file_path)    

def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes."""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

def copy_file(src: str, dest: str) -> None:
    """Copy a file from src to dest."""
    import shutil
    shutil.copy2(src, dest) 

def move_file(src: str, dest: str) -> None:
    """Move a file from src to dest."""
    import shutil
    shutil.move(src, dest)  