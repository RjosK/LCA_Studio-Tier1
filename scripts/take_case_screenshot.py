import subprocess
import os

chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'

out = os.path.join(brain, 'case_cafetera_canvas_live.png')
subprocess.run([
    chrome, '--headless=new', '--virtual-time-budget=4000',
    f'--screenshot={out}', '--window-size=1440,2400',
    'http://127.0.0.1:8098/case_cafetera.html'
])

print('Full screenshot size:', os.path.getsize(out))

# Also crop around the canvas section
try:
    from PIL import Image
    im = Image.open(out)
    # The canvas is roughly between y=1000 and y=2000
    # Let's crop from y=850 to y=1850 across the full width
    crop_canvas = im.crop((100, 900, 1340, 1850))
    crop_out = os.path.join(brain, 'case_cafetera_canvas_crop.png')
    crop_canvas.save(crop_out)
    print('Crop size:', os.path.getsize(crop_out))
except Exception as e:
    print('Error cropping:', e)

