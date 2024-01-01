from math import log2

__all__ = 'Symm',


class Symm:
    def __init__(self, key: int):
        self.key = key.to_bytes(int(log2(key)+1) // 8 + 1, 'big')
        self.key_len = len(self.key)
        self.encode_key_idx = 0
        self.decode_key_idx = 0

    def encode(self, data: bytes) -> bytearray:
        result = bytearray(data)
        data_len = len(data)
        i = 0
        while i < data_len:
            result[i] ^= self.key[self.encode_key_idx]
            i += 1
            self.encode_key_idx += 1
            if self.encode_key_idx == self.key_len:
                self.encode_key_idx = 0
        return result

    def decode(self, data: bytes) -> bytearray:
        result = bytearray(data)
        data_len = len(data)
        i = 0
        while i < data_len:
            result[i] ^= self.key[self.decode_key_idx]
            i += 1
            self.decode_key_idx += 1
            if self.decode_key_idx == self.key_len:
                self.decode_key_idx = 0
        return result
