import os
import json
import re

db_dir = r"d:\www\dau-tay-hoc-lop-1\on-thi-timo\public\database"

for root, dirs, files in os.walk(db_dir):
    for file in files:
        if file.endswith('.json'):
            path = os.path.join(root, file)
            print(f"File: {os.path.relpath(path, db_dir)}")
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(f"  Error parsing json: {e}")
                    continue
                
                print(f"  Total items: {len(data)}")
                renderers = set()
                for idx, item in enumerate(data):
                    renderer = item.get("figure", {}).get("renderer") if isinstance(item.get("figure"), dict) else None
                    if renderer:
                        renderers.add(renderer)
                print(f"  Renderers: {renderers}")
