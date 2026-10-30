from PIL import Image
import os

brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'
im = Image.open(os.path.join(brain, 'case_cafetera_final_sankey.png'))

crop_bottom = im.crop((50, 1400, 1390, 2200))
crop_out = os.path.join(brain, 'case_cafetera_final_sankey_bottom.png')
crop_bottom.save(crop_out)
print('Bottom crop saved:', os.path.getsize(crop_out))

