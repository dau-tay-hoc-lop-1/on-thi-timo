import os
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Re-run audit and print findings that are not translation word mismatches,
# and check if translation mismatches are real.
db_dir = r"d:\www\dau-tay-hoc-lop-1\on-thi-timo\public\database"

def clean_math(expr):
    expr = expr.replace('−', '-').replace('–', '-').replace('—', '-').replace('×', '*').replace('÷', '/').replace(':', '/')
    expr = expr.replace(' ', '')
    return expr

def eval_expr(expr):
    expr = clean_math(expr)
    if re.match(r'^[0-9\+\-\*\/\(\)]+$', expr):
        try:
            return eval(expr)
        except Exception:
            return None
    return None

def extract_and_solve_math(text):
    text_clean = text.replace(' ', '')
    m1 = re.search(r'([0-9\+\-\*\/\(\)\u2212\u2013]+)=\?', text_clean)
    if m1:
        val = eval_expr(m1.group(1))
        if val is not None:
            return val
            
    eq_text = text_clean
    for blank in ['___', '__', '_', '□', '?', 'x']:
         eq_text = eq_text.replace(blank, 'X')
    
    if 'X' in eq_text and '=' in eq_text:
        parts = eq_text.split('=')
        if len(parts) == 2:
            left, right = parts[0], parts[1]
            for val in range(-100, 1001):
                try:
                    left_eval = eval(clean_math(left.replace('X', str(val)))) if 'X' in left else eval(clean_math(left))
                    right_eval = eval(clean_math(right.replace('X', str(val)))) if 'X' in right else eval(clean_math(right))
                    if left_eval == right_eval:
                        return val
                except Exception:
                    continue
                    
    matches = re.findall(r'[0-9]+(?:\s*[\+\-\u2212\u2013]\s*[0-9]+)+', text)
    if matches:
        longest_match = max(matches, key=len)
        val = eval_expr(longest_match)
        if val is not None:
            return val
            
    return None

word_to_num = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, 'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10
}

def get_numbers_and_words(text):
    # Extract all digits
    nums = [int(n) for n in re.findall(r'\d+', text)]
    # Extract word equivalents
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    for w in words:
        if w in word_to_num:
            nums.append(word_to_num[w])
    return sorted(list(set(nums)))

findings = []

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
                    answer = item.get("answer", {})
                    answer_key = answer.get("key")
                    
                    if not item_id:
                        continue
                    
                    # 1. Missing answer key
                    if not answer_key:
                        findings.append(("MISSING_ANSWER_KEY", item_id, f"{category}/{file}", "Missing answer key", item))
                        continue
                    
                    # 2. Invalid answer key
                    choice_ids = [c.get("id") for c in choices]
                    if answer_key not in choice_ids:
                        findings.append(("INVALID_ANSWER_KEY", item_id, f"{category}/{file}", f"Answer key '{answer_key}' not in choices {choice_ids}", item))
                    
                    # 3. Duplicate choices
                    choice_vals = [c.get("en") or c.get("vi") for c in choices]
                    if len(choice_vals) != len(set(choice_vals)):
                        findings.append(("DUPLICATE_CHOICES", item_id, f"{category}/{file}", f"Duplicate choices values: {choice_vals}", item))
                    
                    # 4. Translation mismatch (refined)
                    nums_en = get_numbers_and_words(stem_en)
                    # For VI stem, we also convert some common word numbers
                    vi_word_to_num = {'một': 1, 'hai': 2, 'ba': 3, 'bốn': 4, 'năm': 5, 'sáu': 6, 'bảy': 7, 'tám': 8, 'chín': 9, 'mười': 10, 'nhất': 1, 'nhì': 2}
                    nums_vi = [int(n) for n in re.findall(r'\d+', stem_vi)]
                    vi_words = re.findall(r'\b\w+\b', stem_vi.lower())
                    for w in vi_words:
                        if w in vi_word_to_num:
                            nums_vi.append(vi_word_to_num[w])
                    nums_vi = sorted(list(set(nums_vi)))
                    
                    # If sets of numbers are not equal, check if they are actually different
                    if nums_en != nums_vi:
                        # Allow difference if it's just about 3 vs 3-digit where 3 is matched anyway
                        # but check if there's a serious number difference, e.g. different digits in the problem
                        # Let's filter out if the difference is very small (like just containing 3 or 4)
                        # We only flag if they are significantly different
                        diff = set(nums_en).symmetric_difference(set(nums_vi))
                        # Ignore differences that only contain 1, 2, 3, 4 (often from "1st", "2nd", "3-digit", "4 steps" etc.)
                        significant_diff = [d for d in diff if d > 4]
                        if significant_diff:
                            findings.append(("TRANSLATION_NUM_MISMATCH", item_id, f"{category}/{file}", f"Significant number mismatch EN: {nums_en} vs VI: {nums_vi}.\n  EN: '{stem_en}'\n  VI: '{stem_vi}'", item))
                    
                    # 5. Math mismatch
                    computed = extract_and_solve_math(stem_en)
                    if computed is None:
                        computed = extract_and_solve_math(stem_vi)
                    if computed is None and isinstance(figure, dict) and figure.get("renderer") == "text":
                        fig_content = figure.get("params", {}).get("content", "")
                        computed = extract_and_solve_math(fig_content)
                    
                    correct_choice_val = None
                    for c in choices:
                        if c.get("id") == answer_key:
                            correct_choice_val = c.get("en") or c.get("vi")
                            break
                            
                    if computed is not None and correct_choice_val is not None:
                        val_str = str(correct_choice_val).lower().strip()
                        if val_str in ['even', 'chẵn']:
                            is_correct = (computed % 2 == 0)
                        elif val_str in ['odd', 'lẻ']:
                            is_correct = (computed % 2 != 0)
                        else:
                            try:
                                is_correct = (int(computed) == int(correct_choice_val))
                            except ValueError:
                                is_correct = True
                        
                        if not is_correct:
                            findings.append(("MATH_MISMATCH", item_id, f"{category}/{file}", f"Math eval mismatch: computed {computed}, answer key {answer_key} is '{correct_choice_val}'.\n  EN: '{stem_en}'\n  VI: '{stem_vi}'\n  Figure: {figure}", item))

# Print grouped findings
by_type = {}
for ftype, item_id, filepath, msg, item in findings:
    by_type.setdefault(ftype, []).append((item_id, filepath, msg, item))

for ftype, items in by_type.items():
    print(f"=== TYPE: {ftype} ({len(items)}) ===")
    for item_id, filepath, msg, item in items:
        print(f"ID: {item_id} ({filepath})")
        print(f"  {msg}")
        print()

