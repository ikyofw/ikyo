import base64
import logging
import os
import shutil
import traceback
from pathlib import Path

import core.core.fs as fs
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
from Crypto.PublicKey import RSA

from django_backend.settings import BASE_DIR

logger = logging.getLogger('backend')

ENCRYPT_FORDER = os.path.join(BASE_DIR, 'var', 'encrypt')
ENCRYPT_PUBLIC_PEM = Path(os.path.join(BASE_DIR, 'var', 'encrypt'), 'rsa_public_key.pem')
ENCRYPT_PRIVATE_PEM = Path(os.path.join(BASE_DIR, 'var', 'encrypt'), 'rsa_private_key.pem')


def generateRsaKeys() -> None:
    # get keys
    random_generator = Random.new().read
    rsa = RSA.generate(1024, random_generator)
    public_key = rsa.publickey().exportKey()
    private_key = rsa.exportKey()
    if not os.path.exists(ENCRYPT_FORDER):
        fs.mkdirs(ENCRYPT_FORDER)
    # save keys
    with open(ENCRYPT_PUBLIC_PEM, 'wb')as f:
        f.write(public_key)

    with open(ENCRYPT_PRIVATE_PEM, 'wb')as f:
        f.write(private_key)


def getPublicKey() -> str:
    if not os.path.exists(ENCRYPT_PUBLIC_PEM):
        return None
    with open(ENCRYPT_PUBLIC_PEM) as publicKeyFile:
        data = publicKeyFile.read()
        # pub_key = RSA.importKey(data)
        return data


def getPrivateKey() -> str:
    if not os.path.exists(ENCRYPT_PRIVATE_PEM):
        return None
    with open(ENCRYPT_PRIVATE_PEM) as privateKeyFile:
        data = privateKeyFile.read()
        pri_key = RSA.importKey(data)
        return pri_key


def encryptData(data) -> str:
    cipher = PKCS1_cipher.new(getPublicKey())  # Generate an encrypted class
    encrypted_data = base64.b64encode(cipher.encrypt(data.encode()))  # Encrypt data
    return encrypted_data.decode()  # Decode text

    return None


def decryptData(data) -> str:
    cipher = PKCS1_cipher.new(getPrivateKey())  # Generate a decryption class
    decrypted_data = cipher.decrypt(base64.b64decode(data), 0)
    return decrypted_data.decode()
