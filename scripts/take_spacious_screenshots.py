import subprocess
import os

chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'

# Capture standard mode
out_std = os.path.join(brain, 'case_cafetera_spacious_std.png')
subprocess.run([
    chrome, '--headless=new', '--virtual-time-budget=4000',
    f'--screenshot={out_std}', '--window-size=1440,2500',
    'http://127.0.0.1:8098/case_cafetera.html'
])

print('Standard screenshot size:', os.path.getsize(out_std))

# Crop around the canvas
try:
    from PIL import Image
    im = Image.open(out_std)
    # The canvas is roughly around y=900 to y=1900
    crop_canvas = im.crop((50, 850, 1390, 1950))
    crop_out = os.path.join(brain, 'case_cafetera_spacious_crop.png')
    crop_canvas.save(crop_out)
    print('Cropped spacious size:', os.path.getsize(crop_out))
except Exception as e:
    print('Error cropping:', e)

