"""Generate and parse MongoDB-compatible ObjectId values.

ObjectId is a 12-byte value, represented as 24 hex chars. Layout used here:
- 4 bytes: big-endian Unix timestamp (seconds)
- 5 bytes: random/process-unique bytes
- 3 bytes: counter (monotonic per-process)

This implementation follows the general structure of MongoDB ObjectId
enough for compatibility (hex form, 12-byte binary, creation time).
"""

import os
import time
import threading
import struct
import binascii
from typing import Optional


class ObjectId:
    """A minimal MongoDB ObjectId compatible implementation."""

    # 3-byte counter, initialized randomly to reduce collision odds across restarts
    _inc_lock = threading.Lock()
    _inc = int.from_bytes(os.urandom(3), "big")
    # 5 random bytes used as process-unique fingerprint
    _rand5 = os.urandom(5)

    def __init__(self, value: Optional[bytes | str] = None):
        """Create a new ObjectId.

        - If `value` is None: generate a new id.
        - If `value` is a 24-char hex string: parse it.
        - If `value` is bytes of length 12: use those bytes.
        """
        if value is None:
            self._bytes = self._generate()
        elif isinstance(value, str):
            hexstr = value
            if not ObjectId.is_valid(hexstr):
                raise ValueError("Invalid ObjectId hex string")
            self._bytes = binascii.unhexlify(hexstr)
        elif isinstance(value, (bytes, bytearray)):
            b = bytes(value)
            if len(b) != 12:
                raise ValueError("ObjectId bytes must be 12 bytes long")
            self._bytes = b
        else:
            raise TypeError(
                "ObjectId must be created from None, 12 bytes, or 24-char hex string"
            )

    @classmethod
    def _generate(cls) -> bytes:
        ts = int(time.time())
        ts_bytes = struct.pack(">I", ts)  # 4 bytes
        rand5 = cls._rand5
        with cls._inc_lock:
            c = cls._inc
            cls._inc = (cls._inc + 1) % 0x1000000
        counter_bytes = c.to_bytes(3, "big")
        return ts_bytes + rand5 + counter_bytes

    @classmethod
    def from_hex(cls, hexstr: str) -> "ObjectId":
        return cls(hexstr)

    @classmethod
    def from_bytes(cls, b: bytes) -> "ObjectId":
        return cls(b)

    @staticmethod
    def is_valid(hexstr: str) -> bool:
        if not isinstance(hexstr, str):
            return False
        if len(hexstr) != 24:
            return False
        try:
            binascii.unhexlify(hexstr)
            return True
        except (TypeError, binascii.Error):
            return False

    def __bytes__(self) -> bytes:
        return self._bytes

    def to_bytes(self) -> bytes:
        return self._bytes

    def __str__(self) -> str:
        return binascii.hexlify(self._bytes).decode()

    def to_hex(self) -> str:
        return str(self)

    def __repr__(self) -> str:
        return f"ObjectId('{self.to_hex()}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, ObjectId):
            return self._bytes == other._bytes
        if isinstance(other, (bytes, bytearray)):
            return self._bytes == bytes(other)
        if isinstance(other, str):
            return self.to_hex() == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._bytes)

    @property
    def generation_time(self) -> int:
        """Return the Unix timestamp (seconds) when the id was generated."""
        ts_bytes = self._bytes[0:4]
        return struct.unpack(">I", ts_bytes)[0]

    def __len__(self) -> int:
        return 12


if __name__ == "__main__":
    # Example usage
    oid = ObjectId()
    print(f"Generated ObjectId: {oid}")
    print(f"Bytes: {oid.to_bytes()}")
    print(f"Hex: {oid.to_hex()}")
    print(f"Generation time: {oid.generation_time}")

    # 从 hex 解析
    h = str(oid)
    oid2 = ObjectId(h)
    print(oid2.to_hex(), oid2.generation_time)

    # 比较
    print(oid == oid2)
