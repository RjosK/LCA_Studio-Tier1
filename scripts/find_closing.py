with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.find('<div class="case-system-arch">')
# find closing tag by counting divs
depth = 0
end_idx = start_idx
for i in range(start_idx, len(text)):
    if text[i:i+4] == '<div':
        depth += 1
    elif text[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            end_idx = i + 6
            break

print("Start:", start_idx, "End:", end_idx)
print("Content to replace:")
print(text[start_idx:end_idx])
print("\nFollowed by:")
print(text[end_idx:end_idx+200])

