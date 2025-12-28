from src.utils.encryption.handle import *
from src.utils.fileops.file_handle import file_exists, delete_file
import pytest

def test_generate_encrypted_file(get_test_files, get_lock_key):

    # test valid generation
    generate_encrypted_file("key", get_test_files['file_path']+'.enc', get_lock_key['lock'] )
    assert file_exists(get_test_files['file_path']+'.enc')

    data = decrypt_file(f"{get_test_files['file_path']}.enc", get_lock_key['lock'], True)
    assert data == 'key'

    # test invalid key
    with pytest.raises(ValueError):
        generate_encrypted_file("key", get_test_files['file_path']+'.enc',"none" )
    
    with pytest.raises(AttributeError):
        generate_encrypted_file(None, get_test_files['file_path']+'.enc' , get_lock_key['lock'] )

    if file_exists(get_test_files['file_path']+'.enc'):
        delete_file(get_test_files['file_path']+'.enc')



def test_encrypt_file(get_test_files, get_lock_key):

    # tests file encryption
    encrypt_file(get_test_files['file_path'], get_lock_key['lock'])
    assert file_exists(get_test_files['file_path']+'.enc')

    data = decrypt_file(f"{get_test_files['file_path']}.enc", get_lock_key['lock'], True)
    assert data == 'key'

    # test invalid path
    with pytest.raises(FileNotFoundError):
        encrypt_file(get_test_files['file_path']+"none", get_lock_key['lock'])

    # test invalid key
    with pytest.raises(ValueError):
        encrypt_file(get_test_files['file_path'], "none")

    if file_exists(get_test_files['file_path']+'.enc'):
        delete_file(get_test_files['file_path']+'.enc')
    

def test_decrypt_file(get_test_files, get_lock_key):

    # test valid decryption
    generate_encrypted_file("key", get_test_files['file_path']+'.enc', get_lock_key['lock'] )
    assert file_exists(get_test_files['file_path']+'.enc')

    data = decrypt_file(f"{get_test_files['file_path']}.enc", get_lock_key['lock'], True)
    assert data == 'key'

    # test valid file generation
    decrypt_file(f"{get_test_files['file_path']}.enc", get_lock_key['lock'])
    assert file_exists(get_test_files['file_path'])

    # test invalid file path
    with pytest.raises(FileNotFoundError):
        data = decrypt_file(f"{get_test_files['file_path']}.enc"+'none', get_lock_key['lock'], True)

    # test invalid key
    with pytest.raises(ValueError):
        data = decrypt_file(f"{get_test_files['file_path']}.enc", "", True)

    if file_exists(get_test_files['file_path']+'.enc'):
        delete_file(get_test_files['file_path']+'.enc')
    

def test_generate_key(get_lock_key):
    # test valid key generation
    key = generate_key(get_lock_key['key'])
    assert key == get_lock_key['lock'], "Failed to generate valid key"

    # test invalid key
    key = generate_key(get_lock_key['key'])
    assert key != 'key=', "Failed to test invalid key"

    # test invalid input
    with pytest.raises(AttributeError):
        generate_key(123)






