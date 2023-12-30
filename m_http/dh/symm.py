from math import log2

__all__ = 'Symm',


class Symm:
    def get_key(key: int) -> bytes:
        return key.to_bytes(int(log2(key)+1) // 8 + 1, 'big')

    def encode(data: bytes, key: bytes) -> bytearray:
        result = bytearray(data)
        data_len = len(data)
        key_len = len(key)
        i = 0
        j = 0
        while i < data_len:
            result[i] ^= key[j]
            i += 1
            j += 1
            if j == key_len:
                j = 0
        return result

    def decode(data: bytes, key: bytes) -> bytearray:
        return Symm.encode(data, key)
