# Front-end asset credits

The production image elements use stock-photo image URLs from Pexels, with a local visual fallback in `frontend/assets/` if an image host is unavailable. The photos are not testimonials and the pictured people are not represented as BolKeResolve customers or endorsers. Check the source pages and current terms before any public or commercial release.

- **Homepage hero and at-home scenario:** Ketut Subiyanto, Pexels — [Concentrated young Indian couple working remotely from home using a smartphone](https://www.pexels.com/photo/concentrated-young-indian-couple-working-remotely-from-home-using-smartphone-4307872/). Delivery URL: `https://images.pexels.com/photos/4307872/pexels-photo-4307872.jpeg?auto=compress&cs=tinysrgb&w=1600`.
- **Phone-story / case-intake photography:** Ketut Subiyanto, Pexels — [Cheerful Indian man talking on cellphone and looking away](https://www.pexels.com/photo/cheerful-indian-man-talking-on-cellphone-and-looking-away-4307713/). The photo's page identifies it as a free stock photograph of a man in a turban using a smartphone. Delivery URL: `https://images.pexels.com/photos/4307713/pexels-photo-4307713.jpeg?auto=compress&cs=tinysrgb&w=1200`.
- **Couple using a phone / WhatsApp visual:** Ketut Subiyanto, Pexels — [Happy Indian couple using smartphone together](https://www.pexels.com/photo/happy-indian-couple-using-smartphone-together-4307867/). Delivery URL: `https://images.pexels.com/photos/4307867/pexels-photo-4307867.jpeg?auto=compress&cs=tinysrgb&w=1200`.
- **Additional phone-use photo:** Thangaraj Nagercoil, Pexels — [Indian man talking on a phone](https://www.pexels.com/photo/indian-man-talking-on-a-phone-16795630/). Delivery URL: `https://images.pexels.com/photos/16795630/pexels-photo-16795630.jpeg?auto=compress&cs=tinysrgb&w=1200`.
- **Manga-style helper artwork:** “Business man guide” by Juhele on OpenClipart. [Original item and license record](https://openclipart.org/detail/285004-business-man-guide). The item's listing identifies the work as CC0/public-domain artwork. The character is a visual guide only, not an expert or real person.
- **Typography:** DM Sans, DM Serif Display and Caveat requested from Google Fonts. See the [Google Fonts FAQ](https://developers.google.com/fonts/faq) and the individual font pages for licensing details.

Pexels says its images may be used for free, including commercially, subject to the Pexels license. Attribution is not required but is appreciated. Do not imply a depicted person or brand endorses the product; see the [official Pexels license](https://www.pexels.com/legal-pages/license/). Retain this source record with the project.


## Homepage “How it works” photography refresh — 22 October 2026

The three step cards now use separate, context-matched photographs rather than reusing the same local fallback image. Photos are served from Pexels' image CDN, with local fallback assets retained for unavailable networks. These are illustrative stock photographs only, not BolKeResolve customers or endorsements.

- **Tell us once:** Ketut Subiyanto, Pexels — [Cheerful Indian man talking on a cellphone](https://www.pexels.com/photo/cheerful-indian-man-talking-on-cellphone-and-looking-away-4307713/). Image URL: `https://images.pexels.com/photos/4307713/pexels-photo-4307713.jpeg?auto=compress&cs=tinysrgb&w=1400`.
- **Check the facts:** Mikhail Nilov, Pexels — [Workspace with laptop, bank card and smartphone](https://www.pexels.com/photo/a-person-transacting-a-bank-card-online-using-a-laptop-6613956/). Image URL: `https://images.pexels.com/photos/6613956/pexels-photo-6613956.jpeg?auto=compress&cs=tinysrgb&w=1400`.
- **Take the next step:** Kaboompics (Karolina Grabowska), Pexels — [Woman talking on a phone while looking at a laptop](https://www.pexels.com/photo/person-talking-on-the-cellphone-while-looking-at-the-laptop-5237652/). Image URL: `https://images.pexels.com/photos/5237652/pexels-photo-5237652.jpeg?auto=compress&cs=tinysrgb&w=1400`.

All three source pages mark the photos as free to use. Review the [Pexels license](https://www.pexels.com/legal-pages/license/) before any public or commercial release. The selected remote photographs are not vendored as local image files in this package. If an image host is unavailable, the story and follow-through cards use distinct local photos; the facts card uses a purpose-built, locally served SVG illustration.

## Original BolKeResolve guide character

- `frontend/assets/bolke-guide.webp` — original AI-generated anime-inspired Indian guide illustration created for the BolKeResolve UI, October 2026.
- `frontend/assets/bolke-guide-avatar.webp` — locally cropped/optimised avatar derivative of the same original illustration.
- These assets are served locally; no third-party image host is required for the guide character.


## Homepage photo-sequence refresh — 4 November 2026

The homepage hero now rotates slowly through the same three Pexels photographs used by the “How it works” explainer: tell your story (4307713), check the facts (6613956), and take the next step (5237652). The sequence cross-fades on a 24-second cycle, has a visible pause/play button, and stops automatically for `prefers-reduced-motion`. Images remain illustrative stock photography, not evidence of actual BolKeResolve use or endorsements. Local fallbacks are retained for restricted/offline image hosts.
