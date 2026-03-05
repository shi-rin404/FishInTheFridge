import random
import string

ALLOWED_CHARS = (string.digits + string.ascii_uppercase).encode("ascii")
def generate_session_title() -> str:
    return ''.join(chr(random.choice(ALLOWED_CHARS)) for _ in range(16))

# if __name__ == "__main__":
#     print(generate_session_title())