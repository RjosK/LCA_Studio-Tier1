from PIL import Image
import os

brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'
im = Image.open(os.path.join(brain, 'case_cafetera_960_sankey.png'))

crop_bottom_960 = im.crop((50, 1600, 1390, 2350))
crop_out = os.path.join(brain, 'case_cafetera_960_bottom.png')
crop_bottom_960.save(crop_out)
print('Saved bottom crop 960:', os.path.getsize(crop_out))

