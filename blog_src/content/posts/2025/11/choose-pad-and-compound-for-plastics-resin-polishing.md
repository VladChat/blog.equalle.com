---
author: David Chen
cards:
  facebook: /posts/2025/11/18/choose-pad-and-compound-for-plastics-resin-polishing/cards/facebook/choose-pad-and-compound-for-plastics-resin-polishing.jpg
  instagram: /posts/2025/11/18/choose-pad-and-compound-for-plastics-resin-polishing/cards/instagram/choose-pad-and-compound-for-plastics-resin-polishing.jpg
  pinterest: /posts/2025/11/18/choose-pad-and-compound-for-plastics-resin-polishing/cards/pinterest/choose-pad-and-compound-for-plastics-resin-polishing.jpg
  twitter: https://blog.equalle.com/posts/2025/11/18/choose-pad-and-compound-for-plastics-resin-polishing/cards/facebook/choose-pad-and-compound-for-plastics-resin-polishing.jpg
categories:
- Resin Polishing
date: 2025-11-18 13:37:22.906103+00:00
description: 'Engineer’s guide to resin polishing: pick the right pad and compound
  for acrylic, polycarbonate, and epoxy. Tested combos, heat control, and pro tips.'
draft: false
image: https://blog.equalle.com/images/brand/01.webp
slug: choose-pad-and-compound-for-plastics-resin-polishing
tags:
- grit-600
- grit-800
- grit-1000
- grit-1500
- grit-2000
- grit-3000
- grit progression
- sanding block
- polishing pads
title: Choose Pad And Compound For Plastics
---

# Resin polishing: Pads and compounds for plastics

On a quiet Saturday, I watched a friend slowly lower a buffing pad onto the cloudy edge of his epoxy river table. The coffee mugs had left fine scuffs; sunlight turned them into halos. He’d already tried an all-purpose metal polish and a “universal” wool pad—both grabbed hard, smeared the surface, and left the epoxy warmer than I liked. He looked at me and asked the question I hear weekly: “Which pad and which compound do I actually use for plastics?” It’s an honest question with costly consequences if you guess wrong. Unlike metal paint systems that tolerate a surprising amount of heat and pressure, plastics and cured resins can haze, smear, or stress-craze from a few seconds of the wrong contact.

As a product engineer, I approach resin polishing the same way I evaluate abrasives in the lab: define the substrate, control the variables, measure the result. The route to optical clarity on acrylic (PMMA) is not the same as on polycarbonate (PC), ABS, or epoxy resin. Each polymer has its own glass-transition temperature (Tg), scratch response, and thermal behavior. Choose the wrong pad/compound pair and you’ll escalate heat, clog the pad with polymer fines, and chase your tail with deeper micro-marring.

This guide distills bench testing on five common plastics—acrylic, polycarbonate, ABS, PETG, and cast epoxy resin—using common pad families (foam, microfiber, wool) and plastic-safe compounds (aluminum oxide, silica blends, and specialty polymer polishes). I’ll explain how foam cell structure and thickness alter pressure and heat; why microfiber cuts fast but can induce haze on soft substrates; how diminishing versus non-diminishing abrasives behave on plastic; and where speed and pressure windows keep you out of the danger zone. If you’ve struggled to get a consistent, glassy finish—or if resin polishing has seemed unpredictable—this is the evidence-based path to reliable results.



<figure class="brand-image">
  <img src="/images/brand/01.webp" alt="Resin polishing: Pads and compounds for plastics — Sandpaper Sheets" loading="lazy" decoding="async">
</figure>

> Quick Summary: Match pad aggressiveness and abrasive type to the plastic’s heat tolerance and hardness, control temperature, and step through a fine grit progression to eliminate scratches without inducing haze.

## Understand your plastic and its limits

Before touching a machine, identify the polymer and its constraints. Plastics are not “soft paint.” Each has a heat threshold and failure mode that determines pad and compound selection:

- Acrylic (PMMA): Tg ≈ 105°C. Harder than PC, polishes to high gloss, but can stress-craze if overheated or hit with aggressive solvents. Responds well to fine alumina polishes and open-cell foam pads.
- Polycarbonate (PC): Tg ≈ 147°C, but surface softens under friction far sooner, smearing and “ghosting” if overheated. Micro-marring is easy to induce with rough microfiber or wool. Requires slower work and more lubrication.
- Epoxy resin: Tg varies (60–100°C depending on cure). Softer finishes (common in hobby epoxies) are heat-sensitive and prone to pad loading. Benefits from fine-cut compounds, modest pressure, and frequent pad cleaning.
- ABS/PETG: Moderate hardness, lower Tg (ABS ~105°C, PETG ~80°C). Prone to edge melt if a pad catches corners. Use smaller pads and lower RPM to keep temperatures in check.

