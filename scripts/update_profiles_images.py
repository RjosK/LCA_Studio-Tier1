with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace image 1
text = text.replace(
    'images/case_studies/thumbs/small_01_watermill.jpg',
    'images/candidates/slate/cand_18_slate.jpg'
)

# Replace image 2
text = text.replace(
    'images/case_studies/thumbs/small_04_press.jpg',
    'images/candidates/slate/cand_17_slate.jpg'
)

# Replace image 3
text = text.replace(
    'images/case_studies/thumbs/small_02_architecture.jpg',
    'images/candidates/slate/cand_21_slate.jpg'
)

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated index.html with gallery slate images')

