const http = require("http");
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "public");
const port = Number(process.env.PORT || 31337);

const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".wasm": "application/wasm",
  ".png": "image/png",
  ".mp3": "audio/mpeg",
  ".ogg": "audio/ogg",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".md": "text/markdown; charset=utf-8",
};

function send(res, status, body, type = "text/plain; charset=utf-8") {
  res.writeHead(status, {
    "content-type": type,
    "cache-control": "no-store",
  });
  res.end(body);
}

const server = http.createServer((req, res) => {
  if (req.method === "POST" && req.url === "/leaderboard") {
    req.resume();
    send(res, 200, "");
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  let rawPath;
  try {
    rawPath = decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname);
  } catch {
    send(res, 400, "bad request");
    return;
  }
  const filePath = path.normalize(path.join(root, rawPath));

  if (!filePath.startsWith(root)) {
    send(res, 403, "forbidden");
    return;
  }

  fs.readFile(filePath, (error, data) => {
    if (error) {
      send(res, 404, "not found");
      return;
    }
    send(res, 200, data, types[path.extname(filePath)] || "application/octet-stream");
  });
});

server.listen(port, "0.0.0.0", () => {
  console.log(`BUZZK1LL running at http://127.0.0.1:${port}/`);
});
