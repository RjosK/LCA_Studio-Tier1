with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

old_func = '''    const handleHomeViewExamples = (e) => {
      if (e) e.preventDefault();
      const capabilitiesSection = document.getElementById("homeCapabilities");
      if (capabilitiesSection) {
        capabilitiesSection.scrollIntoView({ behavior: "smooth" });
      } else {
        showView(state.isAuthenticated ? "dashboard" : "login");
      }
    };'''

new_func = '''    const handleHomeViewExamples = (e) => {
      if (e) e.preventDefault();
      const target = document.getElementById("homeCases") || document.getElementById("homePricing") || document.getElementById("homeArchitecture");
      if (target) {
        target.scrollIntoView({ behavior: "smooth" });
      } else {
        showView(state.isAuthenticated ? "dashboard" : "login");
      }
    };'''

if old_func in text:
    text = text.replace(old_func, new_func)
    with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/js/app.js', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated handleHomeViewExamples in app.js successfully')
else:
    print('old_func not found in app.js')

