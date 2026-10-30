with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Hero button to <a href="#homeCases">
old_btn = '''              <button class="palladio-btn-pricing" id="btnHomeViewExamples" data-alias="heroBtnEjemplosNOM" name="heroBtnEjemplosNOM" onclick="document.getElementById('homeCases').scrollIntoView({behavior:'smooth'})">
                <span>Ver Planes y Casos</span>
                <span class="palladio-btn-arrow">&rarr;</span>
              </button>'''

new_btn = '''              <a href="#homeCases" class="palladio-btn-pricing" id="btnHomeViewExamples" data-alias="heroBtnEjemplosNOM" name="heroBtnEjemplosNOM">
                <span>Ver Planes y Casos</span>
                <span class="palladio-btn-arrow">&rarr;</span>
              </a>'''

if old_btn in text:
    text = text.replace(old_btn, new_btn)
    print('Updated btnHomeViewExamples to <a> tag')
else:
    # Try more flexible replace
    import re
    text = re.sub(
        r'<button class="palladio-btn-pricing"[^>]*id="btnHomeViewExamples"[^>]*>.*?<span>Ver Planes y Casos</span>.*?</button>',
        new_btn.strip(),
        text,
        flags=re.DOTALL
    )
    print('Updated btnHomeViewExamples via regex')

# 2. Add smooth scroll handler for all a[href^="#home"] in the landing script
smooth_scroll_code = '''
  <script>
    // Smooth scrolling for all landing page anchors
    document.addEventListener('DOMContentLoaded', function() {
      document.querySelectorAll('a[href^="#home"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
          var targetId = this.getAttribute('href').substring(1);
          var targetEl = document.getElementById(targetId);
          if (targetEl) {
            e.preventDefault();
            targetEl.scrollIntoView({ behavior: 'smooth' });
            if (history.pushState) {
              history.pushState(null, null, '#' + targetId);
            }
          }
        });
      });
    });
  </script>
'''

if 'Smooth scrolling for all landing page anchors' not in text:
    text = text.replace('</body>', smooth_scroll_code + '\n</body>')
    print('Added smooth scroll listener')

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('index.html fully updated!')

