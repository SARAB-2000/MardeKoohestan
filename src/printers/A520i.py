# تنها
# آخر چسبان
# اول چسبان
# وسط

import socket


SOCKET_HOST = "192.168.0.248"
SOCKET_PORT = 16000
SOCKET_START_CODE = "0002"
SOCKET_END_CODE = "0003"
SEPARATOR = ";"



word_dict = {
    "آ": {"prefix":"FE","codes": ["81", "82", "81", "82"], "original_code": "0622" , "stick_to_the_next": False},
    "ا": {"prefix":"FE","codes": ["8D", "8E", "8D", "8E"], "original_code": "0627" , "stick_to_the_next": False},
    "ب": {"prefix":"FE","codes": ["8F", "90", "91", "92"], "original_code": "0628" , "stick_to_the_next": True},
    "پ": {"prefix":"FB","codes": ["56", "57", "58", "59"], "original_code": "067E" , "stick_to_the_next": True},  
    "ت": {"prefix":"FE","codes": ["95", "96", "97", "98"], "original_code": "062A" , "stick_to_the_next": True},
    "ث": {"prefix":"FE","codes": ["99", "9A", "9B", "9C"], "original_code": "062B" , "stick_to_the_next": True},
    "ج": {"prefix":"FE","codes": ["9D", "9E", "9F", "A0"], "original_code": "062C" , "stick_to_the_next": True},
    "چ": {"prefix":"FB","codes": ["7A", "7B", "7C", "7D"], "original_code": "0686" , "stick_to_the_next": True},   
    "ح": {"prefix":"FE","codes": ["A1", "A2", "A3", "A4"], "original_code": "062D" , "stick_to_the_next": True},
    "خ": {"prefix":"FE","codes": ["A5", "A6", "A7", "A8"], "original_code": "062E" , "stick_to_the_next": True},
    "د": {"prefix":"FE","codes": ["A9", "AA", "A9", "AA"], "original_code": "062F" , "stick_to_the_next": False},
    "ذ": {"prefix":"FE","codes": ["AB", "AC", "AB", "AC"], "original_code": "0630" , "stick_to_the_next": False},  
    "ر": {"prefix":"FE","codes": ["AD", "AE", "AD", "AE"], "original_code": "0631" , "stick_to_the_next": False},
    "ز": {"prefix":"FE","codes": ["AF", "B0", "AF", "B0"], "original_code": "0632" , "stick_to_the_next": False},
    "ژ": {"prefix":"FB","codes": ["8A", "8B", "8A", "8B"], "original_code": "0698" , "stick_to_the_next": False},  
    "س": {"prefix":"FE","codes": ["B1", "B2", "B3", "B4"], "original_code": "0633" , "stick_to_the_next": True},
    "ش": {"prefix":"FE","codes": ["B5", "B6", "B7", "B8"], "original_code": "0634" , "stick_to_the_next": True},
    "ص": {"prefix":"FE","codes": ["B9", "BA", "BB", "BC"], "original_code": "0635" , "stick_to_the_next": True},
    "ض": {"prefix":"FE","codes": ["BD", "BE", "BF", "C0"], "original_code": "0636" , "stick_to_the_next": True},
    "ط": {"prefix":"FE","codes": ["C1", "C2", "C3", "C4"], "original_code": "0637" , "stick_to_the_next": True},
    "ظ": {"prefix":"FE","codes": ["C5", "C6", "C7", "C8"], "original_code": "0638" , "stick_to_the_next": True},
    "ع": {"prefix":"FE","codes": ["C9", "CA", "CB", "CC"], "original_code": "0639" , "stick_to_the_next": True},
    "غ": {"prefix":"FE","codes": ["CD", "CE", "CF", "D0"], "original_code": "063A" , "stick_to_the_next": True},
    "ف": {"prefix":"FE","codes": ["D1", "D2", "D3", "D4"], "original_code": "0641" , "stick_to_the_next": True},
    "ق": {"prefix":"FE","codes": ["D5", "D6", "D7", "D8"], "original_code": "0642" , "stick_to_the_next": True},  
    "ک": {"prefix":"FE","codes": ["D9", "DA", "DB", "DC"], "original_code": "06A9" , "stick_to_the_next": True},
    "گ": {"prefix":"FB","codes": ["92", "93", "94", "95"], "original_code": "06AF" , "stick_to_the_next": True},   
    "ل": {"prefix":"FE","codes": ["DD", "DE", "DF", "E0"], "original_code": "0644" , "stick_to_the_next": True},
    "م": {"prefix":"FE","codes": ["E1", "E2", "E3", "E4"], "original_code": "0645" , "stick_to_the_next": True},
    "ن": {"prefix":"FE","codes": ["E5", "E6", "E7", "E8"], "original_code": "0646" , "stick_to_the_next": True},
    "ه": {"prefix":"FE","codes": ["E9", "EA", "EB", "EC"], "original_code": "0647" , "stick_to_the_next": True},
    "و": {"prefix":"FE","codes": ["ED", "EE", "ED", "EE"], "original_code": "0648" , "stick_to_the_next": False},
    "ی": {"prefix":"FE","codes": ["EF", "F0", "F3", "F4"], "original_code": "06CC" , "stick_to_the_next": True},
    "ء": {"prefix":"FE","codes": ["80", "80", "80", "80"], "original_code": "0621" , "stick_to_the_next": False},
    "ئ": {"prefix":"FE","codes": ["89", "8A", "8B", "8C"], "original_code": "0626" , "stick_to_the_next": True},
    "ؤ": {"prefix":"FE","codes": ["85", "86", "85", "86"], "original_code": "0624" , "stick_to_the_next": False},
    "إ": {"prefix":"FE","codes": ["87", "88", "87", "88"], "original_code": "0625" , "stick_to_the_next": False},
    "أ": {"prefix":"FE","codes": ["83", "84", "83", "84"], "original_code": "0623" , "stick_to_the_next": False},
    "ۀ": {"prefix":"FE","codes": ["93", "94", "93", "94"], "original_code": "06C0" , "stick_to_the_next": False},
}

