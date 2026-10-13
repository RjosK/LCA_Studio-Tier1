# Project Guidelines & Agent Configuration

## Design & User Interface Standards (Apple Human Interface Guidelines)

All UI/UX development and improvements in this repository must adhere to Apple Human Interface Guidelines (HIG) standards, leveraging the workspace skill:
- **Skill**: `.agents/skills/apple-design` (Registered and active)
- **Key References**:
  - `references/hig/layout.md` & `references/hig/typography.md`
  - `references/hig/toolbars.md` & `references/hig/tab-bars.md`
  - `references/hig/sidebars.md` & `references/hig/segmented-controls.md`
  - `references/cross-platform.md` (Desktop Web / Electron / Desktop standards)

### Interface Rules
1. **Desktop Density & Typography**:
   - Maintain compact, clean desktop ergonomics (11-13px typography scale).
   - Never allow toolbar items or panel tabs to overflow awkwardly or get cut off by screen edges.
   - Use `text-overflow: ellipsis; white-space: nowrap;` and responsive media queries so all tools and controls remain accessible on screens down to 1024px width.
2. **Apple Segmented Controls & Tabs**:
   - Equal distribution, subtle active shadows, proper hover and tactile press states (`scale(0.97)`).
3. **Internationalization (i18n)**:
   - 100% of UI strings must support dynamic English and Spanish language switching without page reloads.
   - Dynamic data lists (LCIA impact methods, categories, badges) must translate their labels and family groupings seamlessly.
