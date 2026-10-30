import subprocess
import os

chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'

# Script to get scroll position and take full page or scrolled screenshot
js_scroll = "document.getElementById('homeCases').scrollIntoView();"

out = os.path.join(brain, 'index_cases_scrolled.png')
# Since headless chrome CLI doesn't evaluate arbitrary JS easily without CDP, we can screenshot full page or a very tall window
subprocess.run([
    chrome, '--headless=new', '--virtual-time-budget=4000',
    f'--screenshot={out}', '--window-size=1440,6500',
    'http://127.0.0.1:8098/'
])

print('Full page screenshot:', os.path.getsize(out))

try:
    from PIL import Image
    im = Image.open(out)
    w, h = im.size
    print('Image dimensions:', w, h)
    
    # Let's search where #homeCases is:
    # In earlier runs, homeCases was around y=3600 to 5200
    crop_cases = im.crop((100, 3600, 1340, 5200))
    crop_cases.save(os.path.join(brain, 'index_cases_detected.png'))
    print('Cropped detected size:', os.path.getsize(os.path.join(brain, 'index_cases_detected.png')))
except Exception as e:
    print('Error:', e)

