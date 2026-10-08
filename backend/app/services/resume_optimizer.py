from ..services.resume_parser import normalize_resume_text


MAX_PROFILE_INPUT_CHARS = 18000


def optimize_resume_text(text: str) -> str:
    cleaned = normalize_resume_text(text)
    seen: set[str] = set()
    unique_lines: list[str] = []
    for line in cleaned.splitlines():
        key = line.casefold()
        if key not in seen:
            seen.add(key)
            unique_lines.append(line)
    compact = "\n".join(unique_lines)
    if len(compact) <= MAX_PROFILE_INPUT_CHARS:
        return compact
    half_limit = MAX_PROFILE_INPUT_CHARS // 2
    return f"{compact[:half_limit]}\n\n[Resume text shortened locally]\n\n{compact[-half_limit:]}"