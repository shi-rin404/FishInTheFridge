from .modder import skin_modder

def deapply_mod(placeholder: str):
    skin_modder.patch(placeholder, placeholder, pad=False)