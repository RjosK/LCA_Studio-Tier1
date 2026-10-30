import os
from PIL import Image

brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'
im = Image.open(os.path.join(brain, 'case_cafetera_canvas_live.png'))

crop_canvas_bottom = im.crop((100, 1300, 1340, 2100))
crop_out = os.path.join(brain, 'case_cafetera_canvas_bottom.png')
crop_canvas_bottom.save(crop_out)
print('Crop bottom saved:', os.path.getsize(crop_out))

