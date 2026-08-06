# Harena Term

한글·일본어·영문이 모두 1급 시민인 터미널 고정폭 글꼴. 셀 격자는 정확히 1:2.

[English](README.md) | [日本語](README.ja.md) | **한국어**

![같은 한글 문장을 Sarasa Term K와 Harena Term K로, 같은 셀 너비에서 조판한 비교](docs/specimen.png)

대부분의 CJK 터미널 글꼴은 전각 글자를 한 셀에 맞춰 놓고 자간은 남는 대로 둡니다.
한글에서는 그 결과가 원 제작자가 그린 것보다 훨씬 헐겁습니다 — Sarasa Term K의
자간/획 비율은 `T = 0.264`인데, 비례폭 Pretendard는 `0.1287`로 두 배 넘게 촘촘합니다.

Harena Term은 각 문자 체계를 **고유 폭이 셀에 정확히 떨어지도록** 확대합니다.
`T`는 배율에 불변이므로, 이는 근사가 아니라 원본 자간의 **항등 재현**입니다.
출시 바이너리 실측: 한글 `T = 0.1260`, **Sarasa 대비 52% 더 촘촘**, 격자는 여전히
정확히 1:2.

[Iosevka Term Nerd Font Mono](https://github.com/be5invis/Iosevka)(라틴, 기호,
박스 드로잉, 점자, Powerline, Nerd Font 아이콘)와
[Pretendard JP](https://github.com/orioncactus/pretendard)(한글, 한자, 가나)를
병합해 만들었고, 둘 다 전각으로 그리지 않는 부분은
[M PLUS 1p](https://github.com/coz-m/MPLUS_FONTS)와
[Noto Sans KR](https://github.com/notofonts/noto-cjk)이 채웁니다.

## 내려받기

[**Releases**](../../releases/latest)에서 최신 배포본을 받으세요.

> **1.0.0.** 안정 버전 번호에 걸어둔 세 조건이 모두 충족되었습니다: 실제 배포로
> 검증된 릴리스 워크플로, 0.9.0이 안고 나갔던 획 굵기 결함의
> [해결](docs/adr/0014-the-compensation-target-erases-the-source-relative-weighting.md),
> 그리고 가정이 아니라 [실행하고 측정한](docs/adr/0017-windows-verified.md) Windows.
> 이 번호가 뜻하지 *않는* 것은 남은 게 없다는 뜻입니다 —
> [알려진 한계](CHANGELOG.md#known)는 목록으로 있고, 각각은 실수가 아니라 기록을
> 가진 결정입니다. [1.0까지의 길](CHANGELOG.md#the-road-to-10).

| | |
|---|---|
| `HarenaTerm-ttf.zip` | 데스크톱 — 터미널, 편집기, 워드프로세서 |
| `HarenaTerm-woff2.zip` | 웹 — `@font-face`로 브라우저 기반 터미널에 |

각 압축 파일에 네 벌이 들어 있습니다: `Harena Term K`와 `Harena Term J`의
Regular, Bold.

## 설치

압축을 풀고 시스템 글꼴 설치기를 쓰세요 — macOS는 Font Book, Windows는 파일을
선택해 우클릭 → 설치. 또는 시스템이 찾는 자리에 넣으면 됩니다:

```sh
# macOS
cp *.ttf ~/Library/Fonts/

# Linux
cp *.ttf ~/.local/share/fonts/ && fc-cache -f
```

이 프로젝트는 설치 스크립트를 배포하지 않습니다. OS가 이미 잘 하는 일이고, 그
너머는 우리가 유지보수하고도 모든 플랫폼에서 시험할 수 없는 스크립트보다 패키지
매니저가 낫기 때문입니다 — [ADR 0016](docs/adr/0016-no-install-scripts.md).

## 두 벌: K와 J

한국과 일본은 같은 한자를 다르게 그립니다. 가장 뚜렷한 예가 運 進 週 選 過 達 通 連 遠의
좌하단 책받침 부수로, 한국은 전통적인 두 점을 쓰고 일본 신자체는 한 점을 씁니다.

유니코드는 이들을 **같은 코드포인트**로 부호화합니다. 따라서 차이는 부호화가 아니라
글리프 선택이고, 보통은 언어 태그로 발동하는 OpenType `locl` 기능에 담깁니다.
**터미널은 그 기능에 닿지 못합니다** — 텍스처 아틀라스 렌더러는 평범한 CSS
문자열로 글꼴을 지정하므로 `font-feature-settings`도 언어 태그도 없고, 네이티브
터미널도 실행 단위로 언어를 태깅하는 경우가 거의 없습니다.

그래서 지역 자형을 `cmap`에 구워 넣고 두 벌을 배포합니다.

| | |
|---|---|
| **Harena Term K** | 한국 자형. 한글 위주라면, 또는 잘 모르겠으면 이쪽. |
| **Harena Term J** | 일본 자형. 일본어를 읽는다면 이쪽. |

두 벌은 **37652자 중 611자**만 다르고, 전부 한자 범위 안이며, **폭 차이는
0**입니다. 그래서 한 화면에 섞어 써도 행이 어긋나지 않습니다. 한글, 가나, 라틴,
기호, 박스 드로잉, 점자는 두 벌이 바이트 단위로 동일합니다.

## 수록 범위

**86개 유니코드 블록에 걸쳐 37652 코드포인트**, 한 벌당 38478 글리프. 블록별
출처는 [`docs/COVERAGE.md`](docs/COVERAGE.md)에 전부 있습니다.

| | |
|---|---|
| 한글 음절 | **11172자 완비**, 더해 조합형 자모 67자 |
| 한자 | **7138자** — JIS X 0208, cp932, KS X 1001 완비 |
| 가나 | 히라가나 90, 가타카나 94, 반각 가타카나 63 |
| 점자 | **256/256** — 에이전트 TUI가 스피너를 이걸로 그립니다 |
| 박스 드로잉 / 블록 / 도형 / 화살표 | 128 · 32 · 96 · 112 |
| Nerd Font 아이콘 | Powerline, Font Awesome, Devicons, Octicons, Material 등 |
| 코드페이지 | cp932 **100%**, cp949 **99.98%** |

이 글꼴은 **NFD 한글을 스스로 조합**합니다 — `ccmp` 합자 11172개로. macOS는
파일 이름을 NFD로 저장하므로 `ls` 목록의 모든 한글 파일명이 조합형 자모로
들어옵니다. 이걸 셰이퍼에 맡기는 글꼴은 CoreText에서 자모가 겹쳐 그려집니다.

### 읽어둘 호환성 사항 하나

글자 폭은 xterm.js `unicode11` 제공자가 구현한 Unicode 11 East Asian Width 표를
따릅니다. 이 표는 **Ambiguous 폭 문자를 한 셀로** 해석합니다 — `♥ ○ → ± ′` 외
1197자.

터미널을 `ambiguous = wide`로 설정하면 그 문자들에 **두 셀**을 예약하는데 이
글꼴은 한 셀로 그리므로 해당 행이 어긋납니다. Sarasa는 반대로 선택했습니다.
글꼴은 글리프마다 폭이 하나뿐이라 양쪽을 다 만족시킬 수 없습니다. 터미널이
`ambiguous = wide`라면 이 글꼴은 맞지 않습니다.

## 직접 빌드하기

빌드는 **고정된 소스로부터 바이트 단위로 재현 가능**하며, 산출물 여덟 개의 해시가
`SHA256SUMS`에 기록되어 있습니다.

```sh
pip install -r requirements.txt
pnpm install
scripts/fetch_sources.sh      # 고정 URL, SHA-256 검증, 라틴 빌드까지
python3 scripts/build.py      # 라틴과 CJK를 격자에 병합
python3 scripts/postbuild.py  # 힌팅, 재스탬프, WOFF2, SHA256SUMS
python3 scripts/verify.py     # 게이트
cd dist && sha256sum -c ../SHA256SUMS
```

`verify.py`는 **보고하지 않고 단언합니다** — 종료 코드가 곧 게이트입니다. 네 벌에
걸쳐 **158개 검사**를 돌립니다: 모든 폭을 바이너리에서 다시 유도해 폭 제공자 표와
대조(수록된 21349 코드포인트 전부), 모든 전각 글리프의 셀 초과 검사, NFD 음절
11172개를 `ccmp` 합자 트리로 직접 순회, 자간과 한글/한자 획 굵기 비율을 Pretendard
원본과 대조, `OS/2` 문자 체계 선언, 그리고 출시 바이트에 찍힌 재현성 스탬프까지.

`SOURCE_DATE_EPOCH`로 빌드 스탬프를 덮어쓸 수 있습니다. CI가 매 푸시마다 전체
순서를 실행하고 해시를 검사합니다.

각 선택의 이유는 — 그것을 결정지은 실측값과, 그것을 다시 열어야 할 조건과 함께 —
[`PLAN.md`](PLAN.md)와 [`docs/adr/`](docs/adr/)에 있습니다.

## 출처

이 글꼴은 병합물입니다. 그려진 것은 전부 다른 사람이 그렸고, 여기서 새로 만든
것은 맞춤과 격자와 게이트입니다. [`docs/LINEAGE.md`](docs/LINEAGE.md)가 각 소스가
거쳐온 모든 손을 추적합니다.

| | 그린 이 | 여기서 그리는 것 |
|---|---|---|
| [Iosevka](https://github.com/be5invis/Iosevka) | Belleve Invis | 라틴, 기호, 박스 드로잉, 점자 |
| [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) | Ryan L McIntyre 외 기여자 | 아이콘 세트 |
| [Pretendard JP](https://github.com/orioncactus/pretendard) | 길형진 | 한글, 한자, 가나 |
| [M PLUS 1p](https://github.com/coz-m/MPLUS_FONTS) | Coji Morishita | 괄호류, 반각 가타카나, 〇 〒 〓 |
| [Noto Sans KR](https://github.com/notofonts/noto-cjk) | Adobe / Google | 원문자·사각 단위, 옛 자모 |

Pretendard의 name 테이블은 라틴을 Inter, 한글과 한자를 Noto Sans CJK(Source Han
Sans), 가나를 M PLUS 1p로 밝히고 있습니다. 그래서 몇몇은 계보에 두 번 나옵니다 —
한 번은 직접, 한 번은 Pretendard를 거쳐서.

## 라이선스

JetBrains Mono와 Nerd Fonts를 따라, **무엇이냐에 따라** 나눕니다.

| | 적용 대상 |
|---|---|
| [`OFL.txt`](OFL.txt) — SIL Open Font License 1.1 | **글꼴 자체.** 배포 산출물과 이 트리에서 빌드한 모든 것 |
| [`LICENSE`](LICENSE) — Apache License 2.0 | **빌드 시스템.** 스크립트, 빌드 플랜, 문서 |
| [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) + [`licenses/`](licenses/) | 둘 중 어느 쪽도 아닌 Nerd Fonts 아이콘 세트. 일부는 MIT나 CC-BY-4.0이고 두 개는 저작자 표시가 필요합니다 |

**`Harena Term`은 OFL의 예약 글꼴 이름(Reserved Font Name)입니다.** 글꼴을
자유롭게 수정·재배포할 수 있지만, 수정본은 다른 이름을 써야 합니다.

Copyright © 2026 Jeeyong Um. 상위 소스의 저작권 표시는 OFL §2가 요구하는 대로
`OFL.txt`에 유지되어 있습니다.
