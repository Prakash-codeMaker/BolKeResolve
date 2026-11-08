# BolKeResolve — Frontend Layout Polish & Design Research

**Date:** 23 October 2026  
**Scope:** The Guided Chat, sample-case demonstration, and saved-case workspace shown in the supplied screenshots.  
**Design constraint:** Preserve the established BolKeResolve palette (warm cream, deep forest green, mint accents), editorial serif display typography, rounded surfaces, and focused product scope. This is a layout/interaction repair, not a rebrand.

## Executive summary

The screenshots do not indicate that the visual identity is wrong. They show a small set of layout and state-management problems that undermine an otherwise coherent visual system:

1. **Secondary case view and its navigation can become detached.** The `Prepare & contact`/`Progress` panel sits outside the disclosure containing the three case tabs. If a tab is selected but the disclosure collapses, content remains on screen while the controls that explain and change the selected view disappear. This is a functional navigation bug, not just a spacing issue.
2. **The case panel's intro had a narrower, separately centred width than the support card below it.** It caused the “Get ready, then reach out” heading to sit noticeably further right than the aligned card/content grid.
3. **The sample-demo columns used `align-items: start` and self-alignment that made their card heights diverge.** A short control card beside a much taller result card looked unfinished and unbalanced.
4. **The Guided Chat introduction could behave like a sticky side note while the chat card had its own tall internal layout.** Depending on the scroll position/viewport, the main heading and supporting copy could look clipped or detached from the chat.
5. **View changes and anchor links did not share a consistent scroll rule.** Smooth whole-page transitions and anchors without a sticky-header offset could leave users looking at a cropped portion of the new section.
6. **The CSS had accumulated multiple competing overrides.** A final, scoped repair layer is safer for this pass than replacing the existing style system or changing the brand.

## Changes implemented

### 1. One case grid, from heading through content

- `#casePanelPrep` and `#casePanelProgress` now use one shared centered maximum width and shrink safely within their parent.
- `.case-combined-panel-intro` now follows the parent grid rather than using its own narrower, centred 960px column.
- Support cards, disclosures and route content are explicitly allowed to shrink and wrap long names, links, labels and messages.
- Mobile support-route actions stack to a single full-width action, avoiding narrow button collisions.

### 2. Keep case-navigation controls with the selected workspace

- Selecting `Prepare & contact` or `Progress` keeps `More case tools` expanded so users can see which destination is active and switch to another.
- Returning to the main plan closes the secondary menu again.
- Opening a deep link such as the support message or evidence disclosure opens that target and scrolls it into view.
- The view switch no longer animates the entire document through a mid-scroll state; the new view starts at the top, while local panel transitions retain subtle motion.

### 3. Balanced sample-case demo

- The control and result cards stretch to a common row height on wider screens.
- The left card uses a flexible column and keeps its caption/action anchored consistently instead of leaving an awkward dead area.
- Long fictional stories, explanations, source references and steps wrap inside their own card.
- At tablet/mobile widths the layout becomes a single-column sequence with natural heights, avoiding oversized blank cards.

### 4. Guided-chat layout stability

- The left introduction is in normal document flow instead of sticky positioning, preventing the large title from becoming detached from the chat while scrolling.
- Both grid columns can shrink without forcing horizontal overflow.
- The message composer has a visible, consistent input surface with clearer alignment among attachment, input and send controls.
- The language selector and voice button retain their distinct control treatment while sharing predictable heights and responsive spacing.

### 5. Scroll offsets, motion and cache

- Section anchors account for the site-header height through `scroll-margin-top`.
- Small in-panel transitions make tab/disclosure changes easier to follow without animating the whole page.
- `prefers-reduced-motion: reduce` disables the added animations.
- The service-worker shell cache was bumped from `v15` to `v16` so the revised CSS/JS can be refreshed. API routes remain network-only; case data is not added to the static shell cache.

## Acceptance checks

The existing automated suite covers the case tab selection state, relevant panel scroll, shared panel grid, demo column stretching, reduced-motion handling, anchor offsets, and cache-version change. The latest run completed with **196 passed tests plus 77 subtests**. JavaScript syntax checks passed for both `frontend/app.js` and `frontend/sw.js`.

A live Chromium visual run was attempted against the local app, but browser navigation was blocked by the environment with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. As a result, this report does **not** claim pixel-level screenshot verification. The final project still needs a browser visual pass on the target machine after downloading the package.

## Visual QA checklist for the target browser

Check at widths 1440px, 1024px, 768px, 390px and 320px:

- [ ] Guided Chat headline starts fully visible when the view opens; its first line is not behind the header.
- [ ] Guided Chat title/copy and panel sit in a consistent two-column grid on desktop and stack in a sensible reading order on mobile.
- [ ] The message input grows/shrinks without pushing the attachment or send button off-screen.
- [ ] Sample demo controls and result cards align along the top and share row height on desktop.
- [ ] Switching between sample scenarios never shows the wrong scenario's result or a stale loading state.
- [ ] Saved-case primary action appears before secondary disclosures.
- [ ] Opening `Prepare & contact` or `Progress` leaves the “More case tools” tab selector visible and the active tab identifiable.
- [ ] Case intro, support-route card and disclosures align to the same left/right grid.
- [ ] Long merchant names, source titles and user-provided text do not overflow cards.
- [ ] Anchor navigation does not place section headings behind the header.
- [ ] Keyboard focus is visible and not hidden beneath the site header.
- [ ] Reduced-motion preference disables non-essential transitions.

## Research method and boundaries

