import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2

# The ROT13 version of the email to encrypt
plaintext = "q4gn.rk7enpg@cebgbaznvy.pu"
password = "nexus2024!"

# Generate salt
salt = get_random_bytes(8)

# Derive key using PBKDF2
key = PBKDF2(password, salt, dkLen=32, count=10000)

# Pad plaintext to AES block size
pad_len = 16 - (len(plaintext) % 16)
padded = plaintext + chr(pad_len) * pad_len

print(f"Plaintext: {plaintext} (length: {len(plaintext)})")
print(f"Padded: {padded} (length: {len(padded)})")
print(f"Salt: {salt.hex()}")

# Encrypt
cipher = AES.new(key, AES.MODE_CBC)
ciphertext = cipher.encrypt(padded.encode())

print(f"IV: {cipher.iv.hex()}")
print(f"Ciphertext length: {len(ciphertext)}")

# Format as OpenSSL Salted format  
# Structure: "Salted__" + salt + IV + ciphertext
openssl_format = b'Salted__' + salt + cipher.iv + ciphertext
encrypted_b64 = base64.b64encode(openssl_format).decode()

print(f"\nEncrypted string (for auth.yaml.bak):")
print(encrypted_b64)

# Test decryption
print(f"\n--- Testing Decryption ---")
encrypted_data = base64.b64decode(encrypted_b64)
test_salt = encrypted_data[8:16]
test_iv = encrypted_data[16:32]
test_ciphertext = encrypted_data[32:]

test_key = PBKDF2(password, test_salt, dkLen=32, count=10000)
test_cipher = AES.new(test_key, AES.MODE_CBC, test_iv)
test_decrypted = test_cipher.decrypt(test_ciphertext)

test_pad_len = test_decrypted[-1]
test_plaintext = test_decrypted[:-test_pad_len].decode()

print(f"Decrypted: {test_plaintext}")

import codecs
test_email = codecs.decode(test_plaintext, 'rot_13')
print(f"ROT13: {test_email}")

test_hash = hashlib.sha256(test_email.encode()).hexdigest()[:6]
print(f"Hash: {test_hash}")
print(f"\n✅ Final answer: {test_email}:{test_hash}")
