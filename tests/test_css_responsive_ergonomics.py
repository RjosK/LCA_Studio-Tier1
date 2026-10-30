"""
test_css_responsive_ergonomics.py
Empirical stress-testing of CSS Architecture for Milestone 1:
- Responsiveness: 1024px and 768px media queries (font scaling, grid collapse, dock toolbar wrapping)
- Apple HIG ergonomics: minimum touch target sizes (>= 28px, 36px dock, 48px CTA), micro-typography scale
- Luminous pure white theme (#FFFFFF) on #viewHome and absence of dark mode regressions
- #viewCanvas layout isolation and non-interference
- Contrast ratio calculations against white background
- Contract selectors completeness
"""

import sys
import re
import math

CSS_PATH = r"C:\Users\Josue\Documents\Espacio\ECONODE\public\css\styles.css"

def parse_css_blocks(content):
    """Simple parser to extract media queries and top-level rules."""
    media_blocks = {}
    # Find media queries
    pattern = re.compile(r"@media\s*([^{]+)\s*\{((?:[^{}]*|\{[^{}]*\})*)\}", re.DOTALL)
    for match in pattern.finditer(content):
        query = match.group(1).strip()
        body = match.group(2).strip()
        media_blocks[query] = body
    return media_blocks

def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else math.pow((c + 0.055) / 1.055, 2.4)

