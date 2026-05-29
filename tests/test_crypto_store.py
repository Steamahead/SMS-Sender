from core import crypto_store


class TestCryptoStore:
    def test_roundtrip_returns_original(self):
        secret = "sk-ant-api03-SECRET-value-123"
        protected = crypto_store.protect(secret)
        assert crypto_store.unprotect(protected) == secret

    def test_empty_passthrough(self):
        assert crypto_store.protect("") == ""
        assert crypto_store.unprotect("") == ""

    def test_plaintext_unprotect_passthrough(self):
        # A value without the dpapi: marker is treated as plaintext (migration).
        assert crypto_store.unprotect("legacy-plaintext-key") == "legacy-plaintext-key"

    def test_protected_value_is_marked_and_opaque(self):
        if not crypto_store.is_available():
            return  # DPAPI not present on this runner — nothing to assert
        secret = "my-api-key"
        protected = crypto_store.protect(secret)
        assert crypto_store.is_protected(protected)
        assert secret not in protected  # ciphertext must not leak the plaintext