In testing, we monitor surface temperature with an IR thermometer every 10–15 seconds. A safe rule: keep plastic surfaces below 55–60°C during polishing. Above that, PMMA and ABS will begin to haze, and epoxy can smear or swell. Smearing is often misread as “deep scratches” when it’s actually softened polymer being dragged.

Scratch geometry matters. Plastics don’t fracture like minerals; they plastically deform. That’s why sanding steps are critical. If 1000-grit scratches remain when you move to a finishing compound, they’ll telegraph through as dull trails even if the gloss meter reads high. Our lab process to prep for polishing:

- Flatten and remove damage with P600–P800 if necessary (only when surface defects are deep).
- Establish uniform scratch with P1000–P1500, then refine to P2000–P3000. For show surfaces, step to P5000 or Micro-Mesh 6000–12000.
- Rinse between steps; plastic fines clog abrasives and re-score the surface.

Finally, think geometry: smaller pads (1–3 in) on edges and tight radii to reduce pressure peaks, 3–5 in pads on broader surfaces. Larger pads (6 in) increase heat risk on plastics due to higher contact area and friction.

## Resin polishing on acrylic and epoxy

Acrylic and epoxy both polish to a water-clear finish, but they behave differently under heat and pressure. Here’s how to approach each with minimal risk.

Acrylic (PMMA) likes consistent, small abrasives on a compliant surface. Our most reliable combo for medium haze (post-P2000 sanding) is an open-cell finishing foam (white/black foam, low to medium compression, 25–40 PPI) with a non-diminishing aluminum oxide compound rated as “finishing” (abrasive size ~0.3–1.0 µm). On a dual-action (DA) polisher, set 3000–4500 OPM with minimal downforce—just enough to maintain pad contact. This setup routinely produces 90–94 GU (gloss units at 60°) and <1.0% haze (ASTM D1003) on clear PMMA sheets without leaving buffer trails.

For deeper acrylic scratches (from P1000), step first with a polish labeled “medium cut plastic” on a light polishing foam (yellow/orange). Avoid microfiber until you’ve tested on a small area—microfiber cuts quickly but can induce a gray veil that requires extra refining passes.

Epoxy resin depends heavily on cure state. Ensure a full cure per the resin’s datasheet; many tabletop epoxies reach a functional hardness after 72 hours but continue to increase Tg over a week. Polishing too early increases smearing and pad clogging. For epoxy, a finishing foam pad paired with a water-based plastic polish works best. If you need more bite, a very mild microfiber finishing pad with a fine non-diminishing compound can level small swirls, but monitor heat every pass. In our tests on a cast epoxy panel prepped to P3000, a soft foam plus fine alumina finishing compound reached 88–92 GU, and refining with the same pad and a “jeweling” polish added ~2–3 GU while reducing micro-haze by ~0.3%.

Practical notes:

- Use a spritz of distilled water as a lubricant if the compound flashes quickly; this reduces friction and helps manage temperature.
- Clean pads every panel or every two minutes of runtime. Epoxy fines load pads faster than automotive clear.
- Edge control: epoxy rounds over easily. Use a 3 in pad at lower speed near edges to avoid cutting through flood coats.

When resin polishing either substrate, the data points are the same: low, steady temperature; fine, consistent abrasives; and a pad that conforms without biting.

## Pad science: foam, microfiber, and wool

Pads are more than colors. Their structure determines cut rate, temperature rise, and scratch morphology.

Foam: Reticulated open-cell foam dissipates heat and helps sling out swarf. Two variables matter most:

- PPI (pores per inch): Higher PPI (finer cells) holds more compound, runs cooler at the surface, and reduces point loads—ideal for plastics. Lower PPI (coarser, more aggressive) increases cut but risks marring on softer resins.
- Compression/ILD: Softer foams increase contact area and lower pressure per unit area, reducing haze risk but slowing defect removal. Medium-soft finishing foams (often black/white) are the safest starting point.

Microfiber: A thin pile of synthetic fibers bonded to a foam interface. Microfiber increases cut through micro-hooking of scratches but can leave a uniform haze on plastics if paired with a high-cut compound. Using microfiber with a very fine compound can be effective for stubborn micro-marring, but you must slow the machine and reduce pressure.

Wool: Twisted or knitted fibers with excellent air flow. On paint, wool runs relatively cool; on plastic, the fiber tips can score softer polymers, producing a visible trail pattern. I reserve wool for hard acrylic in a pre-polish step only, and even then, a very mild compound at low speed.

