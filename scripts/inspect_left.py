from PIL import Image
import os

brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'
im = Image.open(os.path.join(brain, 'case_cafetera_final_sankey.png'))

# Crop the left column cards exactly
# x from 100 to 500, y from 950 to 1800
crop_left = im.crop((80, 960, 480, 1850))
crop_left.save(os.path.join(brain, 'inspect_left_column.png'))
print('Saved inspect_left_column.png:', crop_left.size)

