---
title: "Grain & Grit – Guide to Smooth Finishes"
---

<style>
/* === HERO BLOCK STYLES === */
.nailak-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.equalle-hero-text {
  flex: 1 1 360px;
  min-width: 260px;
  font-size: 1.15rem;
  line-height: 1.6;
  margin: 0 1rem;
  text-align: justify;
}

/* === Adaptive light/dark circle style === */
.equalle-logo-circle {
  width: 120px;
  height: 120px;
  border-radius: 20%;
  padding: 3px;
  object-fit: contain;
  background: radial-gradient(
    circle at center,
    var(--logo-bg-start, #ffffff) 0%,
    var(--logo-bg-end, #f4f4f4) 100%
  );
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
  transition: background 0.3s ease, box-shadow 0.3s ease;
}

/* Light theme */
@media (prefers-color-scheme: light) {
  .equalle-logo-circle {
    --logo-bg-start: #ffffff;
    --logo-bg-end: #f4f4f4;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

/* Dark theme */
@media (prefers-color-scheme: dark) {
  .equalle-logo-circle {
    --logo-bg-start: #0f1a13;
    --logo-bg-end: #1b2a1e;
    box-shadow: 0 4px 12px rgba(255, 255, 255, 0.08);
  }
}

/* === Mobile layout === */
@media (max-width: 640px) {
  .nailak-hero {
    justify-content: center !important;
    text-align: center !important;
  }
  .nailak-hero > div {
    flex: 1 1 100% !important;
  }
  .equalle-hero-text {
    text-align: left; /* можно заменить на justify, если нужно растянуть */
    margin: 0 1rem;
  }
}
</style>

<div class="nailak-hero">
  <div class="equalle-hero-text">
    From coarse sanding to mirror polishing — discover tools, techniques, and real-world finishing guides brought to you by the experts at <strong>eQualle</strong>.
  </div>

  <div style="flex: 0 0 140px; display: flex; justify-content: center; align-items: center;">
    <img src="/sandpaper/circle-logo.webp"
         alt="eQualle Sandpaper Circle Logo"
         class="equalle-logo-circle">
  </div>
</div>
