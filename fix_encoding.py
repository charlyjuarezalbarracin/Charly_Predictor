"""Fix double-encoded UTF-8 in app.py"""

path = r'd:\Repo\Charly_Predictor\app.py'

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix common double-encoded sequences (UTF-8 read as Latin-1 then written as UTF-8)
replacements = {
    'Ã¡': 'á',  # á
    'Ã©': 'é',  # é
    'Ã\xad': 'í',  # í
    'Ã³': 'ó',  # ó
    'Ãº': 'ú',  # ú
    'Ã±': 'ñ',  # ñ
    'Ã\x81': 'Á',  # Á
    'Ã\x89': 'É',  # É
    'Ã\x8d': 'Í',  # Í
    'Ã"': 'Ó',  # Ó
    'Ãš': 'Ú',  # Ú
    'Ã\x91': 'Ñ',  # Ñ
    'Ã¼': 'ü',  # ü
    '\u00c3\u201c': 'Ó',  # Ã" (smart quote variant)
    '\u00c3\u2030': 'É',  # Ã‰ (smart quote variant)
    '\u00c3\u2019': 'Ñ',  # Ã' (smart quote variant)
}

count = 0
for old, new in replacements.items():
    c = text.count(old)
    if c > 0:
        text = text.replace(old, new)
        count += c
        print(f'  Replaced {old!r} -> {new!r} ({c} times)')

with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text)

print(f'Done! {count} total replacements')

# Verify
with open(path, 'r', encoding='utf-8') as f:
    check = f.read()
remaining = check.count('Ã')
print(f'Remaining Ã chars: {remaining}')
if remaining > 0:
    for i, line in enumerate(check.split('\n'), 1):
        if 'Ã' in line:
            print(f'  Line {i}: ...{line.strip()[:80]}...')
            if i > 10:
                print('  ... (more)')
                break
