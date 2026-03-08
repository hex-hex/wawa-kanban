from typing import Tuple, Dict


def parse_frontmatter(content: str) -> Tuple[Dict, str]:
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    fm_text = parts[1].strip()
    frontmatter = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    body = parts[2].strip() if len(parts) > 2 else ""
    return frontmatter, body


def serialize_frontmatter_and_body(frontmatter: Dict, body: str) -> str:
    """Serialize frontmatter dict and body back to markdown file content."""
    lines = ["---"]
    for k, v in frontmatter.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    return "\n".join(lines)
