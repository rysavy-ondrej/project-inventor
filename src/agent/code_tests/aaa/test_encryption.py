from unittest.mock import patch
from jose import jwt
from aaa import encryption


def test_encrypt_valid_input():
    data = {"user": "Alice", "role": "admin"}
    key = "my_secret_key"

    result = encryption.encrypt(data, key)

    assert result == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiQWxpY2UiLCJyb2xlIjoiYWRtaW4ifQ.FP9lViTRIAddIUvGNQMoNy871b0miXL3kM2iKvYVydM"


def test_encrypt_valid_input_nested():
    data = {"key1": "value1", "key2": 2, "key3": {"inner1": "value3.1", "inner2": 3.2}}
    key = "my_secret_key"

    result = encryption.encrypt(data, key)

    assert result == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkxIjoidmFsdWUxIiwia2V5MiI6Miwia2V5MyI6eyJpbm5lcjEiOiJ2YWx1ZTMuMSIsImlubmVyMiI6My4yfX0.v91c3dAKqQhCgACTegpd3Zcg_N35l9fMAZ-y6h9vgPY"


@patch('utils.logs.error')
def test_encrypt_invalid_data_type(mock_error):
    data = ["not", "a", "dict"]
    key = "my_secret_key"

    result = encryption.encrypt(data, key)
    assert result is None

    mock_error.assert_called_with("Unable to encrypt the data - wrong data type <class 'list'> instead of dictionary.")


@patch('utils.logs.error')
def test_encrypt_invalid_key_type(mock_error):
    data = {"user": "Alice"}
    key = 12345  # Not a string

    result = encryption.encrypt(data, key)
    assert result is None

    mock_error.assert_called_with("Unable to encrypt the data - wrong key type <class 'int'> instead of string.")


@patch('jose.jwt.encode', side_effect=jwt.JWTError("Some error"))
@patch('utils.logs.error')
def test_encrypt_jwt_error_unknown_reason(mock_error, mock_encode):
    data = {"user": "Alice"}
    key = "my_secret_key"

    result = encryption.encrypt(data, key)

    assert result is None
    mock_error.assert_called_with("Unable to encrypt the data - unknown reason.")


def test_encrypt_empty_dict():
    data = {}
    key = "my_secret_key"

    result = encryption.encrypt(data, key)

    assert result == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.p10yaiAwCVW5_sASd6qj8QeWzaQBeMSeUaV_w22JzSM"


def test_encrypt_empty_key():
    data = {"user": "Alice"}
    key = ""

    result = encryption.encrypt(data, key)

    assert result == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiQWxpY2UifQ.WH2XXtVpSGuV0ugGjypw5hEAnMkl2Tvk0Mt4DV3l7Mc"


def test_decrypt_valid_input():
    ciphertext = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkxIjoidmFsdWUxIiwia2V5MiI6Miwia2V5MyI6eyJpbm5lcjEiOiJ2YWx1ZTMuMSIsImlubmVyMiI6My4yfX0.v91c3dAKqQhCgACTegpd3Zcg_N35l9fMAZ-y6h9vgPY"
    key = "my_secret_key"
    expected_output = {"key1": "value1", "key2": 2, "key3": {"inner1": "value3.1", "inner2": 3.2}}

    result = encryption.decrypt(ciphertext, key)
    assert result == expected_output


@patch('utils.logs.error')
def test_decrypt_invalid_ciphertext_type(mock_error):
    ciphertext = 12345  # Not a string
    key = "my_secret_key"

    result = encryption.decrypt(ciphertext, key)

    assert result is None
    mock_error.assert_called_with("Unable to decrypt the data - message must be a string and not <class 'int'>.")


@patch('utils.logs.error')
def test_decrypt_invalid_key_type(mock_error):
    ciphertext = "valid_encoded_string"
    key = 12345  # Not a string

    result = encryption.decrypt(ciphertext, key)

    assert result is None
    mock_error.assert_called_with("Unable to decrypt the data - key be a string and not <class 'int'>.")


@patch('utils.logs.error')
def test_decrypt_invalid_key(mock_error):
    ciphertext = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiQWxpY2UiLCJyb2xlIjoiYWRtaW4ifQ.FP9lViTRIAddIUvGNQMoNy871b0miXL3kM2iKvYVydM"
    key = "invalid_key"

    result = encryption.decrypt(ciphertext, key)

    assert result is None
    mock_error.assert_called_with("Unable to decrypt the data - probably the key is invalid.")


@patch('utils.logs.error')
def test_decrypt_invalid_ciphertext(mock_error):
    ciphertext = "asdasdsadasdasdasdasd"
    key = "my_secret_key"

    result = encryption.decrypt(ciphertext, key)

    assert result is None
    mock_error.assert_called_with("Unable to decrypt the data - probably the key is invalid.")


@patch('jose.jwt.decode', side_effect=jwt.JWTError("Unknown error"))
@patch('utils.logs.error')
def test_decrypt_unknown_reason(mock_error, mock_decode):
    ciphertext = "valid_encoded_string"
    key = "my_secret_key"

    result = encryption.decrypt(ciphertext, key)

    assert result is None
    mock_error.assert_called_with("Unable to decrypt the data - probably the key is invalid.")


@patch('utils.logs.error')
def test_decrypt_empty_ciphertext(mock_error):
    ciphertext = ""
    key = "my_secret_key"

    result = encryption.decrypt(ciphertext, key)

    assert result is None
    mock_error.assert_called_with("Unable to decrypt the data - probably the key is invalid.")


@patch('utils.logs.error')
def test_decrypt_empty_key(mock_error):
    ciphertext = "valid_encoded_string"
    key = ""

    result = encryption.decrypt(ciphertext, key)

    assert result is None
    mock_error.assert_called_with("Unable to decrypt the data - probably the key is invalid.")


def test_calculate_hash_valid_string():
    data = "Hello, world!"
    expected_result = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"

    result = encryption.calculate_hash(data)

    assert result == expected_result


def test_calculate_hash_empty_string():
    data = ""
    expected_result = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    result = encryption.calculate_hash(data)

    assert result == expected_result


@patch('utils.logs.error')
def test_calculate_hash_non_string(mock_error):
    data = 12345

    result = encryption.calculate_hash(data)

    assert result is None
    mock_error.assert_called_with("Unable to hash the nonstring value type <class 'int'>.")


@patch('utils.logs.error')
def test_calculate_hash_unicode_encode_error(mock_error):
    data = "Hello, world!\udc00"  # Invalid character for UTF-8

    result = encryption.calculate_hash(data)

    assert result is None
    mock_error.assert_called_with("Unable to hash the value - encoding error.")


def test_calculate_hash_special_characters():
    data = "!@#$%^&*()_+-={}[]|\\:;\"'<>,.?/"
    expected_result = "09d9aeffb7ffed7ea05fde28de5d6ea783f7daf7a3715548981c58385d8f1ff8"

    result = encryption.calculate_hash(data)

    assert result == expected_result


@patch('utils.logs.error')
def test_calculate_hash_none(mock_error):
    data = None

    result = encryption.calculate_hash(data)

    assert result is None
    mock_error.assert_called_with("Unable to hash the nonstring value type <class 'NoneType'>.")


def test_calculate_hash_long_string():
    data = "a" * 100000000
    expected_result = "83d30385a4a11980275dc23de3fb49ff37b906cc841efa048a96c62d90ff3b5f"

    result = encryption.calculate_hash(data)

    assert result == expected_result
