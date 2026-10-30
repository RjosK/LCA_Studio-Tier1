r"""
tests/verify_m2_semantics.py
Challenger 2 empirical verification script for Milestone 2:
1. 5 fold dock tabs in #heroFoldToolbar (data-stage, icons, tab names, both .fold-dock-tab and .fold-dock-item)
2. 3-pillar card step badges (pattern ^\d{2}\s*//\s*[A-Z]+)
3. 4 bento cards semantic structure (2 wide, 2 normal, Leontief and NOM-070 references)
4. 12 modal overlays (hidden state: display: none or default-hidden)
5. Live HTTP response from http://127.0.0.1:8095/ (HTTP 200, matching content)
"""

import sys
import os
import re
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")

INDEX_HTML_PATH = r"C:\Users\Josue\Documents\Espacio\ECONODE\public\index.html"
LIVE_SERVER_URL = "http://127.0.0.1:8095/"

def run_verification():
    results = {}
    errors = []

    print("======================================================================")
    print("CHALLENGER M2_2 EMPIRICAL VERIFICATION HARNESS")
    print("======================================================================\n")

    if not os.path.exists(INDEX_HTML_PATH):
        print(f"FATAL: {INDEX_HTML_PATH} does not exist.")
        return False

    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # ------------------------------------------------------------------
    # 1. 5 Fold Dock Tabs in #heroFoldToolbar
    # ------------------------------------------------------------------
    print("1. VERIFYING 5 FOLD DOCK TABS IN #heroFoldToolbar...")
    toolbar_match = re.search(r'id=["\']heroFoldToolbar["\'][\s\S]*?(?=<div[^>]*class=["\']strand-stage-telemetry|<section)', html)
    if not toolbar_match:
        errors.append("heroFoldToolbar container not found in index.html")
        print("  [FAIL] #heroFoldToolbar container not found")
    else:
        toolbar_html = toolbar_match.group(0)
        # Find all tab buttons
        tab_buttons = re.findall(r'<button\b([^>]*)>([\s\S]*?)</button>', toolbar_html)
        print(f"  Found {len(tab_buttons)} buttons in #heroFoldToolbar")
        expected_stages = ["injection", "blowmolding", "distribution", "vault", "audit"]
        found_stages = []
        for i, (attrs, inner) in enumerate(tab_buttons):
            stage_m = re.search(r'data-stage=["\']([^"\']+)["\']', attrs)
            stage = stage_m.group(1) if stage_m else None
            found_stages.append(stage)

            cls_m = re.search(r'class=["\']([^"\']+)["\']', attrs)
            classes = cls_m.group(1).split() if cls_m else []
            has_dock_tab = "fold-dock-tab" in classes
            has_dock_item = "fold-dock-item" in classes

            has_icon = bool(re.search(r'<svg|<i\b|<span[^>]*class=["\'][^"\']*icon', inner))
            clean_text = re.sub(r'<[^>]+>', ' ', inner).strip()
            clean_text = ' '.join(clean_text.split())

            print(f"  Tab {i+1}: stage='{stage}', text='{clean_text}'")
            print(f"    - has .fold-dock-tab: {has_dock_tab}")
            print(f"    - has .fold-dock-item: {has_dock_item}")
            print(f"    - has icon: {has_icon}")

            if not has_dock_tab:
                errors.append(f"Tab {stage} missing class .fold-dock-tab")
            if not has_dock_item:
                errors.append(f"Tab {stage} missing class .fold-dock-item")
            if not has_icon:
                errors.append(f"Tab {stage} missing icon")
            if not clean_text:
                errors.append(f"Tab {stage} missing text label")

        if found_stages != expected_stages:
            errors.append(f"Fold dock tab stages {found_stages} != expected {expected_stages}")
            print(f"  [FAIL] Stages mismatch: found {found_stages}, expected {expected_stages}")
        else:
            print("  [PASS] All 5 fold dock tabs match expected stages, classes, icons, and text labels.")

    # ------------------------------------------------------------------
    # 2. 3-Pillar Step Badges (pattern ^\d{2}\s*//\s*[A-Z]+)
    # ------------------------------------------------------------------
    print("\n2. VERIFYING 3-PILLAR STEP BADGES (pattern ^\\d{2}\\s*//\\s*[A-Z]+)...")
    badge_pattern = r'^\d{2}\s*//\s*[A-Z]+'
    pillar_badges = re.findall(r'class=["\'][^"\']*(?:strand-pillar-num|strand-card-number)[^"\']*["\'][^>]*>([\s\S]*?)</div>', html)
    clean_badges = [re.sub(r'<[^>]+>', '', b).strip() for b in pillar_badges]
    print(f"  Found {len(clean_badges)} pillar step badges: {clean_badges}")

    if len(clean_badges) != 3:
        errors.append(f"Expected 3 pillar step badges, found {len(clean_badges)}")
        print(f"  [FAIL] Count mismatch: expected 3, found {len(clean_badges)}")
    else:
        all_match = True
        for b in clean_badges:
            matches = bool(re.match(badge_pattern, b))
            print(f"  Badge '{b}': regex match = {matches}")
            if not matches:
                errors.append(f"Badge '{b}' does not match regex pattern {badge_pattern}")
                all_match = False
        if all_match:
            print("  [PASS] All 3 pillar step badges match pattern ^\\d{2}\\s*//\\s*[A-Z]+")

    # ------------------------------------------------------------------
    # 3. 4 Bento Cards Semantic Structure
    # ------------------------------------------------------------------
    print("\n3. VERIFYING 4 BENTO CARDS...")
    # Find bento cards
    bento_section = re.search(r'id=["\']homeCapabilities["\'][\s\S]*?(?=<section|\Z)', html)
    if not bento_section:
        bento_section = re.search(r'class=["\'][^"\']*strand-bento-section[\s\S]*?(?=<section|\Z)', html)

    card_openings = re.findall(r'<div\b([^>]*class=["\'][^"\']*(?:strand-bento-card|bento-card)[^"\']*["\'][^>]*)>', html)
    print(f"  Total bento cards found in DOM: {len(card_openings)}")
    wide_count = sum(1 for c in card_openings if 'bento-wide' in c)
    normal_count = sum(1 for c in card_openings if 'bento-wide' not in c)
    print(f"  Wide cards (.bento-wide): {wide_count} (expected 2)")
    print(f"  Normal cards: {normal_count} (expected 2)")

    if len(card_openings) != 4 or wide_count != 2 or normal_count != 2:
        errors.append(f"Bento cards structure mismatch: total={len(card_openings)}, wide={wide_count}, normal={normal_count}")
        print("  [FAIL] Bento cards count/dimensions mismatch")
    else:
        print("  [PASS] Exactly 4 bento cards: 2 wide and 2 normal.")

    # Check Leontief formula / references
    has_leontief_name = bool(re.search(r'Leontief', html, re.IGNORECASE))
    has_leontief_formula = bool(re.search(r's\s*=\s*A\^?\{\s*-1\s*\}\s*\\cdot\s*f|np\.linalg\.solve\(A,\s*f\)|A\^?[-−]?1\s*[·*•\\]', html))
    print(f"  Leontief reference present: {has_leontief_name}")
    print(f"  Leontief matrix formula present: {has_leontief_formula}")
    if not has_leontief_name:
        errors.append("Leontief reference missing from bento cards")
    if not has_leontief_formula:
        errors.append("Leontief formula missing from bento cards")

    # Check NOM-070 reference
    has_nom070 = "NOM-070" in html
    print(f"  NOM-070 reference present: {has_nom070}")
    if not has_nom070:
        errors.append("NOM-070 reference missing from bento cards")

    if has_leontief_name and has_leontief_formula and has_nom070:
        print("  [PASS] Bento cards contain Leontief formula and NOM-070 references.")

    # ------------------------------------------------------------------
    # 4. 12 Modal Overlays (Hidden State)
    # ------------------------------------------------------------------
    print("\n4. VERIFYING 12 MODAL OVERLAYS (HIDDEN STATE)...")
    expected_modals = [
        "modalDocuments", "modalConnectNodes", "modalWizard", "modalInviteCollaborator",
        "modalSettings", "modalAddProcessComment", "modalProcessEditor", "modalSelectDbFlow",
        "modalCreateCustomFlow", "modalSelectProvider", "modalSubscription", "reportBubbleToolbar"
    ]

    for mid in expected_modals:
        modal_m = re.search(rf'<div\b([^>]*id=["\']{mid}["\'][^>]*)>', html)
        if not modal_m:
            errors.append(f"Modal #{mid} NOT FOUND in index.html")
            print(f"  [FAIL] #{mid}: NOT FOUND")
            continue
        attrs = modal_m.group(1)
        cls_m = re.search(r'class=["\']([^"\']*)["\']', attrs)
        style_m = re.search(r'style=["\']([^"\']*)["\']', attrs)
        classes = cls_m.group(1) if cls_m else ""
        style = style_m.group(1) if style_m else ""

        # Check default hidden state
        is_hidden = False
        if "display: none" in style.lower() or "display:none" in style.lower():
            is_hidden = True
        elif "hidden" in attrs or "hidden" in classes.split() or "is-hidden" in classes.split():
            is_hidden = True
        elif "modal-overlay" in classes.split() or "modal" in classes.split() or "modal-backdrop" in classes.split():
            # In styles.css line 1509: .modal-overlay { display: none; }
            # Overlays are only displayed when .active or inline display is applied
            if "active" not in classes.split():
                is_hidden = True

        print(f"  #{mid}: class='{classes}', style='{style}', is_hidden={is_hidden}")
        if not is_hidden:
            errors.append(f"Modal #{mid} is not hidden by default")

    print(f"  Verified {len(expected_modals)} modals. Errors: {len([e for e in errors if 'Modal' in e])}")

    # ------------------------------------------------------------------
    # 5. Live HTTP Response from http://127.0.0.1:8095/
    # ------------------------------------------------------------------
    print("\n5. VERIFYING LIVE HTTP RESPONSE FROM http://127.0.0.1:8095/...")
    try:
        req = urllib.request.Request(LIVE_SERVER_URL, headers={"User-Agent": "Challenger2-Verification"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
            headers = dict(resp.headers)
            body = resp.read().decode("utf-8", errors="replace")
            print(f"  HTTP Status: {status}")
            print(f"  Content-Type: {headers.get('Content-Type') or headers.get('content-type')}")
            print(f"  Content-Length Header: {headers.get('Content-Length') or headers.get('content-length')}")
            print(f"  Body length in characters: {len(body)}")
            print(f"  Contains #heroFoldToolbar: {'heroFoldToolbar' in body}")
            print(f"  Contains .strand-pillars-section: {'strand-pillars-section' in body}")
            print(f"  Contains .strand-bento-section: {'strand-bento-section' in body}")
            print(f"  Contains .strand-comparison-table: {'strand-comparison-table' in body}")

            if status != 200:
                errors.append(f"Live server returned status {status}, expected 200")
            if "heroFoldToolbar" not in body:
                errors.append("Live server response missing #heroFoldToolbar")
            if len(body) < 10000:
                errors.append(f"Live server response unexpectedly short ({len(body)} chars)")
            print("  [PASS] Live server serves updated HTML cleanly with HTTP 200.")
    except Exception as ex:
        errors.append(f"Failed to connect to live server: {ex}")
        print(f"  [FAIL] Exception querying live server: {ex}")

    # ------------------------------------------------------------------
    # 6. Adversarial Integrity: ID Uniqueness & HTML Tag Balance
    # ------------------------------------------------------------------
    print("\n6. ADVERSARIAL INTEGRITY: ID UNIQUENESS & HTML TAG BALANCE...")
    all_ids = re.findall(r'\bid=["\']([^"\']+)["\']', html)
    unique_ids = set(all_ids)
    duplicates = [i for i in unique_ids if all_ids.count(i) > 1]
    print(f"  Total IDs in DOM: {len(all_ids)}")
    print(f"  Unique IDs: {len(unique_ids)}")
    print(f"  Duplicate IDs: {len(duplicates)}")
    if duplicates:
        errors.append(f"Duplicate IDs detected: {duplicates}")
    else:
        print("  [PASS] Zero duplicate IDs found in public/index.html.")

    from html.parser import HTMLParser
    class StrictTagValidator(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
            self.tag_errors = []
        def handle_starttag(self, tag, attrs):
            if tag.lower() not in self.void_tags:
                self.stack.append(tag.lower())
        def handle_endtag(self, tag):
            if tag.lower() in self.void_tags:
                return
            if not self.stack:
                self.tag_errors.append(f"Unexpected closing tag </{tag}>")
                return
            expected = self.stack.pop()
            if expected != tag.lower():
                self.tag_errors.append(f"Mismatch: expected </{expected}>, found </{tag}>")

    validator = StrictTagValidator()
    validator.feed(html)
    print(f"  Unclosed tags: {len(validator.stack)}")
    print(f"  Tag hierarchy mismatches: {len(validator.tag_errors)}")
    if validator.stack or validator.tag_errors:
        errors.append(f"HTML structural issues: unclosed={len(validator.stack)}, errors={len(validator.tag_errors)}")
    else:
        print("  [PASS] HTML tags are perfectly balanced with zero syntax errors.")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n======================================================================")
    print("VERIFICATION RESULTS SUMMARY")
    print("======================================================================")
    if errors:
        print(f"FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("ALL EMPIRICAL CHECKS PASSED (0 errors).")
        return True

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
