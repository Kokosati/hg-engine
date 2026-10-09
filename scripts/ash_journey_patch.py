#!/usr/bin/env python3

from pathlib import Path
import struct


def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def write_u16(data, offset, value):
    struct.pack_into("<H", data, offset, value)


# ============================================================
# Ash's Journey
# Permanent binary patches
# ============================================================


# ------------------------------------------------------------
# 1. NEW GAME START POSITION -> PALLET TOWN
# ------------------------------------------------------------

ARM9_PATH = Path("base/arm9.bin")

SPAWN_HEADER_OFFSET = 0xFA17C
SPAWN_X_OFFSET      = 0xFA184
SPAWN_Y_OFFSET      = 0xFA188
SPAWN_DIR_OFFSET    = 0xFA18C

ORIGINAL_SPAWN = (64, 6, 6, 1)
ASH_SPAWN      = (506, 6, 7, 1)

arm9 = bytearray(ARM9_PATH.read_bytes())

current_spawn = (
    read_u16(arm9, SPAWN_HEADER_OFFSET),
    read_u16(arm9, SPAWN_X_OFFSET),
    read_u16(arm9, SPAWN_Y_OFFSET),
    read_u16(arm9, SPAWN_DIR_OFFSET),
)

if current_spawn not in (ORIGINAL_SPAWN, ASH_SPAWN):
    raise SystemExit(
        "ERROR: Unexpected New Game spawn values: "
        f"{current_spawn}"
    )

write_u16(arm9, SPAWN_HEADER_OFFSET, ASH_SPAWN[0])
write_u16(arm9, SPAWN_X_OFFSET,      ASH_SPAWN[1])
write_u16(arm9, SPAWN_Y_OFFSET,      ASH_SPAWN[2])
write_u16(arm9, SPAWN_DIR_OFFSET,    ASH_SPAWN[3])

ARM9_PATH.write_bytes(arm9)

print(
    "Ash's Journey: start -> "
    "Pallet Town / Ash's room (header 506, 6,7, Down)"
)


# ------------------------------------------------------------
# 2. OAK INTRO
# ------------------------------------------------------------

OV53_PATH = Path("base/overlay/overlay_0053.bin")
ov53 = bytearray(OV53_PATH.read_bytes())


# ------------------------------------------------------------
# 2a. After Oak's final intro sentence:
#
# Original:
#   State 60 -> State 61 = gender selection
#
# Previous test:
#   State 60 -> State 94 = naming
#
# Final:
#   State 60 -> State 110 = fade out
#
# Runtime address 0x021E7806
# ------------------------------------------------------------

INTRO_TRANSITION_OFFSET = 0x1F06

STATE_GENDER = 0x203D     # movs r0, #61
STATE_NAME   = 0x205E     # movs r0, #94
STATE_FADE   = 0x206E     # movs r0, #110

current = read_u16(ov53, INTRO_TRANSITION_OFFSET)

if current not in (STATE_GENDER, STATE_NAME, STATE_FADE):
    raise SystemExit(
        "ERROR: Unexpected Oak intro transition: "
        f"0x{current:04X}"
    )

write_u16(ov53, INTRO_TRANSITION_OFFSET, STATE_FADE)

print(
    "Ash's Journey: gender and name selection skipped"
)


# ------------------------------------------------------------
# 2b. OakSpeech_Exit()
#
# Replace the normal:
#
#   PlayerName_StringToFlat(profile, enteredName)
#   PlayerProfile_SetTrainerGender(profile, enteredGender)
#
# with:
#
#   profile->name = "Ash"
#   profile->gender = male
#
# Runtime block:
#   0x021E5B60 .. 0x021E5B7D
#
# File offset:
#   0x260
#
# Character codes:
#   A   = 299 = 0x012B
#   s   = 343 = 0x0157
#   h   = 332 = 0x014C
#   EOS = 0xFFFF
#
# gender offset in PlayerProfile = 0x18
# male = 0
# ------------------------------------------------------------

NAME_BLOCK_OFFSET = 0x260

ORIGINAL_NAME_BLOCK = bytes.fromhex(
    "12 21 "
    "09 01 "
    "61 58 "
    "89 69 "
    "43 f6 ec f9 "
    "60 68 "
    "43 f6 95 f9 "
    "12 21 "
    "09 01 "
    "61 58 "
    "49 68 "
    "43 f6 09 fa"
)

ASH_NAME_BLOCK = bytes.fromhex(
    # movs r1, #255
    "ff 21 "

    # adds r1, #44  -> 299 ('A')
    "2c 31 "
    # strh r1, [r0, #0]
    "01 80 "

    # adds r1, #44  -> 343 ('s')
    "2c 31 "
    # strh r1, [r0, #2]
    "41 80 "

    # subs r1, #11  -> 332 ('h')
    "0b 39 "
    # strh r1, [r0, #4]
    "81 80 "

    # movs r1, #0
    "00 21 "
    # mvns r1, r1   -> 0xFFFFFFFF
    "c9 43 "
    # strh r1, [r0, #6] -> 0xFFFF EOS
    "c1 80 "

    # movs r1, #0
    "00 21 "
    # strb r1, [r0, #24] -> male
    "01 76 "

    # padding
    "c0 46 "
    "c0 46 "
    "c0 46"
)

current_block = bytes(
    ov53[
        NAME_BLOCK_OFFSET:
        NAME_BLOCK_OFFSET + len(ORIGINAL_NAME_BLOCK)
    ]
)

if current_block not in (ORIGINAL_NAME_BLOCK, ASH_NAME_BLOCK):
    raise SystemExit(
        "ERROR: Unexpected OakSpeech_Exit name block.\n"
        f"Current: {current_block.hex(' ')}"
    )

ov53[
    NAME_BLOCK_OFFSET:
    NAME_BLOCK_OFFSET + len(ASH_NAME_BLOCK)
] = ASH_NAME_BLOCK

print(
    "Ash's Journey: player name fixed to Ash; gender fixed to male"
)


# ------------------------------------------------------------
# 2c. REMOVE ETHAN SHRINK SEQUENCE
#
# State 111 normally:
#
#   wait for fade
#   state = 120
#
# State 120 draws Ethan/Lyra and starts the shrink sequence.
#
# Instead, after the fade completes we set r5 = TRUE.
# OakSpeech_DoMainTask() therefore reports completion immediately.
#
# Runtime address:
#   0x021E7C66
#
# Original:
#   movs r0, #120 = 0x2078
#
# Final:
#   movs r5, #1   = 0x2501
# ------------------------------------------------------------

SHRINK_END_OFFSET = 0x2366

ORIGINAL_SHRINK = 0x2078
ASH_END_INTRO   = 0x2501

current = read_u16(ov53, SHRINK_END_OFFSET)

if current not in (ORIGINAL_SHRINK, ASH_END_INTRO):
    raise SystemExit(
        "ERROR: Unexpected shrink transition: "
        f"0x{current:04X}"
    )

write_u16(ov53, SHRINK_END_OFFSET, ASH_END_INTRO)

print(
    "Ash's Journey: Ethan/Lyra shrink sequence removed"
)


OV53_PATH.write_bytes(ov53)

print("Ash's Journey: intro patches complete")
