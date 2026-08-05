// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 Jeeyong Um
// Extract ground-truth cell widths from the real xterm.js unicode11 provider,
// rather than reimplementing wcwidth and hoping it agrees.
//
// The provider is the thing that decides how many cells a terminal reserves for
// a codepoint. If the font's advance disagrees with it, the row shears. So the
// acceptance test has to be against this table, not against a table we wrote.
//
// The provider is resolved from this repository's own node_modules, at the
// version pinned exactly in package.json. That pin is load-bearing: this table
// sets every advance in the font, so it must not float with whatever a
// consuming application happens to have installed.
//
// Usage: node scripts/xterm_widths.mjs [node_modules-root] > build/xterm-widths.json
//
// The optional argument overrides where the addon is resolved from, which is
// only useful for checking this table against another installation's version.

import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';

const require = createRequire(import.meta.url);
const override = process.argv[2];

// The addon is a UMD bundle built for the browser; give it a window-ish global
// and pull the provider class out of the module exports.
const path = override
  ? `${override}/node_modules/@xterm/addon-unicode11/lib/addon-unicode11.js`
  : require.resolve('@xterm/addon-unicode11');
const src = readFileSync(path, 'utf8');
const module_ = { exports: {} };
const fn = new Function('module', 'exports', 'require', 'self', 'window', src);
fn(module_, module_.exports, require, module_.exports, module_.exports);

const Addon = module_.exports.Unicode11Addon ?? module_.exports.default;
if (!Addon) {
  console.error('exports:', Object.keys(module_.exports));
  throw new Error('could not locate Unicode11Addon in the bundle');
}

// The addon registers a provider on a Terminal; emulate the minimal surface.
let provider = null;
const fakeTerminal = {
  unicode: {
    register(p) { provider = p; },
  },
};
new Addon().activate(fakeTerminal);
if (!provider) throw new Error('addon did not register a provider');

const RANGES = [
  ['latin', 0x20, 0x7e],
  ['jamo-conjoining', 0x1100, 0x11ff],
  ['jamo-ext-a', 0xa960, 0xa97f],
  ['jamo-ext-b', 0xd7b0, 0xd7ff],
  ['halfwidth-jamo', 0xffa0, 0xffdc],
  ['latin1', 0xa0, 0xff],
  ['general-punct', 0x2000, 0x206f],
  ['letterlike', 0x2100, 0x214f],
  ['arrows', 0x2190, 0x21ff],
  ['math', 0x2200, 0x22ff],
  ['misc-technical', 0x2300, 0x23ff],
  ['box-drawing', 0x2500, 0x257f],
  ['block', 0x2580, 0x259f],
  ['geometric', 0x25a0, 0x25ff],
  ['misc-symbols', 0x2600, 0x26ff],
  ['braille', 0x2800, 0x28ff],
  ['cjk-punct', 0x3000, 0x303f],
  ['kana', 0x3040, 0x30ff],
  ['hangul-compat', 0x3130, 0x318f],
  ['kanbun', 0x3190, 0x319f],
  ['enclosed-cjk', 0x3200, 0x32ff],
  ['cjk-compat-squared', 0x3300, 0x33ff],
  ['cjk-ext-a', 0x3400, 0x4dbf],
  ['cjk', 0x4e00, 0x9fff],
  ['hangul', 0xac00, 0xd7a3],
  ['cjk-compat', 0xf900, 0xfaff],
  ['fullwidth', 0xff01, 0xff60],
  ['halfwidth-kana', 0xff61, 0xff9f],
  ['cjk-compat-forms', 0xfe30, 0xfe4f],
  ['fullwidth-signs', 0xffe0, 0xffe6],
  ['powerline', 0xe0a0, 0xe0d4],
  ['nerd-symbols', 0xf000, 0xf2ff],
];

const out = {};
for (const [name, lo, hi] of RANGES) {
  const widths = {};
  for (let cp = lo; cp <= hi; cp++) {
    const w = provider.wcwidth(cp);
    (widths[w] ??= []).push(cp);
  }
  out[name] = {
    lo, hi,
    counts: Object.fromEntries(
      Object.entries(widths).map(([w, cps]) => [w, cps.length])
    ),
    // full per-codepoint map, so verify.py can assert on every one of them
    widths: Object.fromEntries(
      Object.entries(widths).map(([w, cps]) => [w, cps])
    ),
  };
}
out._version = provider.version;
console.log(JSON.stringify(out));
