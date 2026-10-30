import re

# Update index.html
with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Pattern to remove 2 Secondary Cases
pattern = r'<!-- 2 Secondary Cases -->\s*<div class="palladio-secondary-cases-grid">.*?</div>\s*</div>\s*(?=</div>\s*</section>)'
match = re.search(pattern, text, re.DOTALL)
if match:
    text = text[:match.start()] + text[match.end():]
    with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Removed secondary cases from index.html')
else:
    print('Pattern not matched in index.html, trying manual replace')
    # Try direct substring
    start = text.find('<!-- 2 Secondary Cases -->')
    if start != -1:
        end = text.find('</div>\n        </div>\n      </div>\n    </section>\n\n    <!-- PALLADIO PLANES')
        if end == -1:
            end = text.find('</div>\n      </div>\n    </section>\n\n    <!-- PALLADIO PLANES')
        if end != -1:
            text = text[:start] + text[end:]
            with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'w', encoding='utf-8') as f:
                f.write(text)
            print('Removed secondary cases via substring')

# Update preview_cases_and_pricing.html
with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/preview_cases_and_pricing.html', 'r', encoding='utf-8') as f:
    p_text = f.read()

start_p = p_text.find('<!-- 2 Secondary Cases -->')
if start_p != -1:
    end_p = p_text.find('</div>\n      </div>\n    </section>\n\n<section class="palladio-pricing-wrapper"')
    if end_p == -1:
        end_p = p_text.find('</div>\n        </div>\n      </div>\n    </section>')
    if end_p != -1:
        p_text = p_text[:start_p] + p_text[end_p:]
        with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/preview_cases_and_pricing.html', 'w', encoding='utf-8') as f:
            f.write(p_text)
        print('Removed secondary cases from preview_cases_and_pricing.html')

