with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/js/i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

# For ES
es_target = '"home.nav_profiles": "Perfiles de Usuario",'
es_replacement = '''"home.nav_profiles": "Perfiles",
    "home.nav_cases": "Casos",
    "home.nav_pricing": "Planes",'''

# For EN
en_target = '"home.nav_profiles": "User Profiles",'
en_replacement = '''"home.nav_profiles": "Profiles",
    "home.nav_cases": "Cases",
    "home.nav_pricing": "Pricing",'''

if es_target in text and en_target in text:
    text = text.replace(es_target, es_replacement, 1)
    text = text.replace(en_target, en_replacement, 1)
    with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/js/i18n.js', 'w', encoding='utf-8') as f:
        f.write(text)
    print('i18n nav cases and pricing added successfully')
else:
    print('Targets not found in i18n.js')

