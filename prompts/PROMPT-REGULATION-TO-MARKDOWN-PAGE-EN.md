Task:
Convert the entire content of the provided PDF — a legal document such as a Law, Government Regulation, Ministerial Decree, Regional Regulation, Contract, or MOU — into a clean, complete Markdown (.md) file with a strict legal heading hierarchy. Preserve the original language. Output is intended for legal archiving, compliance, audit trails, and AI retrieval (RAG).

---

# 1. PDF Page Markers (MANDATORY)
Insert a page marker at the start of **every** PDF page to maintain traceability.

**Required format:**
```
<!-- page: X -->
```
Where `X` is the original PDF page number.

**Rules:**
- Place the marker before the first content line of each page.
- Insert markers even for pages with minimal text, cover pages, or signature pages.
- Insert a marker even when a paragraph, article, or table is split across a page break — do not wait for a clean break.
- Do **not** use any other format. `[PAGE 1]`, `(Page 1)`, `PAGE:1` are all **invalid**.
- Use **only**: `<!-- page: X -->`

**Example:**
```markdown
<!-- page: 1 -->

# LAW OF THE REPUBLIC OF INDONESIA NUMBER 1 OF 2016

<!-- page: 2 -->

## CONSIDERING

Whereas the state...

<!-- page: 3 -->

## CHAPTER I — GENERAL PROVISIONS

### Article 1
```

---

# 2. Content Completeness
- Transcribe the **entire document** verbatim — do not summarize, shorten, or paraphrase any section.
- Include all: preambles (Menimbang/Mengingat/Considering/Recalling), chapters, articles, clauses, paragraphs, annexes, and signature blocks.
- The Table of Contents does **not** need to be transcribed — Markdown heading structure replaces it.

---

# 3. Legal Heading Structure
Use this hierarchy consistently. It is critical for RAG indexing and legal citation.

| Level | Element | Format |
|-------|---------|--------|
| `#` | Document title | ALL CAPS |
| `##` | Preamble sections, DECIDING, Chapters | `## CHAPTER I — GENERAL PROVISIONS` |
| `###` | Parts / Sections (Bagian) | `### Part One — Scope` |
| `####` | Articles / Clauses | `#### Article 1` |

- **Paragraphs (Ayat/Clauses):** plain paragraph with numbering, e.g.: `(1) This law applies to...`
- **Letters:** `a. ...`, `b. ...`
- **Sub-letters:** `1. ...`, `2. ...`
- Do NOT convert article numbers into Markdown bullet points (`-` or `*`).

**Correct example:**
```markdown
## CHAPTER II — SCOPE

#### Article 3

(1) This regulation applies to:
    a. Civil servants;
    b. Contract employees.

(2) Excluded from scope are...
```

---

# 4. Tables and Annexes

## 4a. Table Detection
- Treat any grid of rows and columns as a table, including fee schedules, sanction tables, signatory blocks, and annexes — regardless of whether they use visible borders or just whitespace alignment in the PDF.
- Do **not** convert a table into a bullet list or paragraph.

## 4b. Table Formatting Rules
- Always output tables as standard GitHub-Flavored Markdown (GFM) pipe tables.
- The **first row** is always the header row, separated from data rows by a `|---|` divider line.
- Every column must have an entry in every row — use an empty cell (`|  |`) for blank cells, never skip columns.
- Preserve column order exactly as in the source.
- Keep all numeric values, units, currency, and footnote markers exactly as written.

**Correct example:**
```markdown
| No | Description              | Amount (IDR) |
|----|--------------------------|--------------|
| 1  | Registration fee         | 500,000      |
| 2  | Annual renewal fee       | 250,000      |
```

## 4c. Complex or Merged-Cell Tables
- If a table has multi-level column headers, flatten it: merge sub-header names into each column header, e.g. `| Region - North | Region - South |`.
- If merged rows span multiple data rows, repeat the merged-cell value in each affected row.

## 4d. Tables Spanning Page Breaks
- Insert the `<!-- page: X -->` marker between rows at the page break.
- Do **not** split one table into two separate tables — continue the same table across the marker.

**Example:**
```markdown
| No | Name    | Value |
|----|---------|-------|
| 1  | Item A  | 100   |

<!-- page: 5 -->

| 2  | Item B  | 200   |
```

## 4e. Annexes
- **Annexes with figures/maps:** Insert a placeholder: `[Annex I — refer to source PDF page X]`
- **Long text-only annexes:** Transcribe fully under `## ANNEX I — <TITLE>`.
- **Annexes that are entirely a table:** apply all rules in 4b–4d.

---

# 5. Cross-References
Where the document refers to other regulations, format as a wiki-link when possible:
- `[[2011-uu-12|Law Number 12 of 2011]]`
- Internal references (e.g., "as referred to in Article 5 paragraph (2)") — leave as-is.

---

# 6. OCR and Text Correction
- Fix clearly broken OCR characters (e.g., `G0vernment` → `Government`, `lndonesia` → `Indonesia`).
- Rejoin words split by line or page hyphenation.
- Do **not** guess or reconstruct text that is illegible — leave a note: `[illegible]`.
- Preserve original legal spelling, punctuation, and article numbering exactly.

---

# 7. Suggested Filename
At the very end of your output, after the last line of Markdown content, append a single line in this format:

```
<!-- suggested-filename: {year}-{type_short}-{number}-{subject-slug}.md -->
```

Slug rules: kebab-case, all lowercase, max 80 characters, remove stop words (di, ke, dan, dari, untuk, yang, the, of, and, for).

*Examples:*
```
<!-- suggested-filename: 2016-uu-1-penjaminan.md -->
<!-- suggested-filename: 2024-mou-pemda-bpk-pengelolaan-keuangan.md -->
<!-- suggested-filename: 2023-perda-papua-prov-3-retribusi-daerah.md -->
```

---

# 8. Prohibited
- Do NOT summarize, omit, or reorder any article or clause.
- Do NOT add legal interpretation, commentary, or analysis.
- Do NOT convert article numbering into generic Markdown bullets.
- **NEVER** include opening remarks, closing remarks, or filler phrases (e.g., "Sure, here is the result...").
- Output **only** raw Markdown. No preamble. No postamble. Start directly with `<!-- page: 1 -->`.
