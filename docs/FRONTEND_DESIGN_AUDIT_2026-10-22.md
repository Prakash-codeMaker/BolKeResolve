# BolKeResolve Frontend Design Audit

**Date:** 22 October 2026  
**Scope:** The three supplied screenshots of the Guided Chat landing area, the fictional sample-case demo, and a saved Resolution Passport case.  
**Goal:** Improve layout clarity, alignment, typography, and action visibility while preserving BolKeResolve's existing cream / forest-green / mint brand identity and voice-first product fundamentals.

## Executive finding

The design direction is good. The restrained palette, editorial serif headlines, rounded surfaces, and calm tone fit a consumer support product. The main problem is not that the site needs a new visual identity. It needs a tighter layout system and a stronger hierarchy between primary action, supporting facts, and optional details.

The screenshots show three specific defects:

1. **Guided chat:** the capture shows content clipped beneath the sticky header; the chat card's top is outside the viewport and the issue choices are partly cropped. This may be a mid-scroll capture, so it does not prove an initial-load bug, but it does justify testing sticky-header overlap, anchor scrolling, and focus movement. The composer also needs a more clearly defined input surface and stronger separation between text entry and voice controls.
2. **Sample demo:** “UPI payment failed” is already selected, but the result panel still says to choose a scenario. This is a state mismatch. The large empty results card dominates the screen without explaining exactly what the user should do next.
3. **Saved case:** the user sees the case heading, status, four-part metadata strip, evidence-provenance disclosure, and “More case tools” disclosure before the primary recommended action. In the supplied viewport the most important action begins near the bottom edge. The page gives secondary structures too much vertical priority.

## Evidence-based design principles

- Keep forms short and focused. Nielsen Norman Group recommends visually grouping related labels and fields and using a single-column form layout because multi-column forms interrupt the flow of completion. Source: https://www.nngroup.com/articles/web-form-design/
- For complex or low-confidence tasks, present one decision at a time where it reduces uncertainty; make the question clear and keep hint text short. Source: https://design-system.service.gov.uk/patterns/question-pages/
- Use summary lists for key facts such as amount, merchant, date, status and reference number; make missing fields easy to change rather than using a large empty card. Source: https://design-system.service.gov.uk/components/summary-list/
- Empty states should convey the system state, help users learn, and offer a direct path to the next task. Source: https://www.nngroup.com/articles/empty-state-interface-design/
- Cards work best for related, self-contained groups; they should not be a generic border around every section. Keep cards distinct, avoid repeated content, and use responsive grids. Source: https://designsystem.digital.gov/components/card/
- Visual hierarchy depends on scale, alignment, contrast, balance and grouping. The strongest visual element should be the element of greatest importance to the user's task. Source: https://www.nngroup.com/articles/principles-visual-design/
- Sticky headers should be compact, opaque enough to stay legible, and must not obstruct content or focused controls. Source: https://www.nngroup.com/articles/sticky-headers/
- Layouts should reflow at narrow widths without loss of content or functionality; WCAG 2.2 uses 320 CSS pixels as a key reflow condition. Source: https://www.w3.org/WAI/WCAG22/Understanding/reflow.html
- WCAG 2.2 AA sets a minimum target-size criterion of 24 × 24 CSS pixels subject to exceptions; for this product, aim for about 44 × 44 CSS pixels for primary touch controls where practical. Source: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum
- Labels should remain visible, forms should use semantic grouping, and error messages should explain both the problem and how to fix it. Sources: https://designsystem.digital.gov/components/form/ and https://design-system.service.gov.uk/components/error-message/
- A check-answers step should let users change the relevant answer without repeating the entire journey. Source: https://design-system.service.gov.uk/patterns/check-answers/

## Recommended design direction

### Preserve

- Cream background, forest-green primary actions, mint highlights, and restrained warm borders.
- Serif display typography for the main headline and key case action; sans-serif for body text and controls.
- Friendly, voice-first language and the idea that the user can explain the story before adding details.
- The concise saved-case model and optional secondary case tools.

