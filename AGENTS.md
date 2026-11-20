# Project Guidelines & Agent Configuration - ECONODE Studio

## Design & User Interface Standards (Apple Human Interface Guidelines)

All UI/UX development and improvements in this repository must adhere to Apple Human Interface Guidelines (HIG) standards:
- Desktop Density & Typography: Compact ergonomics (11-13px typography scale).
- Responsive: Ensure controls remain accessible down to 1024px width without cutoffs.
- Apple Segmented Controls: Equal distribution, subtle shadows, proper hover and press states.
- Internationalization (i18n): 100% of UI strings must support dynamic English and Spanish switching without page reload.

## Code Quality & JavaScript Integrity Verification (Anti-Regression Protocol)

To prevent recurrent UI failures where JavaScript fails to parse and breaks page functionality (buttons not responding, login blocked):
1. **Mandatory Syntax Verification**:
   - Before committing any changes to JavaScript (`public/js/app.js`, `public/js/i18n.js`, etc.), you MUST execute `node --check <file>` to verify zero syntax errors.
   - Any `SyntaxError` prevents browser execution, disabling all event listeners and navigation.
2. **Safe Editing for Monolithic Files**:
   - `public/js/app.js` is large (~15,000 lines). When using `edit_file`, ensure the `Target` string contains enough contextual lines (minimum 4-6 lines) to guarantee uniqueness.
   - Always run `git diff --stat` before committing to verify that only the intended lines changed and that large unintended blocks (e.g. hundreds of lines) were not deleted.
3. **Automated Unit Testing Gate**:
   - Run `python -m unittest tests/test_iso_acv_report.py` (which includes `test_javascript_syntax_integrity`) before completing tasks.
