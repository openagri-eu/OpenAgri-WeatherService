import base64
import struct
import copy


def deepcopy_dict(d: dict) -> dict:
    return copy.deepcopy(d)

def number_to_base32_string(num: float) -> str:
    '''
    Explanation:

    Struct Packing: struct.pack('>q', num) converts the integer number to a byte array in big-endian format using the >q format (signed long long, 8 bytes).
    Base32 Encoding: base64.b32encode encodes the byte array to a base-32 encoded bytes object.
    Decoding: .decode('utf-8') converts the bytes object to a string.
    Stripping Equals: .rstrip('=') removes any trailing equal signs used for padding in base-32 encoding.
    '''
    # Convert the number to a byte array
    byte_array = struct.pack('>q', num)  # Use '>q' for long long (8 bytes)
    
    # Encode the byte array using base32
    base32_encoded = base64.b32encode(byte_array).decode('utf-8').rstrip('=')
    
    return base32_encoded