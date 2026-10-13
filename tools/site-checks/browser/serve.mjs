// Minimal static server for the built site, used by the browser checks.
// Behaves like GitHub Pages where it matters: directory URLs serve
// index.html, unknown paths get the site's own 404.html with status 404.
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";

const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
  ".mjs": "text/javascript", ".json": "application/json", ".xml": "application/xml",
  ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".webp": "image/webp", ".ico": "image/x-icon", ".woff2": "font/woff2", ".mp4": "video/mp4",
  ".webm": "video/webm", ".mp3": "audio/mpeg", ".webmanifest": "application/manifest+json",
  ".txt": "text/plain",
};

export function serveSite(root, port = 0) {
  const base = resolve(root);
  const server = createServer(async (req, res) => {
    const path = decodeURIComponent(new URL(req.url, "http://x").pathname);
    let file = normalize(join(base, path));
    if (!file.startsWith(base)) { res.writeHead(403).end(); return; }
    try {
      if ((await stat(file)).isDirectory()) file = join(file, "index.html");
      const body = await readFile(file);
      res.writeHead(200, { "content-type": TYPES[extname(file)] || "application/octet-stream" }).end(body);
    } catch {
      const body = await readFile(join(base, "404.html")).catch(() => "Not found");
      res.writeHead(404, { "content-type": TYPES[".html"] }).end(body);
    }
  });
  return new Promise((ok) => server.listen(port, "127.0.0.1", () => ok(server)));
}
