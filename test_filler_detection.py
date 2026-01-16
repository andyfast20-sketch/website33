import os
import json

def _global_fillers_dir(voice_id: str) -> str:
    base_dir = "filler_audios"
    if voice_id == "sarah":
        return base_dir
    return os.path.join(base_dir, voice_id)

def _global_filler_existing_path(filler_dir: str, filler_num: int):
    for ext in (".wav", ".mp3", ".mpeg"):
        p = os.path.join(filler_dir, f"filler_{filler_num}{ext}")
        if os.path.exists(p):
            return p
    return None

def _load_global_filler_meta(filler_dir: str, filler_num: int):
    try:
        meta_path = os.path.join(filler_dir, f"filler_{filler_num}.json")
        if not os.path.exists(meta_path):
            return {}
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

# Test finding fillers
voice_id = "sarah"
filler_dir = _global_fillers_dir(voice_id)
print(f"Filler directory: {filler_dir}")
print(f"Directory exists: {os.path.exists(filler_dir)}\n")

found_fillers = []
for i in range(1, 31):
    path = _global_filler_existing_path(filler_dir, i)
    if path:
        meta = _load_global_filler_meta(filler_dir, i)
        size = meta.get("size", "unknown")
        phrase = meta.get("phrase", "no phrase")[:40]
        found_fillers.append((i, path, size, phrase))

print(f"Found {len(found_fillers)} filler audio files:")
for num, path, size, phrase in found_fillers[:10]:
    print(f"  {num}. [{size}] {phrase}")

# Group by size
small = [f for f in found_fillers if f[2] == "small"]
medium = [f for f in found_fillers if f[2] == "medium"]
large = [f for f in found_fillers if f[2] == "large"]
unknown = [f for f in found_fillers if f[2] not in ["small", "medium", "large"]]

print(f"\nBy size:")
print(f"  Small: {len(small)}")
print(f"  Medium: {len(medium)}")
print(f"  Large: {len(large)}")
print(f"  Unknown/Untagged: {len(unknown)}")
