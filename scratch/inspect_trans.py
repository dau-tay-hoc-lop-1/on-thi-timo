import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = r"d:\www\dau-tay-hoc-lop-1\on-thi-timo\public\database"

mismatches = [
    ("heat/geometry.json", "GH03"),
    ("heat/geometry.json", "GH04"),
    ("heat/geometry.json", "GH07"),
    ("heat/geometry.json", "GH19"),
    ("heat/logic-thinking.json", "LH01"),
    ("heat/logic-thinking.json", "LH03"),
    ("heat/logic-thinking.json", "LH05"),
    ("heat/logic-thinking.json", "LH06"),
    ("heat/logic-thinking.json", "LH38"),
    ("preliminary/logic-thinking.json", "L01"),
    ("preliminary/logic-thinking.json", "L05"),
    ("preliminary/logic-thinking.json", "L27"),
    ("preliminary/logic-thinking.json", "L32"),
    ("preliminary/logic-thinking.json", "L33"),
    ("preliminary/logic-thinking.json", "L39"),
]

for file_rel, q_id in mismatches:
    with open(f"{db_path}/{file_rel}", 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            if item.get("id") == q_id:
                print(f"=== {q_id} ===")
                print(f"  EN: {item.get('stem', {}).get('en')}")
                print(f"  VI: {item.get('stem', {}).get('vi')}")
                print(f"  Choices: {item.get('choices')}")
                print(f"  Answer: {item.get('answer')}")
                print()
