"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = __dirname;
const publicDir = path.join(root, "public");
const templatesDir = path.join(root, "templates");
const buildDir = path.join(root, ".build");
const maxFlagLen = 128;
const flag = process.env.FLAG || "NSC{}";

function fail(message) {
  console.error(message);
  process.exit(1);
}

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    encoding: "utf8",
  });

  if (result.status !== 0) {
    if (result.stdout) process.stdout.write(result.stdout);
    if (result.stderr) process.stderr.write(result.stderr);
    fail(`command failed: ${command} ${args.join(" ")}`);
  }
}

function ensureFlagBytes(value) {
  if (!/^[\x20-\x7e]+$/.test(value)) {
    fail("FLAG must contain printable ASCII only");
  }

  const bytes = Buffer.from(value, "ascii");
  if (bytes.length === 0) {
    fail("FLAG must not be empty");
  }
  if (bytes.length > maxFlagLen) {
    fail(`FLAG is too long: ${bytes.length} > ${maxFlagLen}`);
  }
  return bytes;
}

function toEncryptedWords(flagBytes) {
  const encrypted = Buffer.alloc(maxFlagLen);
  for (let i = 0; i < flagBytes.length; i++) {
    encrypted[i] = flagBytes[i] ^ ((0x23 + i * 17) & 0xff);
  }

  const words = [];
  for (let i = 0; i < encrypted.length; i += 4) {
    const word = encrypted.readUInt32LE(i);
    words.push(`    [${48 + i / 4}] = 0x${word.toString(16).padStart(8, "0")}u,`);
  }
  return words.join("\n");
}

function renderGameJs(flagLen) {
  const templatePath = path.join(templatesDir, "game.js.template");
  const outPath = path.join(publicDir, "game.js");
  const template = fs.readFileSync(templatePath, "utf8");
  fs.writeFileSync(outPath, template.replace("__FLAG_LEN__", String(flagLen)));
}

function renderGameC(flagWords) {
  const templatePath = path.join(templatesDir, "game.c.template");
  const outPath = path.join(buildDir, "game.c");
  const template = fs.readFileSync(templatePath, "utf8");
  fs.writeFileSync(outPath, template.replace("__FLAG_WORDS__", flagWords));
}

function buildWasm() {
  fs.mkdirSync(buildDir, { recursive: true });

  const rawWasmPath = path.join(buildDir, "game.raw.wasm");
  const wasmPath = path.join(publicDir, "game.wasm");
  const gameCPath = path.join(buildDir, "game.c");

  run("clang", [
    "--target=wasm32-unknown-unknown",
    "-Oz",
    "-nostdlib",
    "-Wl,--no-entry",
    "-Wl,--export-memory",
    "-Wl,--initial-memory=131072",
    "-Wl,--max-memory=131072",
    "-Wl,--global-base=4576",
    "-Wl,--export=reset_machine",
    "-Wl,--export=tick",
    "-Wl,--export=on_hover",
    "-Wl,--export=on_click",
    "-Wl,--export=on_miss",
    "-Wl,--export=get_score",
    "-Wl,--export=check_win",
    gameCPath,
    "-o",
    rawWasmPath,
  ]);

  run("node", [
    path.join(templatesDir, "strip-wasm.js"),
    rawWasmPath,
    wasmPath,
  ]);
}

function main() {
  const flagBytes = ensureFlagBytes(flag);
  fs.mkdirSync(buildDir, { recursive: true });
  renderGameJs(flagBytes.length);
  renderGameC(toEncryptedWords(flagBytes));
  buildWasm();

  const teamId = process.env.TEAM_ID || "unset";
  const instanceId = process.env.INSTANCE_ID || "unset";
  console.log(`BUZZK1LL prepared for TEAM_ID=${teamId} INSTANCE_ID=${instanceId}`);

  if (process.env.GENERATE_ONLY === "1") {
    return;
  }

  require("./server");
}

main();
