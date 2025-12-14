import base64
from cryptography.fernet import Fernet
import hashlib
from src.utils.logger_module.omix_logger import OmixForgeLogger
logger = OmixForgeLogger.get_logger()

def generate_encrypted_file(data: str, filepath: str, key: bytes):
    """
    Generate an encrypted file with the given data and key.

    :param data: Data to be encrypted
    :type data: str
    :param filepath: Path to save the encrypted file
    :type filepath: str
    :param key: Encryption key
    :type key: bytes
    """
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    with open(filepath, 'wb') as file:
        file.write(encrypted_data)
    logger.info(f"Encrypted file generated at: {filepath}")

def encrypt_file(path:str, key: bytes):
    """
    Given a file path and a key, encrypt the file and save it with .enc extension.    
    
    :param path: Path to the file to be encrypted
    :param key: Encryption key
    """
    fernet = Fernet(key)
    with open(path, 'rb') as original_file:
        encrypted = fernet.encrypt(original_file.read())
    with open(path + ".enc", 'wb') as encrypted_file:
        encrypted_file.write(encrypted)


def decrypt_file(filepath: str, key: bytes, need_data: bool = False):
    """
    Decrypt an encrypted file.

    - Returns bytes by default
    - Decodes ONLY if need_data=True
    - Safe for binary files (.tar.gz, .pdf, etc.)
    """
    try:
        fernet = Fernet(key)

        with open(filepath, "rb") as file:
            encrypted_data = file.read()

        decrypted_bytes = fernet.decrypt(encrypted_data)

        # If caller wants data returned
        if need_data:
            try:
                return decrypted_bytes.decode("utf-8")  # text files only
            except UnicodeDecodeError:
                return decrypted_bytes  # binary fallback

        # Otherwise write decrypted file
        output_path = str(filepath).replace(".enc", "")
        with open(output_path, "wb") as f:
            f.write(decrypted_bytes)

        return output_path

    except Exception as e:
        logger.error(f"Failed to decrypt {filepath}: {e}")
        raise
        


def generate_key( s: str) -> str:
    """
    Generate a URL-safe base64-encoded key from a given string using SHA-256 hashing.

    :param s: Input string to generate the key from
    :type s: str
    :return: Generated key as a URL-safe base64-encoded string
    :rtype: str
    """
    digest = hashlib.sha256(s.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode()