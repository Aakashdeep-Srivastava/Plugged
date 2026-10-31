// Generate PLUGGED favicons + app icons from the master transparent PNG.
// Usage: node generate.mjs  (reads SRC env or the default Downloads path)
import sharp from "sharp";
import pngToIco from "png-to-ico";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dir = dirname(fileURLToPath(import.meta.url));
const SRC = process.env.SRC || "C:/Users/aakas/Downloads/PLUGGED-transparent-icon.png";
const OUT = resolve(__dir, "../../plugged/web/icons");
const BG = "#111411";       // PLUGGED Midnight Ink
const ACCENT = "#C7F66A";   // Electric Lime

await mkdir(OUT, { recursive: true });

const transparent = { r: 0, g: 0, b: 0, alpha: 0 };

// A square icon that fits the logo onto a solid background (for iOS/maskable,
// which must be opaque). `scale` is the logo's share of the canvas.
async function onBackground(size, scale, bg) {
  const inner = Math.round(size * scale);
  const logo = await sharp(SRC)
    .resize(inner, inner, { fit: "contain", background: transparent })
    .png()
    .toBuffer();
  return sharp({ create: { width: size, height: size, channels: 4, background: bg } })
    .composite([{ input: logo, gravity: "center" }])
    .png();
}

// A transparent square icon (for favicons / "any" manifest icons).
function transparentIcon(size) {
  return sharp(SRC).resize(size, size, { fit: "contain", background: transparent }).png();
}

const made = [];
async function save(pipeline, name) {
  const p = resolve(OUT, name);
  await pipeline.toFile(p);
  made.push(name);
}

// Favicons (transparent)
for (const s of [16, 32, 48]) {
  await save(transparentIcon(s), `favicon-${s}x${s}.png`);
}
// Classic multi-resolution .ico
const icoBufs = await Promise.all(
  [16, 32, 48].map((s) =>
    sharp(SRC).resize(s, s, { fit: "contain", background: transparent }).png().toBuffer()
  )
);
await writeFile(resolve(OUT, "favicon.ico"), await pngToIco(icoBufs));
made.push("favicon.ico");

// Android / PWA "any" icons (transparent)
await save(transparentIcon(192), "icon-192.png");
await save(transparentIcon(512), "icon-512.png");

// Maskable icon — logo in the ~80% safe zone on brand background
await save(await onBackground(512, 0.72, BG), "maskable-512.png");

// Apple touch icon — opaque, iOS rounds the corners itself
await save(await onBackground(180, 0.82, BG), "apple-touch-icon.png");

// In-UI logos (transparent)
for (const s of [64, 128, 256]) {
  await save(transparentIcon(s), `logo-${s}.png`);
}

// Social / Open Graph card (1200x630): logo + wordmark on brand bg
const logoForOg = await sharp(SRC)
  .resize(300, 300, { fit: "contain", background: transparent })
  .png()
  .toBuffer();
const ogText = Buffer.from(
  `<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
     <text x="470" y="300" font-family="Arial, Helvetica, sans-serif" font-size="110"
           font-weight="800" fill="#FFFFFF" letter-spacing="2">PLUGGED</text>
     <text x="474" y="360" font-family="Arial, Helvetica, sans-serif" font-size="34"
           fill="${ACCENT}">Unexpected collabs. Cultural receipts.</text>
   </svg>`
);
await save(
  sharp({ create: { width: 1200, height: 630, channels: 4, background: BG } }).composite([
    { input: logoForOg, left: 120, top: 165 },
    { input: ogText, left: 0, top: 0 },
  ]).png(),
  "og-image.png"
);

// Web app manifest
const manifest = {
  name: "PLUGGED",
  short_name: "PLUGGED",
  description: "Unexpected collabs. Cultural receipts.",
  theme_color: BG,
  background_color: BG,
  display: "standalone",
  icons: [
    { src: "/static/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
    { src: "/static/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
    { src: "/static/icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
  ],
};
await writeFile(resolve(OUT, "site.webmanifest"), JSON.stringify(manifest, null, 2));
made.push("site.webmanifest");

console.log(`Wrote ${made.length} files to ${OUT}:`);
for (const m of made) console.log("  " + m);
