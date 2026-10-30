with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/preview_all_sections.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'images/case_studies/thumbs/small_01_watermill.jpg',
    'images/candidates/slate/cand_18_slate.jpg'
)
text = text.replace(
    'images/case_studies/thumbs/small_04_press.jpg',
    'images/candidates/slate/cand_17_slate.jpg'
)
text = text.replace(
    'images/case_studies/thumbs/small_02_architecture.jpg',
    'images/candidates/slate/cand_21_slate.jpg'
)

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/preview_all_sections.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('preview_all_sections.html updated with slate images')

