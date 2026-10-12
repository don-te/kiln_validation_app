#!/usr/bin/env python3
"""
Restore temporal validation results from validation_results.csv backup.
Merges CSV data with any existing validated entries and updates both:
1. /home/rishabh.mondal/Brick-Kilns-project/ijcai_2025_kilns/temporal-analysis/streamlit_app/temporal_validation_results.json
2. ./temporal_validation_results.json
"""

import sys
import io
import csv
import json
import shutil
import fcntl
from pathlib import Path
from datetime import datetime

DEFAULT_CSV = Path(__file__).resolve().parent / "validation_results.csv"

# Target JSON paths
TARGET_PATHS = [
    Path("/home/thejastg/validation_app/temporal_validation_results.json"),
]

def parse_bool(val):
    if val is None or val == "":
        return False
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes", "t")

def parse_year(val):
    if not val:
        return None
    try:
        y = int(float(val))
        return y if y > 0 else None
    except:
        return None

def parse_float(val):
    try:
        return float(val)
    except:
        return 0.0

def load_existing_json(filepath):
    p = Path(filepath)
    if not p.exists():
        return {}
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('validated', {})
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return {}

def parse_csv_reader(reader):
    validated = {}
    if not reader.fieldnames:
        return {}
    
    first_col = reader.fieldnames[0]
    
    for row in reader:
        loc_key = (row.get(first_col) or "").strip()
        if not loc_key or "_" not in loc_key:
            lat = row.get("lat")
            lon = row.get("lon")
            if lat and lon:
                loc_key = f"{lat}_{lon}"
            else:
                continue
        
        lat_val = parse_float(row.get("lat")) if row.get("lat") else parse_float(loc_key.split("_")[0])
        lon_val = parse_float(row.get("lon")) if row.get("lon") else parse_float(loc_key.split("_")[1])

        entry = {
            "lat": lat_val,
            "lon": lon_val,
            "validator": row.get("validator", "Unknown"),
            "presence": parse_bool(row.get("presence")),
            "appearance_year": parse_year(row.get("appearance_year")),
            "kiln_type": row.get("kiln_type", "FCBK"),
            "transition_year": parse_year(row.get("transition_year")),
            "demolished": parse_bool(row.get("demolished")),
            "demolished_year": parse_year(row.get("demolished_year")),
            "model_correct": row.get("model_correct", "Yes"),
            "needs_expert_review": parse_bool(row.get("needs_expert_review")),
            "notes": (row.get("notes") or "").strip(),
            "timestamp": row.get("timestamp", "")
        }
        validated[loc_key] = entry
        
    return validated

def parse_csv(csv_path):
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        return parse_csv_reader(reader)

def parse_csv_text(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    return parse_csv_reader(reader)

def merge_and_save(csv_entries, target_paths=TARGET_PATHS):
    if not csv_entries:
        return False, "No valid entries found in CSV data."

    # Collect existing entries from target files to preserve newly validated points
    merged = {}
    for target in target_paths:
        existing = load_existing_json(target)
        if existing:
            for k, v in existing.items():
                merged[k] = v

    # Merge CSV entries (newer timestamp wins if both have timestamps)
    for k, v in csv_entries.items():
        if k in merged:
            t_csv = v.get("timestamp", "")
            t_exist = merged[k].get("timestamp", "")
            if t_exist and t_csv and t_exist > t_csv:
                continue
        merged[k] = v

    payload = {"validated": merged}
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    saved_paths = []
    for target in target_paths:
        try:
            target = Path(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                backup_path = target.with_suffix(f".json.bak_{ts}")
                shutil.copy2(target, backup_path)
            with open(target, "w", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(payload, f, indent=2, default=str)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            saved_paths.append(str(target))
        except Exception as e:
            print(f"Warning: Could not save to {target}: {e}")

    return True, f"Successfully restored {len(merged):,} entries across {len(saved_paths)} locations."

def restore(csv_path_str):
    csv_path = Path(csv_path_str)
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found at {csv_path}")
        return False

    print(f"📖 Reading backup from: {csv_path}")
    csv_entries = parse_csv(csv_path)
    print(f"✓ Found {len(csv_entries):,} entries in CSV.")

    success, msg = merge_and_save(csv_entries)
    print(msg)
    return success

if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    elif DEFAULT_CSV.exists():
        csv_file = str(DEFAULT_CSV)
    else:
        print("Usage: python3 restore_from_csv.py [path_to_validation_results.csv]")
        print("\nNote: You can place 'validation_results.csv' in this folder and re-run,")
        print("or pass the full path to your downloaded CSV file.")
        server_fallback = Path("/home/rishabh.mondal/Brick-Kilns-project/ijcai_2025_kilns/temporal-analysis/aaai_2027/validation_results.csv")
        if server_fallback.exists():
            print(f"\nTip: An older server backup with 16,880 rows was found at:\n  {server_fallback}")
            print("To restore that specifically, run:")
            print(f"  python3 restore_from_csv.py \"{server_fallback}\"")
        sys.exit(1)

    restore(csv_file)
