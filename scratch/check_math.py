import os
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_dir = r"d:\www\dau-tay-hoc-lop-1\on-thi-timo\public\database"

def parse_math_expr(expr):
    # Normalize expression
    expr = expr.replace('−', '-').replace('–', '-').replace('×', '*').replace('÷', '/').replace(':', '/')
    # Handle equation style with □
    # e.g., "13 + □ = 36"
    # we want to find the value of □
    if '□' in expr or '?' in expr or '=' in expr:
        # replace box with x
        expr = expr.replace('□', 'x').replace('?', 'x')
        # if there is '='
        if '=' in expr:
            parts = expr.split('=')
            if len(parts) == 2:
                left, right = parts[0].strip(), parts[1].strip()
                # Find which side has x
                return left, right
    return None

def evaluate_simple_math(content):
    # e.g. "13 + 6 - 15 = ?"
    # "13 + □ = 36"
    # "4 + 4 + 4 + 1 = ?"
    content = content.strip()
    # Replace unicode minus and spaces
    clean = content.replace('−', '-').replace('–', '-').replace(' ', '')
    # Check if format is "EXPR=?" or "?=EXPR"
    if clean.endswith('=?'):
        expr = clean[:-2]
        try:
            val = eval(expr)
            return val
        except Exception:
            pass
    elif clean.startswith('?='):
        expr = clean[2:]
        try:
            val = eval(expr)
            return val
        except Exception:
            pass
    # Format "EXPR=VAL" where EXPR has a □
    # E.g. "13+□=36" -> 36 - 13 = 23
    # E.g. "□-12=24" -> 24 + 12 = 36
    # E.g. "15-□=7" -> 15 - 7 = 8
    # E.g. "□+15=20" -> 20 - 15 = 5
    if '□' in clean and '=' in clean:
        parts = clean.split('=')
        if len(parts) == 2:
            left, right = parts[0], parts[1]
            if '□' in left:
                # We need to solve left = right
                # Try simple replacement of □ with variable
                # Assuming single □
                # We can iterate through integers 0 to 100 to see if it matches
                for val in range(-100, 1000):
                    test_expr = left.replace('□', str(val))
                    try:
                        if eval(test_expr) == eval(right):
                            return val
                    except Exception:
                        pass
            elif '□' in right:
                for val in range(-100, 1000):
                    test_expr = right.replace('□', str(val))
                    try:
                        if eval(left) == eval(test_expr):
                            return val
                    except Exception:
                        pass
    return None

results = []

for root, dirs, files in os.walk(db_dir):
    category = os.path.basename(root)
    for file in files:
        if file.endswith('.json'):
            sub_cat = file.replace('.json', '')
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    item_id = item.get("id")
                    stem_en = item.get("stem", {}).get("en", "")
                    stem_vi = item.get("stem", {}).get("vi", "")
                    figure = item.get("figure", {})
                    choices = item.get("choices", [])
                    answer_key = item.get("answer", {}).get("key")
                    
                    # Find matching choice value
                    correct_choice_val = None
                    for c in choices:
                        if c.get("id") == answer_key:
                            correct_choice_val = c.get("en") or c.get("vi")
                            break
                    
                    # Try to evaluate mathematically if figure is text
                    computed = None
                    figure_content = ""
                    if isinstance(figure, dict) and figure.get("renderer") == "text":
                        figure_content = figure.get("params", {}).get("content", "")
                        computed = evaluate_simple_math(figure_content)
                    
                    results.append({
                        "category": category,
                        "sub_cat": sub_cat,
                        "id": item_id,
                        "stem_en": stem_en,
                        "stem_vi": stem_vi,
                        "figure_renderer": figure.get("renderer") if isinstance(figure, dict) else None,
                        "figure_content": figure_content,
                        "figure_raw": figure,
                        "choices": choices,
                        "answer_key": answer_key,
                        "correct_choice_val": correct_choice_val,
                        "computed": computed,
                        "full_item": item
                    })

# Print items with text math content where computed != correct_choice_val
mismatches = []
for r in results:
    if r["computed"] is not None and r["correct_choice_val"] is not None:
        try:
            choice_int = int(r["correct_choice_val"])
            if int(r["computed"]) != choice_int:
                mismatches.append(r)
        except ValueError:
            # Choice might not be an integer, e.g. text
            mismatches.append(r)

print(f"Total arithmetic text checked: {len([r for r in results if r['computed'] is not None])}")
print(f"Total arithmetic mismatches found: {len(mismatches)}")
for m in mismatches:
    print(f"ID: {m['id']} ({m['category']}/{m['sub_cat']})")
    print(f"  Content: {m['figure_content']}")
    print(f"  Computed: {m['computed']}")
    print(f"  Answer Key: {m['answer_key']} -> Value: {m['correct_choice_val']}")
    print(f"  Stem VI: {m['stem_vi']}")
    print("---")
