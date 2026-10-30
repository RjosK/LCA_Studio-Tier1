import subprocess
import json

chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

# Let's inspect the cards using headless chrome and print their bounding rects!
js_code = """
(() => {
  const cards = Array.from(document.querySelectorAll('.studio-node-card'));
  return cards.map(c => {
    const r = c.getBoundingClientRect();
    return {
      title: c.querySelector('.snode-title') ? c.querySelector('.snode-title').textContent : '',
      top: r.top,
      bottom: r.bottom,
      height: r.height,
      styleTop: c.style.top
    };
  });
})()
"""

# Let's write a small node script or python script with chrome to evaluate this!