### Tighten into one layout system

Create shared tokens and reuse them rather than tuning each page independently:

- **Content container:** one consistent max-width and horizontal gutter shared by header, page titles, cards, and page sections.
- **Spacing scale:** use a consistent 4/8px rhythm (for example 8, 12, 16, 24, 32, 48, 64px) and avoid one-off margins.
- **Card padding:** one primary-card spacing token and one compact-card token; do not let nested panels accumulate large padding.
- **Typography:** one display scale, one page-title scale, one section-title scale, and body/hint/caption sizes. Use fluid sizing via `clamp()` for display type, but preserve readable body text.
- **Borders and radius:** limit emphasis to the primary action panel and selected states; use dividers / summary-list rows for small facts.
- **Grid:** use a responsive 12-column mental model at large sizes; collapse to one column for forms and content panels on narrow screens. Match the DOM order to the visible reading order.

## Page-by-page redesign

### 1. Guided Chat

**Current issue:** the photo/benefit content and chat panel form a tall two-column section. The supplied viewport is scrolled far enough that the headline and upper chat options are clipped by the sticky header. In addition, the text composer appears visually open-ended compared with the strongly outlined language selector and voice button.

**Recommended presentation:**

- Keep the two-column layout on desktop, with the top of the chat card aligned to the top of the hero content—not to a lower item in the hero stack.
- Reduce the left editorial column's height: headline, short explanation, one small social-proof/image card, and at most three short trust points. Keep the optional full-form CTA below this group.
- Set responsive typography so the large heading remains dramatic without pushing the chat card below the useful first viewport.
- Give the composer a visible, consistent outline/background, a persistent accessible label, and a clear text-entry affordance. Group attach, type, and send actions into one coherent composer row.
- Keep language selection and Speak on a dedicated, consistently aligned row above the composer, with concise helper text beneath.
- Make the transcript area the only independently scrollable chat region. The message composer should remain visible within the chat card, not drift with transcript content.
- For in-page links and “Continue here” actions, scroll the destination below the sticky header (`scroll-margin-top`) and move keyboard focus to a meaningful heading/region when appropriate.
- On tablets, allow the layout to stack at the breakpoint where the right chat panel becomes too narrow; on phones, show the short intro, then the chat, and move secondary marketing content below the primary task.

**Suggested hierarchy:**
1. “Tell us what happened” / existing branded H1.
2. One-sentence promise.
3. Chat card header.
4. Visible current message / next question.
5. Choice chips or text input.
6. Voice controls, with safety note in smaller but readable text.
7. Secondary “use full form” option.

### 2. Fictional Sample Demo

**Current issue:** the left column shows “UPI payment failed” selected, but the right-hand panel tells the user to choose a scenario. The blank panel takes almost half the page and makes the demo look unfinished even though a scenario is already active.

**Recommended presentation:**

- Make the chosen state and result state consistent. Best option: show a usable result for the default selected scenario on first load, and update the result when the user selects the second scenario. If a click is deliberately required, the empty pane must say “UPI payment failed is selected—select ‘Show example result’ to preview its plan,” not “Choose a scenario.”
- Let the result panel show real product output immediately: “What we know,” “What needs confirming,” “Recommended next step,” “Why this route,” and “Official source.” Use only three to five short rows, with source links.
- Avoid a giant decorative empty-state icon and large blank region. The output panel should be dense enough to demonstrate value but still breathable.
- The two scenarios should use the same output schema so reviewers can visually compare how the recommended step changes when the problem changes.
- Keep the fictional-data and read-only disclaimer visible but visually secondary; it should not compete with the result.
- On narrow screens, place the scenario selector first and result second. Avoid a two-column demo where a result appears far below the selected option.

**State rule:** selected scenario, button label, loading state, result content and any empty message must all derive from the same state. A selected scenario should never be described as unselected.

### 3. Saved Case / Resolution Passport