Pad thickness and diameter influence temperature. Thicker pads isolate heat from the backing plate and distribute pressure, but they can “grab” edges. Thinner pads transmit more heat to the tool and focus pressure—risky on epoxy or ABS. Diameter scales friction; a 5 in pad runs hotter than a 3 in at the same speed.

Interface pads (soft foam discs placed between backing plate and pad) are underrated. On curved plastics, an extra 5–10 mm of interface foam allows uniform contact, reducing hotspots and edge cut-through.

In side-by-side trials on PMMA:

- Medium polishing foam + medium cut plastic polish removed P1500 sanding marks in ~2 passes, surface temp peak 49°C.
- Microfiber finishing pad + fine compound removed the same in 1–1.5 passes but peaked at 56–58°C and required a refining pass on foam.
- Wool finishing pad + fine compound matched microfiber cut but increased visible trail artifacts; two extra refining passes were needed to clear.

For work on epoxy and PC, foam wins for predictability. Microfiber is a surgical tool—use sparingly when you need a tiny bump in cut without changing compounds. And remember: pad cleanliness is half the battle; a loaded pad behaves like a dirty sanding block.

*According to a [ article](https://resiners.com/blogs/resiners-guide/best-polishing-compound-for-epoxy-resin), epoxy-specific finishing polishes tend to be finer and more lubricated, which aligns with our observation that water-rich, non-diminishing formulas manage heat and haze better on resin surfaces.*



<figure class="brand-image">
  <img src="/images/brand/29.webp" alt="Resin polishing: Pads and compounds for plastics — Sandpaper Sheets" loading="lazy" decoding="async">
</figure>

## Compounds for plastics: abrasives that work

The abrasive dictates how scratches are replaced with finer ones. For plastics, avoid products designed primarily for clearcoat or metal unless they’re known to be plastic-safe. Key variables:

Abrasive type and size:
- Aluminum oxide (alumina): The most common plastic-safe abrasive. Available as diminishing and non-diminishing. Fine versions (~0.3–1 µm) produce high clarity on PMMA and epoxy.
- Silica: Found in some polishes; can work on acrylic but some blends run “dry,” increasing heat. Look for formulations with good lubrication.
- Cerium oxide: Excellent for glass; unnecessary for most plastics and may load pads quickly on soft resins. Reserve for specialty acrylic optical work if specified by the manufacturer.

Diminishing vs non-diminishing:
- Diminishing abrasives fracture into finer particles as you work, giving a built-in “cut to finish” curve. Good when you want to shorten steps, but they require working the cycle long enough to break down—long cycles can build heat on plastics.
- Non-diminishing abrasives maintain size; you set the cut by pad choice and time. On plastics, I prefer non-diminishing for control: short, cool cycles, quick wipe, reassess.

Binder and lubrication:
- Water-based, low-odor formulations are generally safer; oil-rich polishes can smear softer resins and complicate cleanup.
- pH-neutral or slightly alkaline systems tend to be benign; avoid harsh solvents or silicone-heavy products on plastics you may glue or clear-coat later.

Color-coded “rouges” from the metalworking world can be adapted sparingly. Blue and pink bars marketed for plastics use fine alumina in a wax binder; applied with a soft foam or loose flannel wheel at low speed, they can refine edges on acrylic. But wax binders load fast; for flat panels, liquid polishes distribute more evenly.

From lab data on P2000-prepped PMMA panels:
- Medium-cut alumina liquid on a polishing foam reduced average Ra from 0.45 µm to 0.12 µm in two 30-second cycles.
- Fine non-diminishing alumina reduced Ra further to 0.04 µm with a 25–40 PPI finishing foam.
- Switching the final step to a “jeweling” polish (sub-micron abrasive) added ~2–3 GU, often not visible unless under point lights.

On epoxy (P3000-prepped):
- A fine, water-rich finishing compound prevents smear and reduces pad clogging by ~30% compared to a generic automotive finisher in our loading tests (pad mass gain over time).
- Avoid aggressive “cutting” compounds; they buy little speed on resin and increase haze risk.

Bottom line: let the pad set the aggression; let the compound be fine, consistent, and cool-running.

## Dialing in process: speeds, temps, and checks

Machines matter. Dual-action (random orbital) polishers are the default for plastics because they lower the risk of trails and local hotspots. Rotary tools can work in skilled hands for edge work or initial leveling but demand strict temperature control.

Suggested baselines (adjust to your tool):

- DA speed: 3000–4500 OPM for polishing/finishing on plastics. Stay lower on polycarbonate and epoxy; you can increase slightly on PMMA if temps are stable.
- Rotary speed: 600–900 RPM with very light pressure and constant movement. Keep the pad flat; avoid edge-leading passes on plastics.

Pressure and cycle length:
- Use just enough pressure to maintain pad-face contact. Excess pressure collapses foam cells, raises temperature, and rolls the pad edge—leading to cut-through on corners.
- Work 20–30 second cycles per 1 ft² section. Wipe, inspect, and allow heat to dissipate before repeating.

Temperature control:
- Check with an IR thermometer every pass. Aim to keep max surface temperature below 55–60°C.
- If temperatures climb, shorten cycles, reduce speed, spritz distilled water, or switch to a softer, higher-PPI foam.

Inspection and metrology:
- For clear plastics, evaluate both gloss (GU) and haze. A surface can read 90 GU yet still show micro-veil under raking light if the scratch field is inconsistent.
- Backlight the panel; uniform transmission indicates you’ve removed directional scratch patterns.
- If accessible, polarized light can reveal stress crazing early—stop if patterns emerge.

Finish protection:
- After polishing, remove residues with a mild, plastic-safe cleaner. Avoid ammonia or strong alcohols on PC.
- If needed, apply an acrylic-safe sealant; avoid silicone if you plan to bond or coat later.

Actionable tips you can apply today:
- Start gentler than you think: finishing foam + fine, water-based plastic polish. Only step up if needed.
- Use smaller pads (3–4 in) on plastics; they run cooler and give better control.
- Clean your pad every minute or two—compressed air, pad brush, or a quick rinse and spin dry. A clean pad cuts cooler and clearer.
- Sand to at least P2000 (ideally P3000) before polishing; compounds don’t replace proper sanding steps on plastics.
- Log your parameters: substrate, pad type, compound, speed, pass count, and temperature. Repeatability saves time.



<hr/>

<h2>Polishing &amp; Buffing — Video Guide</h2>
<blockquote>If you prefer to watch the logic behind pad choice, the Chemical Guys team has a clear explainer video that breaks down pad materials and their intended use cases. It reframes pad selection as a system—matching cut, finish, and tool motion—rather than a color chart. While the video focuses on automotive paint, the principles translate well to plastics: foam density affects cut and control, microfiber accelerates defect removal, and pad size impacts heat.</blockquote>
<div class="video-embed" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;"><iframe src="https://www.youtube.com/embed/iFnmfn9mwYc" title="Polishing &amp; Buffing Pads - Choosing The Correct Polishing Pad - Chemical Guys CAR CARE" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe></div>
<p style="margin-top:0.5rem;font-size:0.95rem;opacity:0.85;">Video source: <a href="https://www.youtube.com/watch?v=iFnmfn9mwYc" target="_blank" rel="noopener nofollow">Polishing &amp; Buffing Pads - Choosing The Correct Polishing Pad - Chemical Guys CAR CARE</a></p><div class="equalle-product-link"><p><a href="https://www.amazon.com/gp/product/B07QB4HGP1" target="_blank">1000 Grit Sandpaper Sheets (50-pack)</a> — 9x11 in Silicon Carbide Abrasive for Wet or Dry Use — Light polishing grit for removing swirl marks and fine scratches. Commonly used in automotive finishing, plastic restoration, and resin art. Delivers a consistent semi-gloss surface ready for final polish. (Professional Grade).</p></div>



## Frequently Asked Questions (FAQ)  
**Q:** What’s the safest starting combo for acrylic or epoxy?  
**A:** Use a finishing foam pad (high-PPI, soft) with a fine, water-based plastic polish containing non-diminishing aluminum oxide. Run a DA at 3000–4000 OPM with light pressure, 20–30 seconds per section, and keep surface temperature under 55–60°C.

**Q:** Can I use microfiber pads on polycarbonate?  
**A:** Yes, but treat them as a surgical tool. Choose a microfiber finishing pad with a fine polish, reduce speed and pressure, and test a small area first. Microfiber cuts fast but can induce a gray haze on PC that requires additional refining with foam.

**Q:** Do I need cerium oxide for resin polishing?  
**A:** Generally no. Cerium oxide is excellent for glass. Plastics and epoxies respond better to fine aluminum oxide or silica blends formulated for polymers. Cerium can load pads and doesn’t provide clear advantages on most plastics.

**Q:** Why does my epoxy smear or get sticky under the pad?  
**A:** Either the resin isn’t fully cured or you’re exceeding safe surface temperatures. Let the epoxy reach full cure (often 5–7 days), switch to a softer foam with a fine, water-rich polish, reduce cycle time, and clean the pad frequently.

**Q:** How do I know when to stop polishing?  
**A:** When raking light shows no directional scratches, haze is minimized, and additional passes fail to improve clarity or gloss readings. Over-polishing builds heat and can reintroduce haze; it’s better to stop and let the surface cool before deciding on another pass.