PRINTER_PREFIXES = {entry["prefix"] for entry in word_dict.values()}


def get_letter_code_index(chars: list[str], index: int) -> int:
    """Return code index: 0=isolated, 1=final, 2=initial, 3=medial."""
    char = chars[index]

    connects_prev = (
        index > 0
        and chars[index - 1] != " "
        and chars[index - 1] in word_dict
        and word_dict[chars[index - 1]]["stick_to_the_next"]
    )
    connects_next = (
        index < len(chars) - 1
        and chars[index + 1] != " "
        and char in word_dict
        and word_dict[char]["stick_to_the_next"]
    )

    if connects_prev and connects_next:
        return 3
    if connects_prev:
        return 1
    if connects_next:
        return 2
    return 0


def _next_non_space_index(text: str, start: int) -> int:
    i = start
    while i < len(text) and text[i] == " ":
        i += 1
    return i


def segment_text(text: str) -> list[str]:
    """Split text into Persian and non-Persian segments."""
    segments: list[str] = []
    i = 0
    length = len(text)

    while i < length:
        char = text[i]

        if char in word_dict:
            segment_chars: list[str] = []
            while i < length:
                current = text[i]
                if current in word_dict:
                    segment_chars.append(current)
                    i += 1
                elif current == " ":
                    next_index = _next_non_space_index(text, i + 1)
                    if next_index < length and text[next_index] in word_dict:
                        segment_chars.append(current)
                        i += 1
                    else:
                        break
                else:
                    break
            segments.append("".join(segment_chars))

        elif char == " ":
            i += 1

        else:
            segment_chars = []
            while i < length:
                current = text[i]
                if current not in word_dict:
                    if current == " ":
                        next_index = _next_non_space_index(text, i + 1)
                        if next_index < length and text[next_index] in word_dict:
                            break
                    segment_chars.append(current)
                    i += 1
                else:
                    break
            segments.append("".join(segment_chars))

    return segments


def char_to_utf16le_codes(char: str) -> list[str]:
    data = char.encode("utf-16-le")
    return [
        f"{int.from_bytes(data[index : index + 2], 'little'):04X}"
        for index in range(0, len(data), 2)
    ]


def persian_segment_to_codes(text: str) -> list[str]:
    """Convert a Persian segment to prefixed codes for each letter."""
    chars = list(text)
    codes: list[str] = []

    for i, char in enumerate(chars):
        if char == " ":
            codes.append("0020")
            continue
        if char not in word_dict:
            raise ValueError(f"Character not in word_dict: {char!r}")

        letter = word_dict[char]
        code_index = get_letter_code_index(chars, i)
        codes.append(f"{letter['prefix']}{letter['codes'][code_index]}")

    return codes


def segment_to_codes(segment: str) -> list[str]:
    if all(char in word_dict or char == " " for char in segment):
        return list(reversed(persian_segment_to_codes(segment)))

    codes: list[str] = []
    for char in segment:
        codes.extend(char_to_utf16le_codes(char))
    return codes