def relative_luminance(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    r, g, b = [int(hex_str[i:i+2], 16) for i in (0, 2, 4)]
    r_lin = srgb_to_linear(r)
    g_lin = srgb_to_linear(g)
    b_lin = srgb_to_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

def contrast_ratio(hex1, hex2):
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def run_tests():
    with open(CSS_PATH, 'r', encoding='utf-8') as f:
        css = f.read()

    print("======================================================================")
    print("EMPIRICAL TEST SUITE: CSS ARCHITECTURE & ERGONOMICS (M1)")
    print("======================================================================")

    failures = []
    passes = 0

    # 1. Media Queries Extraction & Stress-Test
    media_queries = parse_css_blocks(css)
    print(f"\n[INFO] Found {len(media_queries)} @media blocks.")

    # 1.1 Check 1024px Breakpoint
    mq_1024_matches = [body for q, body in media_queries.items() if '1024px' in q]
    if not mq_1024_matches:
        failures.append("No @media (max-width: 1024px) block found")
    else:
        passes += 1
        print("  [PASS] @media (max-width: 1024px) block present.")
        mq1024 = "\n".join(mq_1024_matches)

        # Title font scaling
        if re.search(r"(\.strand-main-title|\.strand-hero-title)[^{]*\{[^}]*font-size:\s*40px", mq1024):
            passes += 1
            print("  [PASS] 1024px title font scales down to 40px.")
        else:
            failures.append("1024px title font scaling to 40px missing in media query")

        # Pillars grid collapse
        if re.search(r"(\.strand-pillars-cards|\.strand-pillars-grid)[^{]*\{[^}]*grid-template-columns:\s*1fr", mq1024):
            passes += 1
            print("  [PASS] 1024px 3-pillar grid collapses to 1fr single column.")
        else:
            failures.append("1024px 3-pillar grid collapse to 1fr missing")

        # Bento grid collapse
        if re.search(r"\.strand-bento-grid[^{]*\{[^}]*grid-template-columns:\s*1fr", mq1024):
            passes += 1
            print("  [PASS] 1024px bento grid collapses to 1fr single column.")
        else:
            failures.append("1024px bento grid collapse to 1fr missing")

        # Bento-wide span 1
        if re.search(r"(\.bento-wide|\.strand-bento-card\.bento-wide)[^{]*\{[^}]*grid-column:\s*span\s*1", mq1024):
            passes += 1
            print("  [PASS] 1024px bento-wide collapses from span 2 to span 1.")
        else:
            failures.append("1024px bento-wide span 1 collapse missing")

        # Fold dock toolbar wrapping
        if re.search(r"(\.fold-dock-bar|#heroFoldToolbar)[^{]*\{[^}]*flex-wrap:\s*wrap", mq1024):
            passes += 1
            print("  [PASS] 1024px fold dock toolbar flex-wraps without horizontal clipping.")
        else:
            failures.append("1024px fold dock toolbar flex-wrap missing")

        # Table wrapper horizontal scroll
        if re.search(r"(\.strand-comparison-wrapper|\.strand-matrix-wrapper)[^{]*\{[^}]*overflow-x:\s*auto", mq1024):
            passes += 1
            print("  [PASS] 1024px comparison table wrapper has overflow-x: auto.")
        else:
            failures.append("1024px comparison table wrapper overflow-x: auto missing")

    # 1.2 Check 768px Breakpoint
    mq_768_matches = [body for q, body in media_queries.items() if '768px' in q]
    if not mq_768_matches:
        failures.append("No @media (max-width: 768px) block found")
    else:
        passes += 1
        print("  [PASS] @media (max-width: 768px) block present.")
        mq768 = "\n".join(mq_768_matches)

        # Title font scaling to 32px
        if re.search(r"(\.strand-main-title|\.strand-hero-title)[^{]*\{[^}]*font-size:\s*32px", mq768):
            passes += 1
            print("  [PASS] 768px title font scales down to 32px.")
        else:
            failures.append("768px title font scaling to 32px missing")

        # Subtitle font scaling
        if re.search(r"\.strand-main-subtitle[^{]*\{[^}]*font-size:\s*15px", mq768):
            passes += 1
            print("  [PASS] 768px subtitle scales down to 15px.")
        else:
            failures.append("768px subtitle scaling to 15px missing")

        # Action buttons stack vertically
        if re.search(r"\.strand-action-group[^{]*\{[^}]*flex-direction:\s*column", mq768):
            passes += 1
            print("  [PASS] 768px hero CTA action group switches to column stacking.")
        else:
            failures.append("768px hero CTA action group flex-direction: column missing")

        # Full-width buttons on mobile
        if re.search(r"(\.btn-strand-obsidian|\.btn-strand-glass)[^{]*\{[^}]*width:\s*100%", mq768):
            passes += 1
            print("  [PASS] 768px CTA pill buttons expand to 100% width.")
        else:
            failures.append("768px CTA pill buttons width: 100% missing")

        # Section padding reduction
        if re.search(r"(\.strand-pillars-section|\.strand-bento-section|\.strand-comparison-section)[^{]*\{[^}]*padding:\s*0\s*16px", mq768):
            passes += 1
            print("  [PASS] 768px sections reduce lateral padding to 16px.")
        else:
            failures.append("768px sections padding: 0 16px missing")

    # 1.3 Check Accessibility Media Queries
    reduced_motion = [body for q, body in media_queries.items() if 'prefers-reduced-motion' in q]
    if reduced_motion:
        passes += 1
        print("  [PASS] @media (prefers-reduced-motion: reduce) present.")
    else:
        failures.append("Accessibility @media (prefers-reduced-motion: reduce) missing")

    reduced_transparency = [body for q, body in media_queries.items() if 'prefers-reduced-transparency' in q]
    if reduced_transparency:
        passes += 1
        print("  [PASS] @media (prefers-reduced-transparency: reduce) present.")
    else:
        failures.append("Accessibility @media (prefers-reduced-transparency: reduce) missing")

    # 2. Ergonomics & Touch Target Dimensions
    print("\n--- Apple HIG Touch Target Sizing & Ergonomics ---")

    # 2.1 Primary CTA button height: 48px
    obsidian_match = re.search(r"\.btn-strand-obsidian\s*\{([^}]+)\}", css)
    if obsidian_match and "height: 48px" in obsidian_match.group(1):
        passes += 1
        print("  [PASS] Primary Obsidian CTA (.btn-strand-obsidian) has height: 48px (>= 48px target).")
    else:
        failures.append(".btn-strand-obsidian height: 48px missing")

    # 2.2 Secondary CTA button height: 48px
    glass_match = re.search(r"\.btn-strand-glass\s*\{([^}]+)\}", css)
    if glass_match and "height: 48px" in glass_match.group(1):
        passes += 1
        print("  [PASS] Secondary Frosted Glass CTA (.btn-strand-glass) has height: 48px (>= 48px target).")
    else:
        failures.append(".btn-strand-glass height: 48px missing")

    # 2.3 Fold Toolbar Dock tab minimum height: 36px
    dock_tab_match = re.search(r"(\.fold-dock-tab|\.fold-dock-item)\s*\{([^}]+)\}", css)
    if dock_tab_match and "min-height: 36px" in dock_tab_match.group(2):
        passes += 1
        print("  [PASS] Fold dock tab items (.fold-dock-tab, .fold-dock-item) have min-height: 36px (>= 28px HIG minimum).")
    else:
        failures.append("Fold dock tab min-height: 36px missing")

    # 2.4 Tactile active states (scale 0.96)
    active_btn_match = re.search(r"\.btn-strand-obsidian:active\s*\{[^}]*transform:\s*scale\(0\.96\)", css)
    active_dock_match = re.search(r"(\.fold-dock-tab:active|\.fold-dock-item:active)\s*\{[^}]*transform:\s*scale\(0\.96\)", css)
    if active_btn_match and active_dock_match:
        passes += 1
        print("  [PASS] Tactile active press state (transform: scale(0.96)) verified on buttons and dock items.")
    else:
        failures.append("Tactile active transform: scale(0.96) missing on buttons or dock tabs")

    # 2.5 Focus visible ring
    focus_dock_match = re.search(r"(\.fold-dock-tab:focus-visible|\.fold-dock-item:focus-visible)\s*\{[^}]*outline:\s*2px solid", css)
    if focus_dock_match:
        passes += 1
        print("  [PASS] Keyboard accessibility (:focus-visible outline) verified on dock items.")
    else:
        failures.append("Focus-visible outline missing on dock items")

    # 2.6 Micro-typography scale (10-13px)
    micro_checks = [
        (r"\.strand-top-pill-badge\s*\{[^}]*font-size:\s*10px", "Top pill badge: 10px"),
        (r"\.stage-breadcrumb\s*\{[^}]*font-size:\s*11\.5px", "Stage breadcrumb: 11.5px"),
        (r"\.stage-metric-lbl\s*\{[^}]*font-size:\s*10px", "Stage metric label: 10px"),
        (r"\.stage-metric-val\s*\{[^}]*font-size:\s*13px", "Stage metric value: 13px"),
        (r"(\.strand-bento-badge|\.bento-badge)\s*\{[^}]*font-size:\s*10px", "Bento badge: 10px"),
        (r"(\.strand-bento-code-pill|\.bento-code-pill)\s*\{[^}]*font-size:\s*11px", "Bento code pill: 11px"),
        (r"\.strand-trust-pills\s*\{[^}]*font-size:\s*12\.5px", "Trust row pills: 12.5px"),
        (r"(\.fold-dock-tab|\.fold-dock-item)\s*\{[^}]*font-size:\s*12\.5px", "Dock tabs: 12.5px")
    ]
    for pattern_str, label in micro_checks:
        if re.search(pattern_str, css):
            passes += 1
            print(f"  [PASS] Apple HIG micro-typography {label}.")
        else:
            failures.append(f"Micro-typography missing or incorrect: {label}")

    # 3. Pure White Theme (#FFFFFF) on #viewHome & No Dark Mode Regression
    print("\n--- Theme Integrity & Pure White Validation ---")

    view_home_pattern = re.compile(r"(?:#viewHome|\.view-home)\s*\{([^}]+)\}", re.DOTALL)
    view_home_matches = view_home_pattern.findall(css)
    if not view_home_matches:
        failures.append("No #viewHome / .view-home style rules found")
    else:
        for idx, body in enumerate(view_home_matches):
            if "background-color: #FFFFFF" in body:
                passes += 1
                print(f"  [PASS] #viewHome block #{idx+1} specifies pure white background-color: #FFFFFF.")
            else:
                failures.append(f"#viewHome block #{idx+1} does not specify background-color: #FFFFFF")

    # Dark mode regression check
    dark_mode_home = re.findall(r"@media[^{]*prefers-color-scheme:\s*dark[^{]*\{[^}]*#viewHome[^}]*\}", css, re.DOTALL)
    if not dark_mode_home:
        passes += 1
        print("  [PASS] Verified ZERO dark mode overrides for #viewHome (Strict adherence to luminous light theme R3).")
    else:
        failures.append("Found dark mode override on #viewHome")

    # Contrast checks
    print("\n--- Color Contrast Ratios against Pure White (#FFFFFF) ---")
    colors_to_check = [
        ("#090D16", "Strand Obsidian Title (#090D16)", 4.5),
        ("#475569", "Main Subtitle Slate (#475569)", 4.5),
        ("#64748B", "Card Description Slate (#64748B)", 4.5),
        ("#059669", "Emerald Brand Accent (#059669)", 3.0),
        ("#0F172A", "Deep Slate Heading (#0F172A)", 4.5),
    ]
    for hex_code, desc, min_ratio in colors_to_check:
        cr = contrast_ratio(hex_code, "#FFFFFF")
        status = "PASS" if cr >= min_ratio else "FAIL"
        print(f"  [{status}] Contrast of {desc} against #FFFFFF: {cr:.2f}:1 (Required >= {min_ratio}:1)")
        if cr >= min_ratio:
            passes += 1
        else:
            failures.append(f"Insufficient contrast for {desc}: {cr:.2f}:1 < {min_ratio}:1")

    # 4. #viewCanvas Isolation & Non-interference
    print("\n--- #viewCanvas Isolation & Non-Interference ---")
    view_canvas_match = re.search(r"#viewCanvas\s*\{([^}]+)\}", css)
    if view_canvas_match:
        vc_body = view_canvas_match.group(1)
        if "max-width: 100% !important" in vc_body and "padding: 16px 20px !important" in vc_body:
            passes += 1
            print("  [PASS] #viewCanvas baseline layout preserved with !important declarations.")
        else:
            failures.append("#viewCanvas baseline layout altered")
    else:
        failures.append("#viewCanvas definition missing")

    canvas_wrapper_match = re.search(r"\.canvas-wrapper\s*\{([^}]+)\}", css)
    if canvas_wrapper_match:
        cw_body = canvas_wrapper_match.group(1)
        if "grid-template-columns: 280px 1fr 320px" in cw_body:
            passes += 1
            print("  [PASS] .canvas-wrapper 3-column grid structure (280px 1fr 320px) intact.")
        else:
            failures.append(".canvas-wrapper grid structure altered")
    else:
        failures.append(".canvas-wrapper definition missing")

    # Check that .strand-* selectors do NOT select #viewCanvas or canvas elements
    strand_leaks = [line for line in css.splitlines() if '.strand-' in line and ('#viewCanvas' in line or '.canvas-wrapper' in line)]
    if not strand_leaks:
        passes += 1
        print("  [PASS] Zero selector leakage between .strand-* design system and #viewCanvas.")
    else:
        failures.append(f"Found selector leakage between Strand and Canvas: {strand_leaks}")

    # 5. Interface Contract Inventory Verification
    print("\n--- Interface Contract & Selector Inventory ---")
    contract_selectors = [
        # PROJECT.md contract
        ".view-home", ".strand-hero-section", ".strand-top-pill", ".strand-top-pill-badge",
        ".strand-top-pill-text", ".strand-main-title", ".strand-gradient-text",
        ".strand-main-subtitle", ".btn-strand-obsidian", ".btn-strand-glass",
        ".btn-strand-shine", ".strand-stage-window", ".strand-stage-header",
        ".strand-stage-viewport", ".fold-dock-bar", ".fold-dock-tab",
        ".fold-dock-tab.is-active", ".strand-pillars-section", ".strand-pillar-card",
        ".strand-bento-section", ".strand-bento-card", ".strand-bento-card.bento-wide",
        ".strand-comparison-section", ".strand-comparison-table", ".strand-final-cta-section",
        ".strand-final-cta-card",
        # Dual-variant support
        "#heroFoldToolbar", ".fold-dock-item", ".fold-dock-item.active",
        ".strand-pillars-container", ".strand-card", ".bento-card",
        ".strand-comparison-wrapper", ".strand-badge-red", ".strand-badge-emerald"
    ]
    missing_selectors = [sel for sel in contract_selectors if sel not in css]
    if not missing_selectors:
        passes += 1
        print(f"  [PASS] All {len(contract_selectors)} contract selectors and dual variants verified present.")
    else:
        failures.append(f"Missing contract selectors: {missing_selectors}")

    print("\n======================================================================")
    print(f"TEST RESULTS: {passes} PASSED, {len(failures)} FAILED.")
    print("======================================================================")
    if failures:
        print("\nFAILURE DETAILS:")
        for f_item in failures:
            print(f" - {f_item}")
        return False
    return True

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
