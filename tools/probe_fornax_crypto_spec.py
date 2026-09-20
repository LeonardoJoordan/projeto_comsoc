"""Experimento da etapa 2; não é o leitor/escritor de produção do FORNAX.

Execute em ambiente isolado com cryptography==50.0.1. Segredos FIXOS abaixo
são vetores públicos de teste e nunca devem ser usados pelo aplicativo.
"""
import hashlib
import json
import platform
import statistics
import time
import unicodedata

import cryptography
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


def password_bytes(value):
    normalized = unicodedata.normalize("NFC", value)
    if not 8 <= len(normalized) <= 64:
        raise ValueError("Senha fora dos limites")
    return normalized.encode("utf-8", errors="strict")


def derive(value, salt):
    return Argon2id(salt=salt, length=32, iterations=3, lanes=1,
                    memory_cost=65536).derive(password_bytes(value))


def main():
    samples = []
    salt = bytes(range(16))
    password = "Frase pública de teste 2026"
    for _ in range(7):
        start = time.perf_counter()
        kek = derive(password, salt)
        samples.append(round((time.perf_counter() - start) * 1000, 3))
    dek = bytes(range(32))
    wrap_nonce, payload_nonce = bytes(range(12)), bytes(range(12, 24))
    header = {
        "format": "fornax", "version": 1, "mode": "signatures",
        "model_id": "11111111-1111-4111-8111-111111111111",
        "revision_id": "22222222-2222-4222-8222-222222222222",
        "crypto_profile": "a2id-64m-t3-p1-aes256gcm-v1",
        "salt": salt.hex(), "wrap_nonce": wrap_nonce.hex(),
        "payload_nonce": payload_nonce.hex(),
    }
    header_bytes = json.dumps(header, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=True, allow_nan=False).encode("ascii")
    aad_wrap = b"FORNAX/v1/wrap\0" + header_bytes
    aad_payload = b"FORNAX/v1/payload\0" + header_bytes
    wrapped = AESGCM(kek).encrypt(wrap_nonce, dek, aad_wrap)
    # Saídas congeladas para detectar alteração acidental do perfil/AAD.
    assert kek.hex() == "0c1b99d37d90fb462ec192743e92877df162181a158361b7000b40e1a72de5b3"
    assert wrapped.hex() == (
        "38a86c33205773b74bd80be90c5afc36e0f89c497453cf530b8cee0c7086383ba1a9"
        "a843a89063c417af9be7056891e2"
    )
    plaintext = b'{"public_sha256":"synthetic-reference","signatures":[]}'
    encrypted = AESGCM(dek).encrypt(payload_nonce, plaintext, aad_payload)
    assert AESGCM(kek).decrypt(wrap_nonce, wrapped, aad_wrap) == dek
    assert AESGCM(dek).decrypt(payload_nonce, encrypted, aad_payload) == plaintext
    rejected = []
    for name, key, nonce, data, aad in [
        ("wrong_password", derive("Senha incorreta", salt), wrap_nonce, wrapped, aad_wrap),
        ("tampered_wrap", kek, wrap_nonce, wrapped[:-1] + bytes([wrapped[-1] ^ 1]), aad_wrap),
        ("tampered_payload", dek, payload_nonce, encrypted[:-1] + bytes([encrypted[-1] ^ 1]), aad_payload),
        ("changed_header", dek, payload_nonce, encrypted, aad_payload + b"changed"),
        ("wrong_purpose", dek, payload_nonce, encrypted, aad_wrap),
    ]:
        try:
            AESGCM(key).decrypt(nonce, data, aad)
        except InvalidTag:
            rejected.append(name)
        else:
            raise AssertionError(name)
    assert password_bytes("assinátu") == password_bytes("assina\u0301tu")
    assert password_bytes(" " * 8) == b" " * 8
    assert len(password_bytes("é" * 64)) == 128
    for invalid in ("a" * 7, "a" * 65):
        try:
            password_bytes(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Limite de senha")
    before, after = hashlib.sha256(b"before").hexdigest(), hashlib.sha256(b"after").hexdigest()
    assert before != after
    # Mudança pública não participa do AAD: permite decifrar e alertar depois.
    assert AESGCM(dek).decrypt(payload_nonce, encrypted, aad_payload) == plaintext
    print(json.dumps({
        "scope": "isolated primitive probe; no production package implementation",
        "platform": platform.platform(), "python": platform.python_version(),
        "cryptography": cryptography.__version__, "openssl": backend.openssl_version_text(),
        "profile": header["crypto_profile"], "samples_ms": samples,
        "median_ms": statistics.median(samples), "rejected": rejected,
        "unicode_and_length_checks": "passed", "public_change_does_not_block_decryption": True,
        "public_test_vector": {"header_ascii": header_bytes.decode(),
            "password": password, "dek_hex": dek.hex(), "kek_hex": kek.hex(),
            "wrapped_key_hex": wrapped.hex(), "plaintext_hex": plaintext.hex(),
            "encrypted_hex": encrypted.hex()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
