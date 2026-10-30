with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if '<nav class="nav-links" id="landingNavLinks">' in line:
        new_lines.append('    <nav class="nav-links" id="landingNavLinks">\n')
        new_lines.append('      <a href="#homeArchitecture" class="landing-nav-link" id="lnkWhyUs" data-i18n="home.nav_why">Por qu&eacute; ECONODE</a>\n')
        new_lines.append('      <a href="#homeFaq" class="landing-nav-link" id="lnkFaq" data-i18n="home.nav_faq">Pilares T&eacute;cnicos</a>\n')
        new_lines.append('      <a href="#homeProfiles" class="landing-nav-link" id="lnkProfiles" data-i18n="home.nav_profiles">Perfiles de Usuario</a>\n')
        new_lines.append('    </nav>\n')
        skip = True
        continue
    if skip:
        if '</nav>' in line:
            skip = False
        continue
    new_lines.append(line)

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Nav updated cleanly!')

