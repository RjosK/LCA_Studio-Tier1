import subprocess
import os

chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
brain = r'C:\Users\Josue\Documents\Espacio\ECONODE\brain_test'
os.makedirs(brain, exist_ok=True)

# Test script that loads page and invokes setCanvasMode('mass') via console/eval or by having a test page
# Let's create a test copy or temporary html where class="sankey-mode-mass" is on by default to verify the Sankey ribbons rendering!
with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make mass mode active by default for test screenshot
text_mass = text.replace('class="case-canvas-board"', 'class="case-canvas-board sankey-mode-mass"')
text_mass = text_mass.replace('id="btnModeStd" class="case-canvas-mode-btn active"', 'id="btnModeStd" class="case-canvas-mode-btn"')
text_mass = text_mass.replace('id="btnModeMass" class="case-canvas-mode-btn"', 'id="btnModeMass" class="case-canvas-mode-btn active"')
text_mass = text_mass.replace('style="opacity: 0;', 'style="opacity: 1;')

test_html_path = r'C:\Users\Josue\Documents\Espacio\ECONODE\public\test_sankey_view.html'
with open(test_html_path, 'w', encoding='utf-8') as f:
    f.write(text_mass)

out_mass = os.path.join(r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c', 'test_sankey_mass_live.png')
subprocess.run([
    chrome, '--headless=new', '--virtual-time-budget=4000',
    f'--screenshot={out_mass}', '--window-size=1440,2500',
    'http://127.0.0.1:8098/test_sankey_view.html'
])

print('Test sankey mass captured:', os.path.getsize(out_mass))

try:
    from PIL import Image
    im = Image.open(out_mass)
    crop_canvas = im.crop((50, 850, 1390, 1950))
    crop_out = os.path.join(r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c', 'test_sankey_mass_crop.png')
    crop_canvas.save(crop_out)
    print('Cropped test mass size:', os.path.getsize(crop_out))
except Exception as e:
    print('Error cropping:', e)

