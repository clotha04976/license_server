import json
import hashlib
import base64
import datetime
import secrets

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

import os
from ..core.config import settings
from ..models.license import License

import binascii

# It's crucial that these keys are configured securely in your environment
# and match the keys used by the client application.
try:
    AES_KEY = binascii.unhexlify(settings.LICENSE_AES_KEY)
except (binascii.Error, TypeError):
    raise ValueError("LICENSE_AES_KEY in .env file is not a valid hex string.")

# Ensure AES_KEY is 32 bytes (for AES-256)
if len(AES_KEY) != 32:
    raise ValueError(f"Decoded LICENSE_AES_KEY must be 32 bytes long, but got {len(AES_KEY)} bytes.")

# --- Load Private Key from file ---
KEYS_DIR = os.path.join(os.path.dirname(__file__), '..', 'keys')
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, 'private_key.pem')

if not os.path.exists(PRIVATE_KEY_PATH):
    raise FileNotFoundError(f"Private key not found at: {PRIVATE_KEY_PATH}")

with open(PRIVATE_KEY_PATH, "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
        backend=default_backend()
    )

def _sign_license_data(license_data: dict) -> str:
    """Signs license data using the private key."""
    # Ensure json is encoded to utf-8 before hashing
    license_json = json.dumps(license_data, sort_keys=True, default=str, ensure_ascii=False)
    license_hash = hashlib.sha256(license_json.encode('utf-8')).digest()
    
    signature = private_key.sign(
        license_hash,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

def _encrypt_license_data(license_data: dict) -> bytes:
    """Encrypts the license data using AES-256-CBC."""
    json_data = json.dumps(license_data, ensure_ascii=False, default=str).encode('utf-8')
    
    padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(json_data) + padder.finalize()
    
    iv = secrets.token_bytes(16)
    
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    
    return base64.b64encode(iv + encrypted_data)

def generate_license_file_content(license_obj: License, machine_code: str, hardware_ids: dict = None, app_version: str = None) -> bytes:
    """
    Generates the final encrypted and signed .lic file content.
    """
    # 1. Prepare the data payload
    license_data = {
        "license_id": license_obj.serial_number, # Use serial_number as license_id
        "machine_code": machine_code,
        "licensed_to": license_obj.customer.name,
        "email": license_obj.customer.email,
        "issued_at": license_obj.created_at,
        "expires_at": license_obj.expires_at,
        "features": license_obj.features,
        "connection_type": license_obj.connection_type,
    }
    
    # 添加硬體ID資訊（如果提供）
    if hardware_ids:
        license_data["hardware_ids"] = hardware_ids
    
    # 添加應用程式版本資訊（如果提供）
    if app_version:
        license_data["app_version"] = app_version
    
    # 2. Sign the data
    signature = _sign_license_data(license_data)
    license_data_with_signature = license_data.copy()
    license_data_with_signature["signature"] = signature
    
    # 3. Encrypt the data with signature
    encrypted_content = _encrypt_license_data(license_data_with_signature)
    
    return encrypted_content