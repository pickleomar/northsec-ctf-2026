#!/usr/bin/env node
"use strict";

const fs = require("fs");

const [input, output] = process.argv.slice(2);
if (!input || !output) {
  console.error("usage: strip-wasm.js input.wasm output.wasm");
  process.exit(2);
}

const bytes = fs.readFileSync(input);
const out = [bytes.subarray(0, 8)];
let offset = 8;

function readVaruint() {
  let result = 0;
  let shift = 0;
  const start = offset;
  while (true) {
    const byte = bytes[offset++];
    result |= (byte & 0x7f) << shift;
    if ((byte & 0x80) === 0) break;
    shift += 7;
  }
  return { value: result >>> 0, start, end: offset };
}

while (offset < bytes.length) {
  const sectionStart = offset;
  const id = bytes[offset++];
  const size = readVaruint();
  const payloadStart = offset;
  const payloadEnd = payloadStart + size.value;

  if (id !== 0) {
    out.push(bytes.subarray(sectionStart, payloadEnd));
  }

  offset = payloadEnd;
}

fs.writeFileSync(output, Buffer.concat(out));
