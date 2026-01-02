from Crypto.Cipher import AES
import base64
import codecs
import hashlib

# The encrypted string from auth.yaml.bak
encrypted_b64 = "U2FsdGVkX1+KzyITACK2aAnUm2JJfWia3o9tKZ2KX8V8mzilBkE2gSRdo4Q5dfIF"
password = "nexus2024!"

# Decode base64
encrypted_data = base64.b64decode(encrypted_b64)

# Check OpenSSL format
if encrypted_data[:8] != b'Salted__':
    print("Error: Not OpenSSL format")
    exit(1)

# Extract salt
salt = encrypted_data[8:16]
ciphertext = encrypted_data[16:]

print(f"Salt: {salt.hex()}")
print(f"Ciphertext length: {len(ciphertext)}")

# Derive key and IV using OpenSSL's EVP_BytesToKey
def evp_bytes_to_key(password, salt, key_len=32, iv_len=16):
    """Equivalent to OpenSSL's EVP_BytesToKey with count=1 and md5 hash"""
    m = []
    i = 0
    while len(b''.join(m)) < (key_len + iv_len):
        md5 = hashlib.md5()
        data = password.encode() + salt
        if i > 0:
            data = m[i - 1] + data
        md5.update(data)
        m.append(md5.digest())
        i += 1
    ms = b''.join(m)
    return ms[:key_len], ms[key_len:key_len + iv_len]

key, iv = evp_bytes_to_key(password, salt)

print(f"Key: {key.hex()[:32]}...")
print(f"IV: {iv.hex()}")

# Decrypt
cipher = AES.new(key, AES.MODE_CBC, iv)
decrypted = cipher.decrypt(ciphertext)

print(f"Decrypted (with padding): {decrypted.hex()}")

# Remove PKCS#7 padding
pad_len = decrypted[-1]
if 1 <= pad_len <= 16:
    plaintext = decrypted[:-pad_len].decode('utf-8', errors='ignore')
else:
    plaintext = decrypted.decode('utf-8', errors='ignore')

print(f"\nStep 1: Decrypted (ROT13): {plaintext}")

# ROT13 decode
email = codecs.decode(plaintext, 'rot_13')
print(f"Step 2: ROT13 decoded: {email}")

# Calculate hash prefix
hash_prefix = hashlib.sha256(email.encode()).hexdigest()[:6]
print(f"Step 3: Hash prefix: {hash_prefix}")

print(f"\n✅ FINAL ANSWER: {email}:{hash_prefix}")
