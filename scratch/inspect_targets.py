import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = r"d:\www\dau-tay-hoc-lop-1\on-thi-timo\public\database"

targets = [
    ("heat/number-theory.json", "NH14"),
    ("heat/number-theory.json", "NH16"),
    ("heat/number-theory.json", "NH31"),
    ("heat/number-theory.json", "NH32"),
    ("heat/number-theory.json", "NH38"),
    ("heat/number-theory.json", "NH40"),
    ("preliminary/number-theory.json", "N02"),
    ("preliminary/number-theory.json", "N05"),
    ("preliminary/arithmetic.json", "A33")
]

for file_rel, q_id in targets:
    with open(f"{db_path}/{file_rel}", 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            if item.get("id") == q_id:
                print(f"=== {q_id} in {file_rel} ===")
                print(json.dumps(item, ensure_ascii=False, indent=2))
                print()
