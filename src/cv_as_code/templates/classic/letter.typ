// classic — cover-letter template. Exports letter(data).
// data (from letter.resolved.json): {
//   meta: { draft, language },
//   identity: { full_name, headline, location, email, phone, links[] },
//   date: string, paragraphs: [string, ...]
// }
// Same header/branding as the CV template for visual consistency.

#import "../lib/common.typ": *

#let letter(data) = {
  let id = data.identity

  set document(title: id.full_name + " — Cover letter", author: id.full_name)
  set page(
    paper: "a4",
    margin: (x: 2cm, top: 1.6cm, bottom: 1.6cm),
    background: if data.meta.draft {
      place(center + horizon,
        rotate(-28deg, text(size: 100pt, weight: "bold", fill: rgb(32, 69, 107, 18))[DRAFT]))
    },
  )
  set text(font: ("Lato", "Liberation Sans", "DejaVu Sans"),
           size: 10.5pt, fill: luma(25), lang: data.meta.language)
  set par(justify: true, leading: 0.62em, spacing: 0.9em)
  show link: set text(fill: accent)

  // ---- header (matches the CV) ----
  block(text(size: 20pt, weight: "bold", fill: accent)[#id.full_name])
  v(-4pt)
  block(text(size: 11pt, fill: luma(45), tracking: 1pt)[#upper(id.headline)])
  v(2pt)
  {
    let parts = (id.location, link("mailto:" + id.email)[#id.email])
    if id.phone != none { parts.push(id.phone) }
    for lnk in id.links { parts.push(link(lnk.url)[#lnk.label]) }
    block(text(size: 9pt, fill: luma(55), parts.join("  ·  ")))
  }
  v(3pt)
  line(length: 100%, stroke: 0.6pt + accent)
  v(10pt)

  // ---- date ----
  align(right, text(fill: luma(80), size: 9.5pt, data.date))
  v(6pt)

  // ---- body ----
  for p in data.paragraphs {
    par(p)
  }
}
