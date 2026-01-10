import os
import shutil
import json
import zipfile
import tarfile
import os
from pathlib import Path

from src.utils.logger_module.omix_logger import OmixForgeLogger
logger = OmixForgeLogger.get_logger()

def ensure_directory(path: str | list) -> None:    
    """Ensure that a directory exists; create it if it doesn't.
    If path_list is provided, ensure all directories in the list exist."""
    if  isinstance(path, list):
        for path in path:
            if not os.path.exists(path):
                os.makedirs(path)
    else:  
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
    try:
        with open(file_path, 'a') as f:
            f.write(content)
    except Exception as e:  
        logger.error(f"Error appending to file '{file_path}': {str(e)}")

def delete_file(file_path: str) -> None:
    """Delete a file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)

def delete_directory(directory_path: str) -> None:
    """Delete a directory and all its contents."""
    
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)

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
    
    shutil.copy2(src, dest) 

def move_file(src: str, dest: str) -> None:
    """Move a file from src to dest."""
    
    shutil.move(src, dest)  

def json_read(file_path: str) -> dict:
    """Read JSON content from a file and return as a dictionary."""
    
    with open(file_path, 'r') as f:
        return json.load(f)

def json_write(file_path: str, data: dict) -> None:
    """Write a dictionary as JSON content to a file."""
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def zip_folder(folder_path, zip_path):
    """Create a ZIP archive of a directory.
    
    Parameters
    ----------
    folder_path : str
        Path to the folder to zip.
    zip_path : str
        Path where the ZIP file will be saved.
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arc_path = os.path.relpath(full_path, folder_path)
                zipf.write(full_path, arc_path)

def tar_folder(folder_path, tar_path):
    """
    Create a .tar.gz archive from a folder.
    Preserves directory structure and avoids ZIP overhead issues.
    """
    folder_path = os.path.abspath(folder_path)

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(folder_path, arcname=os.path.basename(folder_path))

def untar_folder(tar_path, extract_to):
    """
    Extract a .tar.gz archive to a target directory.

    - Preserves original folder structure
    - Restores original file sizes
    - Works with archives created by tar_folder()
    """
    try:
        tar_path = os.path.abspath(tar_path)
        extract_to = os.path.abspath(extract_to)

        if not file_exists(tar_path):
            raise FileNotFoundError(f"Tar file not found: {tar_path}")

        ensure_directory(extract_to)

        with tarfile.open(tar_path, "r:*") as tar:
            tar.extractall(path=extract_to)
    except Exception as e:
        logger.error(f"Failed to extract file - {e} - {tar_path}")
        raise

def items_collector(root_dir: str, extentions: list, exclude_dir: set):
    """
    Collect file paths from a given root dir for specific extentions
    
    :param root_dir: Root dir to extract the file
    :type root_dir: str
    :param extentions: list of extentions to get file
    :type extentions: list
    :param exclude_dir: List of dir to exclude
    :type exclude_dir: set
    """
    files_collected = []
    exclude_dir = set(exclude_dir)
    for root,dir, files in os.walk(root_dir):
        if exclude_dir.intersection(set(root.split("/"))) :
            continue
        for file in files:
            if Path(file).suffix in extentions:
                files_collected.append(os.path.join(root,file))
    
    return files_collected
        