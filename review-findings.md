# Code Review Findings: Pairwise70 (MAFI Calculator)

**Reviewer**: Claude Opus 4.6 (1M context)
**Date**: 2026-04-03
**Files reviewed**: `MAFI-Calculator-Complete.html` (2,580 lines), `MAFI-Calculator.html` (1,850 lines), `index.html` (45 lines)

## P0 (Critical) -- 1 found

### P0-1: CSV export missing formula injection protection
- **File**: `MAFI-Calculator-Complete.html`, line 2341-2347
- **Issue**: `exportCSV()` writes user-entered study names directly into CSV without sanitizing. A study name starting with `=`, `+`, `@`, `\t`, or `\r` would be interpreted as a formula in Excel.
- **Fix**: Add csvSafe function; sanitize study name before CSV output. Do NOT sanitize `-` prefix (corrupts negative medical values).

## P1 (Important) -- 2 found

### P1-1: Missing skip-nav link (Accessibility)
- **File**: `MAFI-Calculator-Complete.html`
- **Issue**: No skip navigation link for keyboard users. App has proper `role="tab"` ARIA but no skip-to-content.

### P1-2: `document.execCommand('copy')` deprecated
- **File**: `MAFI-Calculator-Complete.html`, line 2357
- **Issue**: `document.execCommand('copy')` is deprecated. Should use `navigator.clipboard.writeText()` with fallback.

## P2 (Minor) -- 2 found

### P2-1: Tab ARIA roles present and correct
- Tabs use `role="tab"`, `role="tablist"`, `aria-selected`, etc.

### P2-2: Closing tags present (`</body>`, `</html>`)
- Both HTML files properly closed.

## Summary
- P0: 1 | P1: 2 | P2: 2
- P0-1 FIXED: CSV injection protection added to exportCSV.
