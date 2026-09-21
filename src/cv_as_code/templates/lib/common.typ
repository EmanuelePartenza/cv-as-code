// Shared primitives for CV templates (templates/lib/common.typ).
// Layout helpers only — zero content, zero language strings.

#let accent = rgb("#20456b")

// A section heading with an underline rule.
#let section-title(label) = {
  v(5pt)
  text(size: 10.5pt, weight: "bold", fill: accent, tracking: 0.8pt)[#upper(label)]
  v(1pt)
  line(length: 100%, stroke: 0.6pt + accent)
  v(3pt)
}

// One experience/project entry header: role (+ optional org) on the left,
// dates on the right, on a single baseline.
#let entry-header(role, org, dates) = {
  grid(
    columns: (1fr, auto),
    align: (left + bottom, right + bottom),
    {
      text(weight: "bold", role)
      if org != none and org != "" [ #text(fill: luma(70))[— #org] ]
    },
    text(fill: luma(95), size: 9pt, dates),
  )
}

// A bullet list from an array of strings.
#let bullets(items) = {
  if items.len() > 0 {
    list(indent: 2pt, spacing: 3pt, ..items)
  }
}
