import os
import glob
import shutil
from pathlib import Path

def consolidate_sovereign_paths():
    """
    Audits skills and migrates legacy data paths (~/.janus/, ~/.claude/frames/)
    to the unified root ~/.abraxas/.
    """
    print("🚀 Starting Sovereign Path Consolidation...")
    
    legacy_paths = ["~/.janus/", "~/.claude/frames/"]
    target_root = Path.home() / ".abraxas"
    target_root.mkdir(parents=True, exist_ok=True)

    # 1. Physical Migration of existing directories (if any)
    for leg_path_str in legacy_paths:
        leg_path = Path(os.path.expanduser(leg_path_str))
        if leg_path.exists():
            print(f"Moving {leg_path} to {target_root}")
            # Simple move logic (avoiding overwrites)
            folder_name = leg_path.name if leg_path.name else "legacy_data"
            dest = target_root / folder_name
            try:
                shutil.move(str(leg_path), str(dest))
                print(f"✅ Migrated {leg_path_str} -> {dest}")
            except Exception as e:
                print(f"❌ Failed to move {leg_path_str}: {e}")
        else:
            print(f"ℹ️ Legacy path {leg_path_str} not found. Skipping physical move.")

    # 2. Logic Audit: Search for hardcoded legacy paths in the codebase
    print("\n🔍 Auditing codebase for legacy path references...")
    found_legacy = False
    files_to_check = glob.glob("skills/**/*.py", recursive=True) # Prioritize Python logic
    
    for file_path in files_to_check:
        with open(file_path, 'r') as f:
            content = f.read()
            for leg in legacy_paths:
                if leg.strip(" /") in content:
                    print(f"⚠️ Found legacy reference in {file_path}: {leg}")
                    found_legacy = True
    
    if not found_legacy:
        print("🌟 Zero legacy path references found in skill logic.")
    else:
        print("❌ Legacy references detected. Manual update required.")

if __name__ == "__main__":
    consolidate_sovereign_paths()
