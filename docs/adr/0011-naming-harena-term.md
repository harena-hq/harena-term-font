# 0011 — The family is Harena Term, and what a font name here must clear

Status: **accepted**, with one open risk recorded below.

## Context

Naming a font after the application it was built for is conventional — JetBrains
Mono, Cascadia Code, SF Mono. But a font name has to clear constraints an
application name does not, and they are worth stating because they narrow the
field before taste gets a say.

## What a name here must clear

**Reserved Font Names.** The OFL lets an upstream reserve its name, and a
derivative may not use it. Of the sources here:

| source | RFN |
|---|---|
| Pretendard JP | **reserves "Pretendard JP"** |
| Source Han Sans (upstream of the han) | **"Source" is reserved** |
| Iosevka | reserves none (`OFL-1.1-no-RFN`) |
| M PLUS 1p | reserves none |

So `Pretendard*` and `Source*` are excluded outright. Iosevka's permissiveness
does not make `Iosevka*` advisable, and it is avoided anyway.

**Vendor ID.** `OS/2.achVendID` is four characters: `HRNA`. Unregistered with
Microsoft, which is common and carries no functional consequence.

## Decision

Families `Harena Term K` and `Harena Term J`; PostScript names
`HarenaTermK-Regular` and so on; vendor `HRNA`.

`Harena Term` is a **Reserved Font Name** under the OFL. Iosevka, Pretendard and
JetBrains Mono all decline to reserve theirs; this one is reserved because the
name is an application's and is carried for recognition, which is the case the
RFN clause exists for. It is also the reversible direction — a copyright holder
can drop an RFN later, but cannot add one to a name already released without it.

## Open risk, recorded rather than resolved

**A commercial display typeface named `Harena` already exists**, by Rvandtype
(<https://www.myfonts.com/collections/harena-font-rvandtype>).

- It is **not** OFL, so there is no Reserved Font Name conflict.
- `Harena Term` is differentiated by the qualifier.
- But it is the same root name in the **same category**, which is where confusion
  doctrine actually applies. The practical cost is discoverability and citation
  rather than licensing.

Precedent splits: JetBrains reused its application name; Microsoft and GitHub
deliberately did not, shipping `Cascadia Code` and `Monaspace` instead.

**This is cheap to change before a release and expensive after.** It is one
constant in `scripts/build.py` today; once published it breaks every user's
configuration.

## Downstream

The repository is named `harena-term-font` rather than `harena-term`, because
"Term" is a product-category word and the bare name reads as a terminal rather
than as the typeface a terminal sets text in. The family name and the repository
name need not match — `naver/d2-coding-font` ships `D2Coding` — and nothing in
the binaries depends on the repository name.
