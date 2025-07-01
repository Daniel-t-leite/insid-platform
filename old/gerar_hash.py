import hashlib

senha = "inSID2025"
hash = hashlib.sha256(senha.encode()).hexdigest()
print(f"Hash gerado: {hash}")