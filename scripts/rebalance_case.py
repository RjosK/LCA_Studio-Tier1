with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update .case-container max-width from 1280px to 1080px
text = text.replace('max-width: 1280px;', 'max-width: 1080px;')

# 2. Update .case-narrative-section grid-template-columns from 280px 1fr to 170px 1fr
text = text.replace('grid-template-columns: 280px 1fr;\n      gap: 56px;', 'grid-template-columns: 170px 1fr;\n      gap: 40px;')
text = text.replace('grid-template-columns: 280px 1fr;', 'grid-template-columns: 170px 1fr;')

# 3. Update hero bottom and lead: remove justify-content: flex-end and text-align: right
old_hero_bottom = '''    .case-hero-bottom {
      position: relative;
      z-index: 2;
      display: flex;
      justify-content: flex-end;
      margin-top: 40px;
    }

    .case-hero-lead {
      font-family: 'Instrument Serif', Georgia, serif;
      font-size: 24px;
      font-style: italic;
      line-height: 1.35;
      color: rgba(255, 255, 255, 0.88);
      max-width: 520px;
      text-align: right;
    }'''

new_hero_bottom = '''    .case-hero-bottom {
      position: relative;
      z-index: 2;
      display: flex;
      justify-content: flex-start;
      margin-top: 32px;
    }

    .case-hero-lead {
      font-family: 'Instrument Serif', Georgia, serif;
      font-size: 22px;
      font-style: italic;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.9);
      max-width: 640px;
      text-align: left;
    }'''

text = text.replace(old_hero_bottom, new_hero_bottom)

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Balanced case_cafetera.html layout')

