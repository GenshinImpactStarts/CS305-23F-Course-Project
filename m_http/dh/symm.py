__all__ = 'Symm',


class Symm:
    KEY_LEN = 64

    def encode(data: bytes, key: bytes) -> bytearray:
        result = bytearray(data)
        i = 0
        data_len = len(data)
        j = 0
        while i < data_len:
            result[i] ^= key[j]
            i += 1
            j += 1
            if j == Symm.KEY_LEN:
                j = 0
        return result

    def decode(data: bytes, key: bytes) -> bytearray:
        return Symm.encode(data, key)
