import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

# Read from auth.yaml.bak
encrypted_b64 = "U2FsdGVkX1+KzyITACK2aAnUm2JJfWia3o9tKZ2KX8V8mzilBkE2gSRdo4Q5dfIF"
password = "nexus2024!"

# Decode
encrypted_data = base64.b64decode(encrypted_b64)
salt = encrypted_data[8:16]
ciphertext_with_iv = encrypted_data[16:]

# Derive key
key = PBKDF2(password, salt, dkLen=32, count=10000)

# IV is embedded by AES.new when we created it
# Split: first 16 bytes are IV, rest is ciphertext
iv = ciphertext_with_iv[:16]
ciphertext = ciphertext_with_iv[16:]

# Decrypt
cipher = AES.new(key, AES.MODE_CBC, iv)
decrypted = cipher.decrypt(ciphertext)

# Remove padding
pad_len = decrypted[-1]
plaintext = decrypted[:-pad_len].decode()

print(f"Decrypted: {plaintext}")

# ROT13
import codecs
email = codecs.decode(plaintext, 'rot_13')
print(f"Email: {email}")

# Hash
import hashlib
hash_prefix = hashlib.sha256(email.encode()).hexdigest()[:6]
print(f"Hash: {hash_prefix}")
print(f"\n✅ ANSWER: {email}:{hash_prefix}")
