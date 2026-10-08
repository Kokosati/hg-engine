#!/usr/bin/env python3

from pathlib import Path
import struct

ARM9_PATH = Path("base/arm9.bin")

# HGSS English – New Game spawn data
SPAWN_HEADER_OFFSET = 0xFA17C
SPAWN_X_OFFSET      = 0xFA184
SPAWN_Y_OFFSET      = 0xFA188
SPAWN_DIR_OFFSET    = 0xFA18C

# Original HGSS:
# Header 64 = New Bark Town player house 2F
ORIGINAL = (64, 6, 6, 1)

# Ash's Journey:
# Header 506 = Pallet Town / Red's House 2F
# Global position 6,7
# Direction 1 = Down
TARGET = (506, 6, 7, 1)


def read_u16(f, offset):
    f.seek(offset)
    return struct.unpack("<H", f.read(2))[0]


def write_u16(f, offset, value):
    f.seek(offset)
    f.write(struct.pack("<H", value))


if not ARM9_PATH.exists():
    raise SystemExit(f"ERROR: {ARM9_PATH} not found")

with ARM9_PATH.open("r+b") as arm9:
    current = (
        read_u16(arm9, SPAWN_HEADER_OFFSET),
        read_u16(arm9, SPAWN_X_OFFSET),
        read_u16(arm9, SPAWN_Y_OFFSET),
        read_u16(arm9, SPAWN_DIR_OFFSET),
    )

    if current not in (ORIGINAL, TARGET):
        raise SystemExit(
            "ERROR: Unexpected New Game spawn values in ARM9: "
            f"{current}. Expected {ORIGINAL} or {TARGET}."
        )

    write_u16(arm9, SPAWN_HEADER_OFFSET, TARGET[0])
    write_u16(arm9, SPAWN_X_OFFSET,      TARGET[1])
    write_u16(arm9, SPAWN_Y_OFFSET,      TARGET[2])
    write_u16(arm9, SPAWN_DIR_OFFSET,    TARGET[3])

print(
    "Ash's Journey start spawn patched: "
    "Pallet Town / Ash's room, header 506, position 6,7, Down"
)
