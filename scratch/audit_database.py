import os
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_dir = r"d:\www\dau-tay-hoc-lop-1\on-thi-timo\public\database"

def clean_math(expr):
    # normalize characters
    expr = expr.replace('−', '-').replace('–', '-').replace('—', '-').replace('×', '*').replace('÷', '/').replace(':', '/')
    # remove spaces
    expr = expr.replace(' ', '')
    return expr

def eval_expr(expr):
    expr = clean_math(expr)
    # Check if only contains digits and +, -, *, /
    if re.match(r'^[0-9\+\-\*\/\(\)]+$', expr):
        try:
            return eval(expr)
        except Exception:
            return None
    return None

def extract_and_solve_math(text):
    # Look for patterns like "13 + 6 - 15 = ?" or "2 + 4 + 6 + 8 + 10"
    # Find any sequences of numbers and operators that end with = ? or = __ or just are math expressions.
    # Let's match typical Grade 1 TIMO arithmetic patterns:
    # 1. "18 - __ = 4" or "18 - _ = 4" or "18 - □ = 4"
    text_clean = text.replace(' ', '')
    
    # Try to extract "A + B - C = ?" or similar
    # Match something like "13+6-15=?"
    m1 = re.search(r'([0-9\+\-\*\/\(\)\u2212\u2013]+)=\?', text_clean)
    if m1:
        val = eval_expr(m1.group(1))
        if val is not None:
            return val
            
    # Match something like "18-___=4" or "18-□=4" or "18-x=4" or "13+□=36"
    # Look for an equation with a single missing box/blank/variable
    # e.g., "18-[box]=4"
    # Replace the blank/box/underlines with 'X'
    eq_text = text_clean
    for blank in ['___', '__', '_', '□', '?', 'x']:
         eq_text = eq_text.replace(blank, 'X')
    
    # Check if it looks like "EXPR=EXPR" containing one X
    if 'X' in eq_text and '=' in eq_text:
        parts = eq_text.split('=')
        if len(parts) == 2:
            left, right = parts[0], parts[1]
            # Try substituting X with values from -100 to 1000
            for val in range(-100, 1001):
                try:
                    left_eval = eval(clean_math(left.replace('X', str(val)))) if 'X' in left else eval(clean_math(left))
                    right_eval = eval(clean_math(right.replace('X', str(val)))) if 'X' in right else eval(clean_math(right))
                    if left_eval == right_eval:
                        return val
                except Exception:
                    continue
                    
    # Try just finding the last mathematical expression of numbers if it ends the sentence
    # e.g. "Find the value of 2 + 4 + 6 + 8 + 10." -> clean up and try to find a sequence of numbers and operators
    # Let's match something like: "2+4+6+8+10"
    # We can search for sequences of digits and operators
    # Let's look for standard sequences:
    matches = re.findall(r'[0-9]+(?:\s*[\+\-\u2212\u2013]\s*[0-9]+)+', text)
    if matches:
        # Take the longest match
        longest_match = max(matches, key=len)
        val = eval_expr(longest_match)
        if val is not None:
            return val
            
    return None

findings = []

for root, dirs, files in os.walk(db_dir):
    category = os.path.basename(root)
    for file in files:
        if file.endswith('.json'):
            sub_cat = file.replace('.json', '')
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    findings.append({
                        "type": "JSON_ERROR",
                        "file": os.path.relpath(path, db_dir),
                        "message": f"Invalid JSON syntax: {str(e)}"
                    })
                    continue
                
                for item in data:
                    item_id = item.get("id")
                    stem_en = item.get("stem", {}).get("en", "")
                    stem_vi = item.get("stem", {}).get("vi", "")
                    figure = item.get("figure", {})
                    choices = item.get("choices", [])
                    answer = item.get("answer", {})
                    answer_key = answer.get("key")
                    
                    # 1. Check if ID exists
                    if not item_id:
                        findings.append({
                            "type": "MISSING_ID",
                            "file": os.path.relpath(path, db_dir),
                            "message": f"Item has no ID: {item}"
                        })
                        continue
                    
                    # 2. Check if answer key is valid
                    if not answer_key:
                        findings.append({
                            "type": "MISSING_ANSWER_KEY",
                            "file": os.path.relpath(path, db_dir),
                            "id": item_id,
                            "message": "Answer key is missing"
                        })
                    
                    # 3. Check choices validity and find correct choice value
                    choice_ids = [c.get("id") for c in choices]
                    if answer_key and answer_key not in choice_ids:
                        findings.append({
                            "type": "INVALID_ANSWER_KEY",
                            "file": os.path.relpath(path, db_dir),
                            "id": item_id,
                            "message": f"Answer key '{answer_key}' is not in choices {choice_ids}"
                        })
                    
                    correct_choice_val = None
                    for c in choices:
                        if c.get("id") == answer_key:
                            correct_choice_val = c.get("en") or c.get("vi")
                            break
                    
                    # Check for duplicate choices
                    choice_vals = [c.get("en") or c.get("vi") for c in choices]
                    if len(choice_vals) != len(set(choice_vals)):
                        findings.append({
                            "type": "DUPLICATE_CHOICES",
                            "file": os.path.relpath(path, db_dir),
                            "id": item_id,
                            "message": f"Duplicate choices values: {choice_vals}"
                        })
                    
                    # 4. Check for mismatches in numbers between EN and VI stems
                    # Find all numbers in EN stem and VI stem
                    nums_en = [int(n) for n in re.findall(r'\d+', stem_en)]
                    nums_vi = [int(n) for n in re.findall(r'\d+', stem_vi)]
                    if sorted(nums_en) != sorted(nums_vi):
                        findings.append({
                            "type": "TRANSLATION_NUM_MISMATCH",
                            "file": os.path.relpath(path, db_dir),
                            "id": item_id,
                            "message": f"Numbers mismatch between EN and VI stems. EN: {nums_en}, VI: {nums_vi}. EN: '{stem_en}', VI: '{stem_vi}'"
                        })
                    
                    # 5. Evaluate arithmetic problems
                    # Check math in stem first, then in figure
                    computed = extract_and_solve_math(stem_en)
                    if computed is None:
                        computed = extract_and_solve_math(stem_vi)
                    if computed is None and isinstance(figure, dict) and figure.get("renderer") == "text":
                        fig_content = figure.get("params", {}).get("content", "")
                        computed = extract_and_solve_math(fig_content)
                        
                    if computed is not None and correct_choice_val is not None:
                        # try to match with correct choice
                        # special cases for Even/Odd answers
                        val_str = str(correct_choice_val).lower().strip()
                        if val_str in ['even', 'chẵn']:
                            is_correct = (computed % 2 == 0)
                        elif val_str in ['odd', 'lẻ']:
                            is_correct = (computed % 2 != 0)
                        else:
                            try:
                                is_correct = (int(computed) == int(correct_choice_val))
                            except ValueError:
                                # Not an integer comparison
                                is_correct = True # skip non-integer choices unless we can parse
                        
                        if not is_correct:
                            findings.append({
                                "type": "MATH_MISMATCH",
                                "file": os.path.relpath(path, db_dir),
                                "id": item_id,
                                "message": f"Math evaluation mismatch. Formula computed to {computed}, but correct choice '{answer_key}' value is '{correct_choice_val}'. Stems: EN='{stem_en}' / VI='{stem_vi}', Figure: {figure}"
                            })

print(f"Total findings: {len(findings)}")
for f in findings:
    print(f"[{f['type']}] File: {f['file']}, ID: {f.get('id', 'N/A')}")
    print(f"  {f['message']}")
    print("-" * 40)
