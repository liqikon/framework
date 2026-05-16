// KB 스타일 기획 보고서 Typst 템플릿 v2
// 개선: 한글 폰트, 코드블록, 목차

#let report(
  title: "제목",
  subtitle: "",
  description: "",
  project: "",
  date: datetime.today().display("[year]-[month]-[day]"),
  version: "v1.0",
  author: "",
  confidential: true,
  logo: none,
  body
) = {
  // 페이지 설정
  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    numbering: "1",
    number-align: center,
  )

  // 폰트 설정 - Pretendard 우선
  set text(
    font: "Pretendard",
    size: 10pt,
    lang: "ko",
  )

  // 단락 설정
  set par(
    justify: true,
    leading: 0.8em,
  )

  // 제목 스타일 (원본 마크다운에 번호가 있으므로 자동 번호 매기기 비활성화)
  set heading(numbering: none)

  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(0.5em)
    text(size: 18pt, weight: "bold", fill: rgb("#1a1a1a"))[#it]
    v(0.5em)
  }

  show heading.where(level: 2): it => {
    v(0.8em)
    text(size: 14pt, weight: "bold", fill: rgb("#333333"))[#it]
    v(0.4em)
  }

  show heading.where(level: 3): it => {
    v(0.6em)
    text(size: 12pt, weight: "bold", fill: rgb("#444444"))[#it]
    v(0.3em)
  }

  show heading.where(level: 4): it => {
    v(0.5em)
    text(size: 11pt, weight: "bold", fill: rgb("#555555"))[#it]
    v(0.2em)
  }

  // 링크 스타일
  show link: it => text(fill: rgb("#2B579A"))[#underline[#it]]

  // raw/code 스타일 - 한글+박스문자 지원 monospace
  show raw: it => {
    set text(font: "Noto Sans Mono CJK KR", size: 9pt)
    it
  }

  // ============================================
  // 표지 페이지
  // ============================================
  set page(numbering: none)

  v(4cm)

  // 로고
  if logo != none {
    align(center)[
      #image(logo, width: 35%)
    ]
    v(2cm)
  }

  // 대제목
  align(center)[
    #text(size: 28pt, weight: "bold", fill: rgb("#1a1a1a"))[#title]
  ]

  v(0.8cm)

  // 부제목
  if subtitle != "" {
    align(center)[
      #text(size: 18pt, weight: "medium", fill: rgb("#444444"))[#subtitle]
    ]
  }

  v(0.5cm)

  // 설명문
  if description != "" {
    align(center)[
      #text(size: 12pt, fill: rgb("#666666"))[#description]
    ]
  }

  v(3cm)

  // 메타 정보 테이블
  align(center)[
    #block(width: 60%)[
      #table(
        columns: (1fr, 2fr),
        stroke: none,
        inset: 10pt,
        align: (right, left),
        fill: (x, y) => if calc.odd(y) { rgb("#f8f8f8") } else { white },

        [*프로젝트*], [#project],
        [*작성일*], [#date],
        [*버전*], [#version],
        [*작성*], [#author],
      )
    ]
  ]

  v(1fr)

  // 기밀 문구
  if confidential {
    align(center)[
      #text(size: 10pt, fill: rgb("#999999"))[Confidential - Internal Use Only]
    ]
  }

  v(2cm)

  // ============================================
  // 목차 페이지
  // ============================================
  pagebreak()
  set page(numbering: "1")
  counter(page).update(1)

  text(size: 18pt, weight: "bold")[목차]
  v(1em)

  outline(
    title: none,
    indent: 1.5em,
    depth: 3,
  )

  // ============================================
  // 본문
  // ============================================
  pagebreak()

  body
}

// ============================================
// 커스텀 컴포넌트
// ============================================

// 정보 박스
#let infobox(title: "", body) = {
  block(
    fill: rgb("#F0F4F8"),
    stroke: (left: 4pt + rgb("#2B579A")),
    inset: 12pt,
    radius: (right: 4pt),
    width: 100%,
  )[
    #if title != "" {
      text(weight: "bold", fill: rgb("#2B579A"), size: 10pt)[#title]
      parbreak()
    }
    #body
  ]
}

// 경고 박스
#let warningbox(title: "", body) = {
  block(
    fill: rgb("#FFF8E1"),
    stroke: (left: 4pt + rgb("#FF9800")),
    inset: 12pt,
    radius: (right: 4pt),
    width: 100%,
  )[
    #if title != "" {
      text(weight: "bold", fill: rgb("#E65100"), size: 10pt)[#title]
      parbreak()
    }
    #body
  ]
}

// 플로우 다이어그램
#let flowdiagram(caption: "", ..steps) = {
  let items = steps.pos()

  align(center)[
    #block(
      inset: 16pt,
    )[
      #for (i, step) in items.enumerate() {
        box(
          fill: rgb("#E3F2FD"),
          stroke: 1pt + rgb("#2B579A"),
          inset: 10pt,
          radius: 4pt,
        )[#text(size: 9pt)[#step]]

        if i < items.len() - 1 {
          h(0.3em)
          text(size: 12pt, fill: rgb("#2B579A"))[→]
          h(0.3em)
        }
      }
    ]

    #if caption != "" {
      v(0.3em)
      text(size: 9pt, fill: rgb("#666666"), style: "italic")[#caption]
    }
  ]
}

// 키워드 태그
#let tag(body) = {
  box(
    fill: rgb("#E8EAF6"),
    stroke: 0.5pt + rgb("#3F51B5"),
    inset: (x: 6pt, y: 3pt),
    radius: 10pt,
  )[#text(size: 8pt, fill: rgb("#3F51B5"))[#body]]
}

// 하이라이트
#let hl(body) = {
  box(
    fill: rgb("#FFF59D"),
    inset: (x: 2pt, y: 0pt),
    outset: (y: 2pt),
    radius: 2pt,
  )[#body]
}
