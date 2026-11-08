# Deep integration research + implemented increment

The original research and architecture discussion remains at `docs/research/BolKeResolve_Deep_Integration_Feature_Research_2026-10-23.md`.

**The first implementation slice is now in code.** `backend/evidence_review.py` provides bounded local image/PDF text extraction; `backend/main.py` provides source-linked candidate review/confirmation and the optional authenticated inbound email bridge; `backend/passport.py` exports confirmed document-fact provenance; the case frontend contains the review tools; and `docs/LIVING_RESOLUTION_PASSPORT_AND_CASE_INBOX_BRIDGE_2026-10-23.md` describes configuration and privacy boundaries.

The email bridge is intentionally off until an operator configures a controlled inbound domain, stable encryption key and strong webhook credentials, and completes the provider/DNS/HTTPS setup. This package does not include a live email provider account, live domain routing or real bank/merchant integration. The current automated suite is synthetic/mock-based and does not verify a live provider or deployment.
