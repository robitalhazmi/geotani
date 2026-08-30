# Walkthrough — "Open Source Palantir" for Indonesia
### Official name: **GeoTani** ("geo" = spatial/mapping, "tani" = farmer/agriculture)

---

## 1. The Long-Term Vision

A free, open-source, map-based decision layer over Indonesia, down to the **desa/kelurahan (village)** level, that lets anyone filter and visualize:

- 🌾 Resource deposits
- 🌱 Crop fertility / land suitability
- 😊 Citizen happiness / wellbeing indicators
- 🏘️ Job and housing occupancy

Think of it as Palantir Foundry's "layer data on a map, filter, and decide" experience — but open-source, free, and built on public Indonesian and global open data instead of proprietary enterprise data.

That is a multi-year platform. We are **not building that yet.**

---

## 2. Where We're Starting (This MVP)

We're validating the core mechanic — **"show me a heatmap of how good a location is for X"** — on the narrowest possible slice:

| Dimension | MVP Scope |
|---|---|
| **Theme** | Agriculture only (plantation/estate crops) |
| **Crops** | 3 crops: **Coffee, Cocoa, Sugarcane** (see rationale in Implementation Plan §0) |
| **Geography** | 3 pilot provinces at true village-level detail — **Lampung, South Sulawesi, East Java**; rest of Indonesia shown at coarser resolution |
| **Output** | A 0–100% "suitability score" per village, per crop, rendered as a smooth heatmap |
| **Users** | Open to everyone, no login required |
| **Business model** | Not decided yet — this MVP proves the product works before we design monetization |

If this narrow slice works — technically and as a compelling demo — the architecture is designed so that adding more crops, more provinces, and eventually the other three pillars (resources, happiness, occupancy) is a matter of adding new data layers, not rebuilding the system.

---

## 3. Who It's For (MVP)

Framed broadly since you chose "open for everyone," but the sharpest early use cases are:

- **Agribusinesses/investors** scouting new plantation sites
- **Cooperatives/exporters** deciding where to expand sourcing
- **Smallholder farmers** curious whether their land is well-suited to a crop before planting
- **Government/NGO planners** doing informal land-use exploration

The scoring model is deliberately explainable (not a black box) so any of these users can trust *why* a location scored the way it did.

---

## 4. The User Journey (MVP)

**Scenario: An investor is scouting land for a new coffee plantation.**

1. User opens the web app. A map of Indonesia loads, centered on the 3 pilot provinces.
2. User selects **"Coffee"** from a crop filter (dropdown or tab: Coffee / Cocoa / Rubber).
3. The map renders a **smooth gradient heatmap** — red/orange = poor suitability, yellow = moderate, green = excellent — computed per village.
4. User zooms into a region of interest (e.g., Lampung). Village-level detail sharpens as they zoom in.
5. User clicks/hovers a village. A side panel shows:
   - Overall score (e.g., "82% suitable for Coffee")
   - The breakdown: climate match, soil match, terrain match, accessibility
   - Village name, kecamatan, kabupaten, province
6. User switches the crop filter to **"Cocoa"** or **"Sugarcane"** — the same map instantly re-renders with a different heatmap, letting them compare the same land across crops (this is also a good demo moment: East Java's sugarcane heartland lights up green, while the same villages may show low suitability for cocoa).
7. (Stretch) User can toggle a layer showing where the crop is *already* grown at scale (from official statistics), to sanity-check the model against reality.

That's the entire MVP loop: **pick a crop → see a heatmap → click a village → understand why.**

---

## 5. What the "Efficiency Score" Actually Means

Important framing for you and for anyone you pitch this to: because there is no open, village-level dataset of "actual measured crop yield" for Indonesia, this score is a **land suitability index**, not a guarantee of yield. It answers:

> "Given this location's climate, soil, terrain, and access to markets, how well-matched is it to this crop's known agronomic requirements?"

This is the same conceptual approach used in FAO's land evaluation / agro-ecological zoning methodology — a well-established, defensible framework, not something invented from scratch. Full detail is in the Implementation Plan.

---

## 6. Roadmap After This MVP (Not Built Yet — Just Context)

1. Add remaining crops from your original list (corn, banana, pineapple, sugar, tobacco, cotton, and more)
2. Expand village-level detail to more provinces, eventually nationwide
3. Add the "resource deposits" layer (mining/geological open data)
4. Add "citizen happiness" and "job/housing occupancy" layers (likely sourced from BPS Podes village census data, which requires a formal data-use request — flagged as a future task, not an MVP blocker)
5. Layer comparison tools, saved views, exports — the "Palantir-style" workbench features

None of this needs to be decided now. The point of the MVP is to prove the map + scoring + filter mechanic works end-to-end.
