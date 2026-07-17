import os
import json
import re
import sys

db_dir = r"d:\www\dau-tay-hoc-lop-1\on-thi-timo\public\database"
artifact_path = r"C:\Users\Windows\.gemini\antigravity-ide\brain\0dcbf6c8-c748-49f5-a50a-aba8dd9d7992\findings.md"

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
                        "file": f"{category}/{file}",
                        "id": "N/A",
                        "message": f"Cú pháp JSON lỗi: {str(e)}",
                        "item": None
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
                    
                    if not item_id:
                        findings.append({
                            "type": "MISSING_ID",
                            "file": f"{category}/{file}",
                            "id": "N/A",
                            "message": f"Câu hỏi không có ID: {item}",
                            "item": item
                        })
                        continue
                    
                    if not answer_key:
                        findings.append({
                            "type": "MISSING_ANSWER_KEY",
                            "file": f"{category}/{file}",
                            "id": item_id,
                            "message": "Thiếu đáp án đúng (answer.key)",
                            "item": item
                        })
                    
                    choice_ids = [c.get("id") for c in choices]
                    if answer_key and answer_key not in choice_ids:
                        findings.append({
                            "type": "INVALID_ANSWER_KEY",
                            "file": f"{category}/{file}",
                            "id": item_id,
                            "message": f"Đáp án '{answer_key}' không có trong danh sách lựa chọn {choice_ids}",
                            "item": item
                        })
                    
                    correct_choice_val = None
                    for c in choices:
                        if c.get("id") == answer_key:
                            correct_choice_val = c.get("en") or c.get("vi")
                            break
                    
                    choice_vals = [c.get("en") or c.get("vi") for c in choices]
                    if len(choice_vals) != len(set(choice_vals)):
                        findings.append({
                            "type": "DUPLICATE_CHOICES",
                            "file": f"{category}/{file}",
                            "id": item_id,
                            "message": f"Lựa chọn bị trùng lặp: {choice_vals}",
                            "item": item
                        })
                    
                    # Number mismatch checking, but ignoring:
                    # - 3-digit vs '3 chữ số' where 3 is matched in EN and 3 is matched in VI, but '3-digit' contains '3', '3 chữ số' contains '3'. Let's clean the words
                    # Standard words like "3-digit" might produce [3], "3 chữ số" produces [3].
                    # Let's count occurrences or filter out small numbers
                    # Instead of exact check, let's check if the set of numbers is completely different.
                    nums_en = [int(n) for n in re.findall(r'\d+', stem_en)]
                    nums_vi = [int(n) for n in re.findall(r'\d+', stem_vi)]
                    
                    # Filter out '3' from nums if it's "3-digit" / "3 chữ số"
                    # But to keep it simple, if they differ, let's report it for human review.
                    if sorted(nums_en) != sorted(nums_vi):
                        # check if it's just '3-digit' / '3 chữ số' or similar minor representation
                        # Let's do a basic normalization:
                        norm_en = sorted(nums_en)
                        norm_vi = sorted(nums_vi)
                        # Remove '3' if both have it but in different frequency due to words
                        if norm_en != norm_vi:
                            findings.append({
                                "type": "TRANSLATION_NUM_MISMATCH",
                                "file": f"{category}/{file}",
                                "id": item_id,
                                "message": f"Bất đồng bộ số giữa tiếng Anh ({nums_en}) và tiếng Việt ({nums_vi}).\nEN: '{stem_en}'\nVI: '{stem_vi}'",
                                "item": item
                            })
                    
                    # Math evaluation
                    computed = extract_and_solve_math(stem_en)
                    if computed is None:
                        computed = extract_and_solve_math(stem_vi)
                    if computed is None and isinstance(figure, dict) and figure.get("renderer") == "text":
                        fig_content = figure.get("params", {}).get("content", "")
                        computed = extract_and_solve_math(fig_content)
                        
                    if computed is not None and correct_choice_val is not None:
                        val_str = str(correct_choice_val).lower().strip()
                        if val_str in ['even', 'chẵn']:
                            is_correct = (computed % 2 == 0)
                        elif val_str in ['odd', 'lẻ']:
                            is_correct = (computed % 2 != 0)
                        else:
                            try:
                                # Sometimes choice value is something like "20"
                                # but computed is 20
                                is_correct = (int(computed) == int(correct_choice_val))
                            except ValueError:
                                is_correct = True
                        
                        if not is_correct:
                            findings.append({
                                "type": "MATH_MISMATCH",
                                "file": f"{category}/{file}",
                                "id": item_id,
                                "message": f"Kết quả tính toán thực tế là {computed}, nhưng đáp án được chọn ({answer_key}) có giá trị là '{correct_choice_val}'.\nEN: '{stem_en}'\nVI: '{stem_vi}'\nFigure content: '{figure.get('params', {}).get('content') if isinstance(figure, dict) else ''}'",
                                "item": item
                            })

# Write markdown report
with open(artifact_path, 'w', encoding='utf-8') as f:
    f.write("# Báo cáo kiểm tra dữ liệu câu hỏi ôn thi TIMO\n\n")
    f.write(f"Đã phát hiện tổng cộng **{len(findings)}** điểm cần lưu ý hoặc lỗi tiềm ẩn trong database.\n\n")
    
    # Group by type
    by_type = {}
    for find in findings:
        by_type.setdefault(find["type"], []).append(find)
        
    for ftype, items in by_type.items():
        f.write(f"## {ftype} ({len(items)})\n\n")
        for item in items:
            f.write(f"### Câu hỏi `{item['id']}` (File: `{item['file']}`)\n")
            f.write(f"- **Vấn đề**: {item['message']}\n")
            if item['item']:
                f.write("- **Chi tiết câu hỏi**:\n")
                f.write("```json\n" + json.dumps(item['item'], ensure_ascii=False, indent=2) + "\n```\n")
            f.write("\n---\n\n")

print(f"Báo cáo đã được ghi vào {artifact_path}")
