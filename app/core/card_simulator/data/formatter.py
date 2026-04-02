def component_to_str(name:str, **fields) -> str:
    res = f"[{name}]"
    for key, value in fields.items():
        res += " :: [" + repr(key) + "=" + repr(value) + "]"
    return res