This is desk research across **30+ public design-system and product-documentation pages** selected for responsive grids, spacing, typography, forms, case/task views, conversation interfaces, content disclosures, accessibility, and motion. The sources were used to extract applicable patterns; this does not mean 30 products were individually usability-tested or reverse-engineered. Design recommendations are adapted to BolKeResolve's current user journey, rather than copied wholesale from any single system.

## Sources reviewed (35 pages)

### Forms, task flows, and concise summaries
1. [GOV.UK Design System](https://design-system.service.gov.uk/) — service-oriented components and patterns.
2. [GOV.UK Summary list](https://design-system.service.gov.uk/components/summary-list/) — compact fact review and edit links.
3. [GOV.UK Task list](https://design-system.service.gov.uk/components/task-list/) — task status and progressive disclosure.
4. [GOV.UK Error message](https://design-system.service.gov.uk/components/error-message/) — local form feedback.
5. [GOV.UK Error summary](https://design-system.service.gov.uk/components/error-summary/) — visible errors and focus handling.
6. [GOV.UK Spacing](https://design-system.service.gov.uk/styles/spacing/) — consistent spacing rhythm.
7. [UK Parliament: Designing forms](https://designsystem.parliament.uk/how-tos/designing-forms/) — form order, labels and helpful prompts.
8. [UX4G India Government Design System patterns](https://www.ux4g.gov.in/patterns) — public-service patterns relevant to Indian audiences.
9. [U.S. Web Design System: Process list](https://designsystem.digital.gov/components/process-list/) — clear, ordered steps.
10. [U.S. Web Design System: Card](https://designsystem.digital.gov/components/card/) — card hierarchy and containment.
11. [U.S. Web Design System: Summary box](https://designsystem.digital.gov/components/summary-box/) — concise highlights without overbuilding dashboards.
12. [Home Office Design System: Error messages](https://design.homeoffice.gov.uk/accessibility/interactivity/error-messages) — actionable and accessible form errors.

### Grids, spacing, type and responsive layouts
13. [Atlassian Grid](https://atlassian.design/foundations/grid) — columns, margins and gutters.
14. [Atlassian Spacing](https://atlassian.design/foundations/spacing) — spacing scale and layout rhythm.
15. [Atlassian Typography](https://atlassian.design/foundations/typography) — text hierarchy.
16. [Atlassian Design tokens](https://atlassian.design/tokens/design-tokens/) — consistent design decisions.
17. [Microsoft Fluent 2 Layout](https://fluent2.microsoft.design/layout) — responsive layouts and alignment.
18. [Carbon Design System Spacing](https://www.carbondesignsystem.com/building-blocks/foundations/spacing/overview) — spacing tokens.
19. [GitHub Primer Layout utilities](https://primer.style/product/css-utilities/layout/) — constrained containers and responsive layout utilities.
20. [Shopify Polaris Page](https://shopify.dev/docs/api/app-home/latest/web-components/layout-and-structure/page) — page-level content structure.
21. [Shopify Polaris Layout](https://polaris-react.shopify.com/components/layout-and-structure/layout) — layout primitives.
22. [Salesforce SLDS Responsive Design](https://developer.salesforce.com/docs/platform/salesforce-pages-developers-guide/guide/vf-dev-best-practices-slds-responsive.html) — responsive interface patterns.
23. [Material Design Responsive UI](https://m1.material.io/layout/responsive-ui.html) — content reflow across screen sizes.
24. [Figma Auto Layout Guide](https://help.figma.com/hc/en-us/articles/360040451373-Guide-to-auto-layout-in-Figma) — content-driven dimensions and consistent spacing.
25. [Figma Responsive webpage tips](https://help.figma.com/hc/en-us/articles/33257143505175-Tips-for-creating-a-responsive-webpage-in-Figma-Sites) — responsive composition.
26. [Figma Layout guides](https://help.figma.com/hc/en-us/articles/360040450513-Create-layout-guides) — consistent horizontal alignment.
27. [Figma Grid Auto Layout](https://help.figma.com/hc/en-us/articles/31289469907863-Use-the-grid-auto-layout-flow) — predictable grid behaviour.

### Case workspaces, navigation and conversation interfaces
28. [SAP Fiori Object Page](https://experience.sap.com/fiori-design-web/v1-30/object-page/) — structured detail pages.
29. [SAP Fiori Dynamic Page](https://experience.sap.com/fiori-design-web/dynamic-page-layout/) — hierarchical page composition.
30. [IBM Carbon Content Switcher](https://www.carbondesignsystem.com/building-blocks/core/components/content-switcher/guidelines) — when and how to switch between related views.
31. [IBM Carbon Tile](https://www.carbondesignsystem.com/building-blocks/core/components/tile/guidelines) — card/tile hierarchy.
32. [Intercom Inbox](https://www.intercom.com/helpdesk/inbox) — conversation and case context patterns.
33. [Intercom: Start a conversation from Inbox](https://www.intercom.com/help/en/articles/6433002-start-a-conversation-from-the-inbox) — focused conversation actions.
34. [Freshdesk: Ticket details enhancements](https://support.freshdesk.com/support/solutions/articles/50000013902-ticket-details-enhancements) — ticket detail density and information grouping.
35. [Salesforce Vertical Navigation](https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-vertical-navigation.html) — navigation states.

### Accessibility and motion references
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) — accessibility requirements.
- [WCAG 2.2: Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) — content reflow at narrow viewports.
- [Apple Human Interface Guidelines: Motion](https://developer.apple.com/design/human-interface-guidelines/motion) — meaningful motion and user comfort.
