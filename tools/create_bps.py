#!/usr/bin/env python3
"""Create a compact BPS patch using same-offset copies and changed runs only."""
import argparse
import binascii
import hashlib
import struct
from pathlib import Path


def encode_number(value):
    if value < 0:
        raise ValueError("BPS values must be non-negative")
    out = bytearray()
    while True:
        digit = value & 0x7F
        value >>= 7
        if value == 0:
            out.append(digit | 0x80)
            return out
        out.append(digit)
        value -= 1


def bps_action(kind, length):
    if length <= 0:
        raise ValueError("BPS actions must have positive length")
    return encode_number(((length - 1) << 2) | kind)


def build_patch(source, target):
    stream = bytearray()
    i = 0
    target_len = len(target)
    source_len = len(source)
    min_copy = 4

    while i < target_len:
        if i < source_len and source[i] == target[i]:
            end = i + 1
            while end < target_len and end < source_len and source[end] == target[end]:
                end += 1
            if end - i >= min_copy:
                stream.extend(bps_action(0, end - i))  # SourceRead
                i = end
                continue

        start = i
        i += 1
        while i < target_len:
            if i < source_len and source[i] == target[i]:
                end = i + 1
                while end < target_len and end < source_len and source[end] == target[end]:
                    end += 1
                if end - i >= min_copy:
                    break
                i = end
            else:
                i += 1

        stream.extend(bps_action(1, i - start))  # TargetRead
        stream.extend(target[start:i])

    patch = bytearray(b"BPS1")
    patch.extend(encode_number(source_len))
    patch.extend(encode_number(target_len))
    patch.extend(encode_number(0))  # no metadata
    patch.extend(stream)
    patch.extend(struct.pack("<I", binascii.crc32(source) & 0xFFFFFFFF))
    patch.extend(struct.pack("<I", binascii.crc32(target) & 0xFFFFFFFF))
    patch.extend(struct.pack("<I", binascii.crc32(patch) & 0xFFFFFFFF))
    return bytes(patch)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    source = args.source.read_bytes()
    target = args.target.read_bytes()
    patch = build_patch(source, target)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patch)

    print("Source SHA1:", hashlib.sha1(source).hexdigest())
    print("Target SHA1:", hashlib.sha1(target).hexdigest())
    print("BPS size:", len(patch))


if __name__ == "__main__":
    main()
