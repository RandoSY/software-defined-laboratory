"""PDP-12 Digital Cooling Lab: independent DS18B20 evidence validation.

This module has no hardware dependencies. It can be imported by both
MicroPython on the RP2040 and CPython unit tests on a development PC.

Design principle: preserve the MSP430's *raw* observation. Do not replace
its reported temperature with a calculated value without showing the
cross-check and associated validity flags.
"""


def crc8(data):
    """Dallas/Maxim reflected CRC-8: polynomial 0x31, reflected 0x8C."""
    crc = 0
    for byte in data:
        b = byte
        for _ in range(8):
            mix = (crc ^ b) & 1
            crc >>= 1
            if mix:
                crc ^= 0x8C
            b >>= 1
    return crc


def from_hex(text, count):
    """Decode precisely count bytes; return None when absent/invalid."""
    if text == 'NA' or len(text) != count * 2:
        return None
    try:
        return bytes.fromhex(text)
    except (ValueError, TypeError):
        return None


def signed16(value):
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def decode_scratch_x16(scratch):
    """Match resolution handling of the original MSP430 decoder.

    DS18B20 scratchpad byte 4 holds config bits R1:R0. Undefined LSBs in
    lower-resolution mode must be removed before interpreting raw value.
    """
    resolution = 9 + ((scratch[4] >> 5) & 3)
    mask = (0xFFFF << (12 - resolution)) & 0xFFFF
    raw = ((scratch[1] << 8) | scratch[0]) & mask
    return signed16(raw), resolution


def parse_evidence(line):
    """Parse a legacy-compatible MSP430 ASCII telemetry line.

    Returns a dictionary, or None for an unrelated line. Raises ValueError
    for a malformed observation; the caller should report and count it.
    """
    if not line.startswith('SEQ_HEX='):
        return None
    parts = {}
    for field in line.strip().split(','):
        if '=' not in field:
            raise ValueError('Missing equal sign in field')
        key, value = field.split('=', 1)
        if key in parts:
            raise ValueError('Duplicate field')
        parts[key] = value
    needed = ('SEQ_HEX', 'STATUS', 'STATE', 'X16_HEX', 'ROM', 'SCRATCH', 'INJECT')
    if any(key not in parts for key in needed):
        raise ValueError('Missing required evidence field')
    try:
        seq = int(parts['SEQ_HEX'], 16)
        status = int(parts['STATUS'])
        state = int(parts['STATE'])
        reported = signed16(int(parts['X16_HEX'], 16))
        injected = int(parts['INJECT'])
    except ValueError:
        raise ValueError('Invalid numerical evidence field')
    if not 0 <= seq <= 65535:
        raise ValueError('Sequence number out of range')
    rom = from_hex(parts['ROM'], 8)
    scratch = from_hex(parts['SCRATCH'], 9)
    rom_crc_ok = rom is not None and crc8(rom[:7]) == rom[7] and rom[0] == 0x28
    scratch_crc_ok = scratch is not None and crc8(scratch[:8]) == scratch[8]
    decoded = None
    resolution = None
    if scratch_crc_ok:
        decoded, resolution = decode_scratch_x16(scratch)
    agreement = decoded is not None and decoded == reported
    # Only real, consistent, non-injected sensor readings may enter the fit.
    valid = status == 0 and injected == 0 and rom_crc_ok and scratch_crc_ok and agreement
    reasons = []
    if status != 0:
        reasons.append('MSP_STATUS=' + str(status))
    if injected:
        reasons.append('INJECT=' + str(injected))
    if not rom_crc_ok:
        reasons.append('ROM_CRC_OR_FAMILY')
    if not scratch_crc_ok:
        reasons.append('SCRATCH_CRC')
    if decoded is not None and not agreement:
        reasons.append('TEMP_DISAGREES')
    return {
        'seq': seq,
        'status': status,
        'state': state,
        'x16': reported,
        'temp_c': reported / 16.0 if valid else None,
        'rom': parts['ROM'],
        'scratch': parts['SCRATCH'],
        'inject': injected,
        'rom_crc_ok': bool(rom_crc_ok),
        'scratch_crc_ok': bool(scratch_crc_ok),
        'temp_agrees': bool(agreement),
        'resolution_bits': resolution,
        'valid': bool(valid),
        'quality': 'OK' if valid else ';'.join(reasons),
    }
