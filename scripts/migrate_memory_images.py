from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
MEMORIES = ROOT / "_memories"
TARGET_DIR = ROOT / "images" / "memory"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".heic"}
SLUGS = {
    "ApplePark.md": "apple-park",
    "Cairns.md": "cairns",
    "NewYork.md": "new-york",
    "NY.md": "new-york-2",
    "SanFrancisco.md": "san-francisco",
    "SanJose.md": "san-jose",
    "kyoto.md": "kyoto",
    "yumeshima.md": "yumeshima",
}
SRC_PATTERN = re.compile(r'(?m)^(\s*-\s+src:\s*")([^"]+)("\s*)$')
IMAGE_PATTERN = re.compile(r'(?m)^(image:\s*")([^"]+)("\s*)$')
UNICODE_DASHES = str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-"})


def slugify(value: str) -> str:
    value = value.lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9-]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "memory"


def normalized_extension(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return ".jpg"
    return suffix if suffix in IMAGE_EXTENSIONS else ".jpg"


def target_path(slug: str, index: int, source: Path) -> Path:
    return TARGET_DIR / f"{slug}-{index:02d}{normalized_extension(source)}"


def move_or_copy(source: Path, target: Path, moved_sources: dict[Path, Path]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise RuntimeError(f"Target already exists: {target.relative_to(ROOT)}")

    if source in moved_sources:
        shutil.copy2(moved_sources[source], target)
        return

    if not source.exists():
        raise FileNotFoundError(f"Referenced image not found: {source.relative_to(ROOT)}")

    shutil.move(str(source), str(target))
    moved_sources[source] = target


def cleanup_directory(directory: Path, slug: str, next_index: int, moved_sources: dict[Path, Path]) -> int:
    if not directory.exists() or directory == TARGET_DIR:
        return next_index

    for remaining in sorted(directory.rglob("*")):
        if not remaining.is_file():
            continue
        if remaining.name == ".DS_Store":
            remaining.unlink()
            continue
        if remaining.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        next_index += 1
        target = target_path(slug, next_index, remaining)
        move_or_copy(remaining, target, moved_sources)

    for child in sorted(directory.rglob("*"), reverse=True):
        if child.is_dir() and not any(child.iterdir()):
            child.rmdir()
    if directory.exists() and not any(directory.iterdir()):
        directory.rmdir()
    return next_index


def migrate_memory(memory_file: Path) -> bool:
    original = memory_file.read_text(encoding="utf-8")
    matches = list(SRC_PATTERN.finditer(original))
    legacy = [match for match in matches if not match.group(2).startswith("/images/memory/")]
    if not legacy:
        normalized = original.translate(UNICODE_DASHES)
        if normalized != original:
            memory_file.write_text(normalized, encoding="utf-8")
            return True
        return False

    slug = SLUGS.get(memory_file.name, slugify(memory_file.stem))
    moved_sources: dict[Path, Path] = {}
    source_directories: set[Path] = set()
    photo_index = 0
    first_target_url = ""

    def replace_src(match: re.Match[str]) -> str:
        nonlocal photo_index, first_target_url
        current_url = match.group(2)
        photo_index += 1

        if current_url.startswith("/images/memory/"):
            target_url = current_url
        else:
            source = ROOT / unquote(current_url.lstrip("/"))
            source_directories.add(source.parent)
            target = target_path(slug, photo_index, source)
            move_or_copy(source, target, moved_sources)
            target_url = "/" + target.relative_to(ROOT).as_posix()

        if not first_target_url:
            first_target_url = target_url
        return match.group(1) + target_url + match.group(3)

    updated = SRC_PATTERN.sub(replace_src, original)

    for directory in sorted(source_directories):
        photo_index = cleanup_directory(directory, slug, photo_index, moved_sources)

    if first_target_url:
        if IMAGE_PATTERN.search(updated):
            updated = IMAGE_PATTERN.sub(lambda match: match.group(1) + first_target_url + match.group(3), updated, count=1)
        else:
            updated = updated.replace("photos:\n", f'image: "{first_target_url}"\nphotos:\n', 1)

    updated = updated.translate(UNICODE_DASHES)
    memory_file.write_text(updated, encoding="utf-8")
    return True


def validate() -> None:
    failures: list[str] = []
    for memory_file in sorted(MEMORIES.glob("*.md")):
        text = memory_file.read_text(encoding="utf-8")
        for match in SRC_PATTERN.finditer(text):
            url = match.group(2)
            if not url.startswith("/images/memory/"):
                failures.append(f"Legacy path remains in {memory_file.name}: {url}")
                continue
            referenced = ROOT / unquote(url.lstrip("/"))
            if not referenced.exists():
                failures.append(f"Missing image in {memory_file.name}: {url}")
    if failures:
        raise RuntimeError("\n".join(failures))


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    changed = []
    for memory_file in sorted(MEMORIES.glob("*.md")):
        if migrate_memory(memory_file):
            changed.append(memory_file.name)
    validate()
    print("Migrated:", ", ".join(changed) if changed else "none")


if __name__ == "__main__":
    main()
