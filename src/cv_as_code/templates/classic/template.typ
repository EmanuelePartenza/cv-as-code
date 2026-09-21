// classic — single-column CV template.
// Exports cv(data): data is the dict from cv.resolved.json (see
// schemas/cv-resolved.schema.json — the generator↔template contract).
// Zero language strings here: every label arrives resolved inside `data`.

#import "../lib/common.typ": *

#let cv(data) = {
  let L = data.labels
  let id = data.identity

  set document(title: id.full_name + " — " + id.headline, author: id.full_name)
  set page(
    paper: "a4",
    margin: (x: 1.5cm, top: 1.3cm, bottom: 1.1cm),
    background: if data.meta.draft {
      place(center + horizon,
        rotate(-28deg, text(size: 100pt, weight: "bold", fill: rgb(32, 69, 107, 18))[DRAFT]))
    },
  )
  set text(font: ("Lato", "Liberation Sans", "DejaVu Sans"),
           size: 9.6pt, fill: luma(25), lang: data.meta.language)
  set par(justify: true, leading: 0.58em, spacing: 0.6em)
  show link: set text(fill: accent)

  // ---------- header ----------
  block(text(size: 22pt, weight: "bold", fill: accent)[#id.full_name])
  v(-4pt)
  block(text(size: 11.5pt, fill: luma(45), tracking: 1pt)[#upper(id.headline)])
  v(1pt)
  {
    let parts = (id.location, link("mailto:" + id.email)[#id.email])
    if id.phone != none { parts.push(id.phone) }
    for lnk in id.links { parts.push(link(lnk.url)[#lnk.label]) }
    block(text(size: 9pt, fill: luma(55), parts.join("  ·  ")))
  }
  v(1pt)

  // ---------- shared entry renderer ----------
  let render-entries(entries) = {
    for e in entries {
      entry-header(e.role, e.org, e.dates)
      bullets(e.bullets)
      v(3pt)
    }
  }

  // ---------- sections (rendered in data.sections order) ----------
  for s in data.sections {
    if s == "summary" and data.summary != none {
      section-title(L.summary)
      block(data.summary)
    } else if s == "experience" and data.experience.len() > 0 {
      section-title(L.experience)
      render-entries(data.experience)
    } else if s == "projects" and data.projects.len() > 0 {
      section-title(L.projects)
      render-entries(data.projects)
    } else if s == "skills" and data.skills.groups.len() > 0 {
      section-title(L.skills)
      for g in data.skills.groups {
        block(spacing: 4pt)[#text(weight: "bold")[#g.label: ] #g.items.join("  ·  ")]
      }
    } else if s == "education" and data.education.len() > 0 {
      section-title(L.education)
      for e in data.education {
        let org = e.institution
        if e.location != none and e.location != "" { org = org + ", " + e.location }
        entry-header(e.degree, org, e.dates)
        if e.notes != none and e.notes != "" {
          text(size: 9pt, fill: luma(60), style: "italic")[#e.notes]
        }
        v(3pt)
      }
    } else if s == "languages" and data.languages.len() > 0 {
      section-title(L.languages)
      block(data.languages.map(l => [#strong(l.name): #l.level]).join("    ·    "))
    }
  }
}
