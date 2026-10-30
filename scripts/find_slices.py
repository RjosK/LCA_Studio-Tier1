from PIL import Image
import os

brain = r'C:\Users\Josue\.gemini\antigravity\brain\e9f3ba53-557a-42b2-9d95-85e7274ed79c'
im = Image.open(os.path.join(brain, 'index_cases_scrolled.png'))
print("Dimensions:", im.size)

# The hero has a dark background. Below the hero is the linen background.
# Let's find where the background transitions from dark to light!
pix = im.load()
w, h = im.size
light_y = []
for y in range(0, h, 20):
    r, g, b, *rest = pix[w // 2, y]
    # Check if background is light (#F4F3EE is ~ 244, 243, 238)
    if r > 200 and g > 200 and b > 200:
        light_y.append(y)

if light_y:
    first_light = light_y[0]
    last_light = light_y[-1]
    print(f"Light background from y={first_light} to y={last_light}")
    
    # Let's take slices every 800px in the light area
    for idx, start in enumerate(range(first_light, min(last_light, first_light + 3500), 700)):
        crop = im.crop((50, start, w - 50, min(h, start + 700)))
        crop.save(os.path.join(brain, f'index_slice_{idx}.png'))
        print(f"Saved slice {idx} from y={start} to y={start+700}")
else:
    print("No light background detected in middle column")