def word_to_codes(text: str) -> list[list[str]]:
    """Convert mixed text to codes; each segment is its own sublist."""
    return [segment_to_codes(segment) for segment in segment_text(text)]


def merge_segment_codes(
    codes_by_segment: list[list[str]], separator: str = "0020"
) -> list[str]:
    """Merge segment code lists into one list with separator between segments."""
    if not codes_by_segment:
        return []

    merged: list[str] = []
    for index, codes in enumerate(codes_by_segment):
        if index > 0:
            merged.append(separator)
        merged.extend(codes)
    return merged


def format_hex_code(code: str) -> str:
    """Format a hex string as 0X**** (4-digit uppercase hex)."""
    return f"0X{int(code, 16):04X}"


def format_hex_codes(codes: list[str]) -> list[str]:
    return [format_hex_code(code) for code in codes]


def text_to_framed_codes(text: str) -> list[str]:
    """Build raw hex code list with start/end frame codes."""
    codes_by_segment = word_to_codes(text)
    reversed_codes = list(reversed(codes_by_segment))
    merged_codes = merge_segment_codes(reversed_codes)
    return ["0002", *merged_codes, "0003"]


def is_printer_code(code: str) -> bool:
    return len(code) == 4 and code[:2] in PRINTER_PREFIXES


def code_to_bytes(code: str) -> bytes:
    """Convert one 4-digit hex code to 2 wire bytes."""
    if is_printer_code(code):
        return bytes.fromhex(code)
    return int(code, 16).to_bytes(2, "big")


def codes_to_binary_payload(codes: list[str]) -> bytes:
    """Convert hex codes to binary payload for printer socket."""
    return b"".join(code_to_bytes(code) for code in codes)


def codes_to_socket_payload(codes: list[str], separator: str = " ") -> str:
    """Join formatted hex codes into one string for display/logging."""
    return separator.join(format_hex_codes(codes))


def wrap_socket_frame(payload: str) -> str:
    """Add start/end frame codes around the socket payload string."""
    return f"{SOCKET_START_CODE} {payload} {SOCKET_END_CODE}"


def text_to_socket_payload(text: str, separator: str = " ") -> str:
    """Convert text to a single socket-ready hex string."""
    framed_codes = text_to_framed_codes(text)
    return codes_to_socket_payload(framed_codes, separator=separator)


def bytes_to_hex_dump(data: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def send_text_via_ready_socket(
    data: list[str],
    socket: socket.socket,
    timeout: float = 5.0,
) -> bytes:
    """Connect to socket and send framed binary payload."""
    binary_payload = code_to_bytes("0002")
    for index, item in enumerate(data):
        framed_codes = text_to_framed_codes(item)
        framed_codes = framed_codes[1:-1]
        binary_payload += codes_to_binary_payload(framed_codes)
        if index < len(data) - 1:
            binary_payload += SEPARATOR.encode("utf-16-be")

    binary_payload += code_to_bytes("0003")

    print("binary_payload:", bytes_to_hex_dump(binary_payload))

    socket.sendall(binary_payload)

    return binary_payload


def print_word_codes(text: str) -> bytes:
    segments = segment_text(text)
    codes_by_segment = word_to_codes(text)
    reversed_codes = list(reversed(codes_by_segment))
    merged_codes = merge_segment_codes(reversed_codes)
    framed_codes = text_to_framed_codes(text)
    formatted_codes = format_hex_codes(merged_codes)
    socket_payload = codes_to_socket_payload(merged_codes)
    framed_payload = text_to_socket_payload(text)
    binary_payload = codes_to_binary_payload(framed_codes)

    print("segments:", segments)
    print("codes:")
    for codes in reversed_codes:
        print(format_hex_codes(codes))
    print("merged:", formatted_codes)
    print("socket:", socket_payload)
    print("framed:", framed_payload)
    print("binary:", bytes_to_hex_dump(binary_payload))

    return binary_payload


def send_to_printer(data: list[str], sock) -> bool:
    """Send encoded label data. *data* is joined with SEPARATOR for one print job."""

    items = [str(item).strip() for item in data if str(item).strip()]
    if not items:
        print("print skipped: empty list")
        return False

    print(f"sending {items!r} to printer ... ")


    # text = SEPARATOR.join(items)
    # print_word_codes(text)

    try:
        binary_payload = send_text_via_ready_socket(items, sock)
        print(f"sent {len(binary_payload)} bytes ... done")
        return True
    except (OSError, ValueError) as error:
        print(f"print error: {error}")
        print("payload was not sent")
        return False
