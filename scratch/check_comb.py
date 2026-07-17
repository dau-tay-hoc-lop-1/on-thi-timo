import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = r"d:\www\dau-tay-hoc-lop-1\on-thi-timo\public\database"

for file in ["heat/combinatorics.json", "preliminary/combinatorics.json"]:
    with open(os.path.join(db_path, file), 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"=== {file} ===")
        for idx, item in enumerate(data[:15]): # check first 15
            print(f"{item.get('id')}: {item.get('stem', {}).get('vi')}")
            # print choices and answer
            choices_str = ", ".join([f"{c.get('id')}:{c.get('en') or c.get('vi')}" for c in item.get('choices', [])])
            print(f"  Choices: [{choices_str}] | Ans: {item.get('answer', {}).get('key')}")
        print("-" * 50)
