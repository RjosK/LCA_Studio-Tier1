import subprocess
import os

chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'

out = os.path.join(brain, 'index_cases_section.png')
# Capture index.html at cases section
subprocess.run([
    chrome, '--headless=new', '--virtual-time-budget=4000',
    f'--screenshot={out}', '--window-size=1440,2600',
    'http://127.0.0.1:8098/#homeCases'
])

print('Captured index.html cases:', os.path.getsize(out))

# Also crop around the cases section
try:
    from PIL import Image
    im = Image.open(out)
    # Crop from y=1200 to y=2200
    crop_cases = im.crop((100, 1100, 1340, 2300))
    crop_out = os.path.join(brain, 'index_cases_crop.png')
    crop_cases.save(crop_out)
    print('Crop cases size:', os.path.getsize(crop_out))
except Exception as e:
    print('Error cropping:', e)

