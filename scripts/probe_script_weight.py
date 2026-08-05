# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Wide-sample stroke weight and kana geometry: shipped font vs Pretendard JP.

Stroke width estimator: for a shape made of strokes of width w and total
centreline length L, area ~ w*L and perimeter ~ 2L, so 2*area/perimeter ~ w.
It handles counters correctly (a ring of radii R,r gives exactly R-r) and is
robust across glyphs in a way a single-stroke probe is not.
"""
import math, sys
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.subset import Options, Subsetter
from fontTools.varLib.instancer import instantiateVariableFont

STEPS = 24

# Run from the repository root, like build.py and postbuild.py.
SOURCE = "sources/pjp/public/variable/PretendardJPVariable.ttf"
OUT = "dist"


class PerimeterPen(BasePen):
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.value = 0.0
        self._p = None
        self._start = None

    def _moveTo(self, pt):
        self._p = self._start = pt

    def _lineTo(self, pt):
        self.value += math.dist(self._p, pt)
        self._p = pt

    def _curveToOne(self, c1, c2, pt):
        p0 = self._p
        prev = p0
        for i in range(1, STEPS + 1):
            t = i / STEPS
            u = 1 - t
            x = (u**3 * p0[0] + 3*u*u*t*c1[0] + 3*u*t*t*c2[0] + t**3*pt[0])
            y = (u**3 * p0[1] + 3*u*u*t*c1[1] + 3*u*t*t*c2[1] + t**3*pt[1])
            self.value += math.dist(prev, (x, y))
            prev = (x, y)
        self._p = pt

    def _qCurveToOne(self, c, pt):
        p0 = self._p
        prev = p0
        for i in range(1, STEPS + 1):
            t = i / STEPS
            u = 1 - t
            x = u*u*p0[0] + 2*u*t*c[0] + t*t*pt[0]
            y = u*u*p0[1] + 2*u*t*c[1] + t*t*pt[1]
            self.value += math.dist(prev, (x, y))
            prev = (x, y)
        self._p = pt

    def _closePath(self):
        if self._p and self._start and self._p != self._start:
            self.value += math.dist(self._p, self._start)
        self._p = self._start


HANGUL = ("가나다라마바사아자차카타파하거너더러머버서어저처"
          "고노도로모보소오조초구누두루무부수우주추그느드르므브스으즈츠"
          "이니디리미비시지치키티피히뚫쫓빻꿇렬끓쏟짧웅쌍핥읊꽃잎")
HAN = ("一二三人大川山口日月木水火土金五六七八九十上下中左右天地生年"
       "鬱襲響驚鑑競藤議護観顔題額類願験ляと"[:30]
       + "国語学校時間電話部屋新聞会社銀行病院食堂映画音楽")
HAN = "".join(c for c in HAN if "㐀" <= c <= "鿿")
KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン"
HIRAGANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん"
SETUP = "セットアップ"

GROUPS = {
    "hangul": HANGUL,
    "han": HAN,
    "katakana": KATAKANA,
    "hiragana": HIRAGANA,
}


def measure(font, chars, label):
    upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    hmtx = font["hmtx"]
    rows = []
    for ch in chars:
        cp = ord(ch)
        if cp not in cmap:
            continue
        gname = cmap[cp]
        ap, pp, bp = AreaPen(gs), PerimeterPen(gs), BoundsPen(gs)
        try:
            gs[gname].draw(ap); gs[gname].draw(pp); gs[gname].draw(bp)
        except Exception:
            continue
        if not bp.bounds or not pp.value:
            continue
        area = abs(ap.value)
        adv = hmtx[gname][0]
        if not adv:
            continue
        x0, y0, x1, y1 = bp.bounds
        # normalise by ADVANCE, not upm: the design was squeezed into a cell,
        # so the cell is the meaningful unit of comparison, not the em.
        k = 1000.0 / adv
        rows.append(dict(
            ch=ch,
            stroke=2 * area / pp.value * k,
            w=(x1 - x0) * k, h=(y1 - y0) * k,
            y0=y0 * k, y1=y1 * k,
            fill=area / (adv * adv) if adv else 0,
        ))
    return rows


def summarise(rows):
    n = len(rows)
    if not n:
        return None
    m = lambda key: sum(r[key] for r in rows) / n
    return dict(n=n, stroke=m("stroke"), w=m("w"), h=m("h"),
                y0=m("y0"), y1=m("y1"), fill=m("fill"))


def load_source(chars, wght):
    f = TTFont(SOURCE)
    o = Options(); o.layout_features = []; o.name_IDs = []; o.notdef_outline = True
    s = Subsetter(options=o); s.populate(text=chars); s.subset(f)
    instantiateVariableFont(f, {"wght": wght}, inplace=True)
    return f


def run():
    allchars = "".join(GROUPS.values()) + SETUP
    for ours_path, wght, label in [
        (f"{OUT}/HarenaTermK-Regular.ttf", 400, "Regular"),
        (f"{OUT}/HarenaTermK-Bold.ttf", 700, "Bold"),
    ]:
        ours = TTFont(ours_path)
        src = load_source(allchars, wght)
        print(f"\n{'='*78}\n{label}   (all values normalised to advance = 1000)\n{'='*78}")
        print(f"{'group':11s} {'n':>3s} | {'stroke ours':>11s} {'src':>7s} {'ratio':>6s} "
              f"| {'ink w':>7s} {'src':>7s} | {'ink h':>7s} {'src':>7s} | {'w/h ours':>8s} {'src':>6s}")
        summ = {}
        for name, chars in GROUPS.items():
            a = summarise(measure(ours, chars, name))
            b = summarise(measure(src, chars, name))
            if not a or not b:
                continue
            summ[name] = (a, b)
            print(f"{name:11s} {a['n']:3d} | {a['stroke']:11.1f} {b['stroke']:7.1f} "
                  f"{a['stroke']/b['stroke']:6.3f} | {a['w']:7.1f} {b['w']:7.1f} "
                  f"| {a['h']:7.1f} {b['h']:7.1f} | {a['w']/a['h']:8.3f} {b['w']/b['h']:6.3f}")

        print(f"\n  cross-script stroke ratios ({label}):")
        for x, y in [("hangul", "han"), ("katakana", "han"),
                     ("hiragana", "han"), ("katakana", "hangul")]:
            if x in summ and y in summ:
                ao = summ[x][0]["stroke"] / summ[y][0]["stroke"]
                bo = summ[x][1]["stroke"] / summ[y][1]["stroke"]
                flag = "  <-- flattened" if abs(ao - 1) < abs(bo - 1) - 0.015 else ""
                print(f"    {x:9s}/{y:9s}  ours {ao:6.3f}   source {bo:6.3f}{flag}")

        print(f"\n  size ratios ({label}):")
        for x, y in [("katakana", "hangul"), ("hiragana", "hangul"), ("katakana", "han")]:
            if x in summ and y in summ:
                print(f"    {x:9s}/{y:9s}  ink h ours {summ[x][0]['h']/summ[y][0]['h']:6.3f}"
                      f"   source {summ[x][1]['h']/summ[y][1]['h']:6.3f}"
                      f"   |  ink w ours {summ[x][0]['w']/summ[y][0]['w']:6.3f}"
                      f"   source {summ[x][1]['w']/summ[y][1]['w']:6.3f}")

        print(f"\n  vertical placement, ink extents ({label}):")
        for name in GROUPS:
            if name in summ:
                a, b = summ[name]
                print(f"    {name:9s} ours y {a['y0']:7.1f}..{a['y1']:7.1f}"
                      f"    source y {b['y0']:7.1f}..{b['y1']:7.1f}")

        print(f"\n  セットアップ per glyph ({label}):")
        ra = {r["ch"]: r for r in measure(ours, SETUP, "s")}
        rb = {r["ch"]: r for r in measure(src, SETUP, "s")}
        for ch in SETUP:
            if ch in ra and ch in rb:
                a, b = ra[ch], rb[ch]
                print(f"    {ch}  ours {a['w']:6.1f} x {a['h']:6.1f}  w/h {a['w']/a['h']:6.3f}"
                      f"   |  source {b['w']:6.1f} x {b['h']:6.1f}  w/h {b['w']/b['h']:6.3f}")


run()
