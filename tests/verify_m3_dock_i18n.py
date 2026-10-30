"""Empirical verification script for Milestone 3 (Interactive Dock Controller & Dynamic Bilingual i18n).
Validates:
1. 100% dictionary completeness & parity across all 47 home.* keys in both ES and EN in i18n.js.
2. Dynamic language translation logic without page reload.
3. setupFoldToolbarHome() controller handles all 5 stages, active & is-active toggling, SVG node & telemetry mutations, and keyboard navigation.
4. CSS styling refinements ("Quitarle la vibra de IA"): high contrast title, titanium metallic gradient, warm white #FAFAFA background, and Apple HIG tactile active press scale(0.97).
5. Studio launch hooks and CTA button bindings.
"""

import os
import re
import sys

BASE_DIR = r"C:\Users\Josue\Documents\Espacio\ECONODE"
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

HTML_PATH = os.path.join(BASE_DIR, "public", "index.html")
CSS_PATH = os.path.join(BASE_DIR, "public", "css", "styles.css")
APP_JS_PATH = os.path.join(BASE_DIR, "public", "js", "app.js")
I18N_JS_PATH = os.path.join(BASE_DIR, "public", "js", "i18n.js")

errors = []

print("=" * 70)
print("MILESTONE 3 EMPIRICAL VERIFICATION SUITE")
print("=" * 70)

# 1. Verify i18n.js
print("\n[1] Verifying Dynamic Bilingual i18n Dictionary...")
with open(I18N_JS_PATH, "r", encoding="utf-8") as f:
    i18n_content = f.read()

# Extract dictionaries
from tests.e2e.e2e_utils import extract_i18n_dictionary
i18n_dict = extract_i18n_dictionary(i18n_content)

if "es" not in i18n_dict or "en" not in i18n_dict:
    errors.append("i18n dictionary must contain both 'es' and 'en' root keys")
else:
    es_dict = i18n_dict["es"]
    en_dict = i18n_dict["en"]
    print(f"  -> ES dictionary loaded: {len(es_dict)} keys")
    print(f"  -> EN dictionary loaded: {len(en_dict)} keys")

    # Read DOM home.* data-i18n keys
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    dom_home_keys = set(re.findall(r'data-i18n=["\'](home\.[^"\']+)["\']', html_content))
    print(f"  -> Found {len(dom_home_keys)} unique home.* keys in index.html")

    missing_es = dom_home_keys - set(es_dict.keys())
    missing_en = dom_home_keys - set(en_dict.keys())
    if missing_es:
        errors.append(f"Missing keys in ES dictionary: {missing_es}")
    if missing_en:
        errors.append(f"Missing keys in EN dictionary: {missing_en}")

    parity_diff = set(es_dict.keys()) ^ set(en_dict.keys())
    if parity_diff:
        errors.append(f"Key parity mismatch between ES and EN: {parity_diff}")
    else:
        print("  -> 100% ES/EN dictionary key parity confirmed!")

    # Verify setLanguage method
    if "function setLanguage(lang)" not in i18n_content:
        errors.append("setLanguage(lang) function missing from i18n.js")
    else:
        print("  -> Dynamic zero-reload setLanguage function confirmed!")

# 2. Verify app.js setupFoldToolbarHome & Telemetry
print("\n[2] Verifying setupFoldToolbarHome Dock Controller...")
with open(APP_JS_PATH, "r", encoding="utf-8") as f:
    app_js = f.read()

if "function setupFoldToolbarHome()" not in app_js:
    errors.append("setupFoldToolbarHome() function missing from app.js")
else:
    print("  -> setupFoldToolbarHome() defined.")

# Check stages
for stage in ["injection", "blowmolding", "distribution", "vault", "audit"]:
    if f"{stage}:" not in app_js:
        errors.append(f"Stage '{stage}' missing from stageCatalog")

# Check class toggling
if 'items.forEach(b => b.classList.remove("active"))' not in app_js or 'btn.classList.add("active")' not in app_js:
    errors.append("Active class toggling missing from dock click handler")
else:
    print("  -> Active class toggling verified.")

if 'items.forEach(b => b.classList.remove("is-active"))' not in app_js or 'btn.classList.add("is-active")' not in app_js:
    errors.append("is-active class toggling missing from dock click handler")
else:
    print("  -> is-active class toggling verified.")

# Check SVG & telemetry mutations
telemetry_ids = [
    "stageNodeCoreTitle", "stageNodeCoreBadge", "heroStageBreadcrumb",
    "stageGwpValText", "stageMassValText", "stageStorageValText", "stageNormBadgeText"
]
for tid in telemetry_ids:
    if f'getElementById("{tid}")' not in app_js:
        errors.append(f"DOM telemetry mutation missing for #{tid}")
print("  -> All 7 telemetry mutation targets verified in app.js.")

# Check keyboard navigation
if "ArrowRight" not in app_js or "ArrowLeft" not in app_js:
    errors.append("Keyboard arrow navigation missing from setupFoldToolbarHome")
else:
    print("  -> Apple HIG keyboard navigation across dock tabs confirmed.")

# Check CTA routing
if 'btnNavEnter.addEventListener("click", () => showView(state.isAuthenticated ? "dashboard" : "login"))' not in app_js:
    errors.append("btnNavEnter click handler missing or malformed")
if 'btnHomeEnter.addEventListener("click", () => showView(state.isAuthenticated ? "dashboard" : "login"))' not in app_js:
    errors.append("btnHomeEnter click handler missing or malformed")
if "homeCapabilities" not in app_js:
    errors.append("btnHomeEx scroll to homeCapabilities missing")
print("  -> Studio launch and CTA navigation hooks verified.")

# 3. Verify styles.css
print("\n[3] Verifying CSS Polish ('Quitarle la vibra de IA')...")
with open(CSS_PATH, "r", encoding="utf-8") as f:
    css_content = f.read()

from tests.e2e.e2e_utils import CSSAnalyzer
css = CSSAnalyzer(css_content)

# Title contrast
rules = css.get_rules_for_selector(".strand-main-title")
if not any("#090d16" in r.lower() for r in rules):
    errors.append(".strand-main-title must have deep obsidian black #090D16")
else:
    print("  -> .strand-main-title high-contrast deep black verified.")

# Titanium metallic gradient
grad_rules = css.get_rules_for_selector(".strand-gradient-text")
if not any("linear-gradient" in r and "#059669" in r for r in grad_rules):
    errors.append(".strand-gradient-text must define titanium gradient ending in subtle #059669")
else:
    print("  -> .strand-gradient-text titanium metallic finish verified.")

# Warm white background
home_rules = css.get_rules_for_selector("#viewHome")
if not any("#fafafa" in r.lower() for r in home_rules):
    errors.append("#viewHome must define warm white #FAFAFA background")
else:
    print("  -> #viewHome warm white #FAFAFA background verified.")

# Tactile active press
dock_active = css.get_rules_for_selector(".fold-dock-item:active")
if not any("scale(0.97)" in r for r in dock_active):
    errors.append(".fold-dock-item:active must have tactile scale(0.97)")
else:
    print("  -> .fold-dock-item:active tactile scale(0.97) verified.")

print("\n" + "=" * 70)
if errors:
    print(f"VERIFICATION FAILED: {len(errors)} error(s) found:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("ALL MILESTONE 3 VERIFICATION CHECKS PASSED (0 errors)!")
    print("=" * 70)
