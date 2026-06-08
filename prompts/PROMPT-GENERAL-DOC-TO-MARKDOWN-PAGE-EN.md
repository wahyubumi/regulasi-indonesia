Task:
Convert the entire content of the provided PDF document into a clean, well-structured Markdown (.md) file with a consistent heading hierarchy. The document may be in any language — preserve the original language throughout. Output is intended for knowledge base archiving and AI retrieval (RAG).

---

# 1. Content Completeness
- Preserve all content from the source document verbatim — do not summarize or paraphrase.
- Do not omit paragraphs, tables, or key points.
- Transcribe the Table of Contents as-is.

# 2. PDF Page Markers (MANDATORY)
To maintain traceability to the original PDF, insert a page marker at the start of **every** PDF page.

**Required format:**
```
<!-- page: X -->
```
Where `X` is the original PDF page number.

**Rules:**
- Place the marker before the first content of each page.
- Insert a marker on every page break, even if the page has minimal text.
- Insert a marker even when a paragraph or table is split across a page break.
- Do not omit markers for blank or near-blank pages.
- Do **not** use any other format — `[PAGE 1]`, `(Page 1)`, `PAGE:1`, `<page>1</page>` are all **invalid**.
- Use **only**: `<!-- page: X -->`

**Example:**
```markdown
<!-- page: 1 -->

# Document Title
Opening paragraph...

<!-- page: 2 -->

## CHAPTER I

Chapter content...
```

Page markers are **non-negotiable** and must appear in the final output without exception.

# 3. Heading Structure
Use a strict, logical heading hierarchy — critical for RAG indexing:

- `#` → Document title (exactly one H1, at the very top).
- `##` → Main chapters or major sections (e.g., INTRODUCTION, METHODOLOGY, CONCLUSION).
- `###` → Sub-sections.
- `####` → Sub-sub-sections.

Apply standard Markdown formatting:
- **Bold** and *italic* matching the emphasis in the source.
- Unordered lists: `-` or `*`.
- Ordered lists: `1.`, `2.`, etc.

# 4. Tables and Figures

## 4a. Table Detection
- Treat any grid of rows and columns as a table, regardless of whether it uses visible borders or is represented by whitespace/tab alignment in the PDF text.
- Do not convert a table into a paragraph or bullet list unless explicitly instructed.

## 4b. Table Formatting Rules
- Always output tables as standard GitHub-Flavored Markdown (GFM) pipe tables.
- The **first row** is always the header row, separated from data rows by a `|---|` divider line.
- Every column **must** have an entry in every row — use an empty cell (`|  |`) for blank cells, never skip columns.
- Do **not** merge or join cells; represent merged-cell spans by repeating the value in each affected cell and adding a note if needed.
- Preserve the column order exactly as it appears in the source.
- Keep all numeric values, units, and footnote markers exactly as written.

**Correct example:**
```markdown
| No | Name          | Amount  |
|----|---------------|---------|
| 1  | Item A        | 100,000 |
| 2  | Item B        |         |
```

**Incorrect (do not do this):**
```
No  Name     Amount
1   Item A   100,000
2   Item B
```

## 4c. Complex or Nested Tables
- If a table has nested sub-headers (multi-level column headers), flatten it: promote sub-headers as separate columns, and note the original grouping in the header name, e.g. `| Region - North | Region - South |`.
- If a table contains a sub-table inside a cell, extract it as a separate table immediately after the parent table, with a label: `*Sub-table from row N above:*`

## 4d. Tables Spanning Page Breaks
- If a table continues across a page break, insert the `<!-- page: X -->` marker between the last row of the previous page and the first row of the next page.
- Do **not** split the table into two separate tables — continue the same table across the marker.

## 4e. Figures and Charts
- **Figures/Charts:** Insert a descriptive placeholder, e.g.: `[Figure 1: Revenue growth chart — refer to original PDF page X]`.

# 5. OCR Correction
- Fix clearly broken OCR characters (e.g., `G0vernment` → `Government`, `rn` misread as `m`).
- Rejoin words broken by line or page hyphenation.

# 6. Prohibited
- Do not summarize, shorten, or omit any section.
- **NEVER** include opening remarks, closing remarks, greetings, or filler phrases (e.g., "Sure, here is the result...").
- Output **only** raw Markdown. No preamble. No postamble.
