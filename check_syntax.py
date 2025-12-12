with open('static/admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

open_braces = content.count('{')
close_braces = content.count('}')

print(f'File has {len(content)} characters')
print(f'Open braces: {open_braces}')
print(f'Close braces: {close_braces}')
print(f'Difference: {open_braces - close_braces}')

if open_braces == close_braces:
    print('✅ Braces are balanced!')
else:
    print('❌ Braces are NOT balanced!')