**Current issue:** the primary recommended action starts below the title, four metadata columns, and two large disclosures. The first viewport spends too much vertical space on facts and optional tools before showing what the user should do now.

**Recommended order:**

1. Compact back link and case reference.
2. Case title, status and a restrained delete action.
3. **Primary next-action card immediately below the title row**, with the recommended action, one-sentence reason, a short evidence note, source link, and one prominent CTA.
4. Compact case-facts row: amount, merchant/app, transaction date, evidence count. Missing values should read “Add” / “Not provided” as small editable links, not dominate a large column.
5. A compact “Where these details came from” disclosure.
6. “More case tools” disclosure, closed by default.

- Make the primary action visible within the initial viewport at a normal desktop height; don't force the user past two accordions before seeing it.
- Reduce the display size of long action titles on case pages. Reserve the largest editorial serif size for the landing-page H1; case-action headings should usually be more compact and wrap predictably.
- At desktop widths, the recommended-action card can occupy the main column with a small side panel only if that panel contains one directly relevant gap/next detail. Do not add a generic secondary panel just to fill space.
- At tablet widths, metadata becomes a 2×2 grid. At mobile widths, it becomes a vertical summary list or two-column compact facts, followed by the primary action.
- Keep provenance and secondary tools accessible, but visually subordinate. The product should make one action feel primary, not make every section look equally important.

## Implementation specification

### Shared responsive grid and alignment

- Use the same `.container` or equivalent across navigation, page headings, and page content.
- Use `minmax(0, 1fr)` in grid children to avoid long labels forcing overflow.
- Avoid fixed heights for cards containing dynamic text, especially Hindi/Hinglish content, source titles and recommended actions.
- Use `align-items: start` for cards that should align at the top; use stretch only where matching card heights aid scanning.
- For all section anchors, use a sticky-header offset and verify focus is not obscured.

### Typography

- Keep the existing serif/sans pairing.
- Use responsive `clamp()` for large display text; do not scale body/caption text below legible sizes to rescue the layout.
- Define line-height explicitly: display 0.95–1.1, headings around 1.15–1.3, body 1.5–1.65 (tune to the font).
- Set reasonable text measure for long descriptions; avoid full-viewport lines.

### Forms and interaction

- All inputs have visible labels; placeholders are examples, not the only labels.
- Group related controls semantically (`fieldset` / `legend` where relevant) and keep visual order aligned with DOM order.
- Inline errors belong next to the corresponding input and say how to fix the problem.
- Buttons and clickable issue cards need visible hover, focus, selected, loading and disabled states.
- Use status text/live regions for async transcription, loading, saved results and errors without relying on color alone.
- Ensure keyboard focus, selected options and validation messages are not hidden by sticky UI.

## Suggested acceptance checks

Test the same key screens at 360, 390, 768, 1024, 1440 and 1920 CSS pixels, and at 200% and 400% browser zoom where applicable.

- No unexpected horizontal overflow at mobile sizes.
- Sticky header never hides the target heading or focused control after a jump.
- Guided-chat H1 and chat card both start within the intended layout grid; the chat input remains visible and clearly interactive.
- Demo's selected scenario and result/empty state always agree.
- Default demo state either shows the result or describes exactly how to reveal it; no unexplained giant blank panel.
- Saved case shows the recommended next action before provenance or secondary tools.
- Long Hinglish messages, merchant names and titles wrap without overlapping.
- Buttons meet at least the WCAG 2.2 AA minimum target size criterion (24×24 CSS px subject to WCAG exceptions); target approximately 44×44px for important touch actions where practical.
- Keyboard-only user can select scenarios, type, send, open disclosures and reach every source link.
- Screen-reader labels and error associations remain meaningful.

## Scope: what not to change

Do not redesign the brand, add more sections, introduce more dashboard cards, or expand the complaint-platform feature set as part of this pass. Preserve the voice-first story, current palette, concise case format, case-provenance disclosure, and “More case tools” model.

The intended outcome is a cleaner, more confident presentation of the same product—not a different product.
