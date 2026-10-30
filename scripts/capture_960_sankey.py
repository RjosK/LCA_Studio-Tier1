import subprocess
import os

chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'

out = os.path.join(brain, 'case_cafetera_960_sankey.png')
subprocess.run([
    chrome, '--headless=new', '--virtual-time-budget=4000',
    f'--screenshot={out}', '--window-size=1440,3200',
    'http://127.0.0.1:8098/case_cafetera.html'
])

print('Screenshot captured, size:', os.path.getsize(out))

try:
    from PIL import Image
    im = Image.open(out)
    # The canvas starts around y=900 and is now ~1100px tall
    crop_canvas = im.crop((50, 850, 1390, 2150))
    crop_out = os.path.join(brain, 'case_cafetera_960_sankey_crop.png')
    crop_canvas.save(crop_out)
    print('Cropped 960 sankey size:', os.path.getsize(crop_out))
    
    # Also crop specifically the left column
    crop_left = im.crop((80, 960, 480, 2100))
    crop_left_out = os.path.join(brain, 'inspect_left_column_960.png')
    crop_left.save(crop_left_out)
    print('Cropped left column size:', os.path.getsize(crop_left_out))
except Exception as e:
    print('Error cropping:', e)

