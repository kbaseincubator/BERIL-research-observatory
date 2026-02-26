# Type Mapping Reference

## Python / openpyxl Type → LinkML Range

When reading Excel files with `openpyxl`, cell values have Python types. Map them to LinkML ranges:

| Python Type (`type(cell.value)`) | LinkML Range | Notes |
|----------------------------------|-------------|-------|
| `str` | `string` | Default; check patterns below for refinement |
| `int` | `integer` | |
| `float` | `float` | Use `decimal` if precision matters |
| `bool` | `boolean` | |
| `datetime.datetime` | `datetime` | Full timestamp |
| `datetime.date` | `date` | Date only |
| `datetime.time` | `time` | Time only |
| `NoneType` | — | Skip; infer from non-null values in same column |

### Mixed-Type Columns

If a column has mixed types (e.g., some `int`, some `str`):
1. If >80% of non-null values are numeric → use `integer` or `float`.
2. Otherwise → use `string`.
3. Note: Excel sometimes stores numbers as strings; try `int(val)` / `float(val)` first.

## String Pattern Detection

When a column is `str`, inspect sample values to detect more specific ranges:

| Pattern | Regex | LinkML Range | Additional |
|---------|-------|-------------|------------|
| Email | `^[\w.+-]+@[\w-]+\.[\w.]+$` | `string` | Add `pattern: "^\\S+@[\\S+\\.]+\\S+"` |
| URL | `^https?://` | `uri` | |
| ISO Date | `^\d{4}-\d{2}-\d{2}$` | `date` | |
| ISO Datetime | `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}` | `datetime` | |
| UUID | `^[0-9a-f]{8}-[0-9a-f]{4}-` | `string` | Add `pattern` for UUID |
| CURIE | `^\w+:\w+` | `uriorcurie` | e.g., `GO:0008150`, `CHEBI:12345` |
| Integer string | `^\d+$` (all values) | `integer` | Cast column to integer |
| Float string | `^\d+\.\d+$` (all values) | `float` | Cast column to float |
| Boolean string | All values in `{true,false,yes,no,0,1}` | `boolean` | |

### Detection Priority

Apply checks in this order (first match wins):
1. UUID
2. ISO Datetime
3. ISO Date
4. URL / URI
5. CURIE
6. Email
7. Integer string
8. Float string
9. Boolean string
10. Default `string`

## Enum Detection Heuristics

A string column is likely an enum when **all** of these are true:

| Criterion | Threshold |
|-----------|-----------|
| Distinct non-null values | ≤ 10 |
| Max value length | ≤ 50 characters |
| Cardinality ratio (distinct / total non-null) | ≤ 0.1 (for columns with 20+ rows) |
| Values are non-numeric | Not parseable as int/float |

### Enum Naming

- Enum name: `{SlotName}Enum` in CamelCase (e.g., column `sample_type` → `SampleTypeEnum`)
- Permissible values: convert to `snake_case`, strip whitespace, replace spaces with underscores

### Examples

| Column Values | Enum? | Reasoning |
|---------------|-------|-----------|
| `["red", "blue", "green"]` | Yes | 3 distinct, short strings |
| `["pending", "active", "inactive", "archived"]` | Yes | 4 status values |
| `["John", "Jane", "Bob", ...]` (50 distinct) | No | Too many distinct values |
| `[1, 2, 3, 4, 5]` | No | Numeric values |
| `["Sample_001", "Sample_002", ...]` | No | High cardinality, looks like IDs |

## Identifier Detection

A column is likely an identifier when:

| Rule | Description |
|------|-------------|
| Name match | Column named `id`, `ID`, `*_id`, `identifier`, `key`, `code` |
| Uniqueness | All non-null values are unique (no duplicates) |
| Non-null | No null/empty values in the column |
| Not an enum | Fails enum detection (too many distinct values) |

### Identifier Slot Properties

```yaml
my_id:
  identifier: true
  range: string        # or uriorcurie if values look like CURIEs
  required: true
```

## Relationship Detection

A column references another class when:

| Rule | Description |
|------|-------------|
| Name match | Column named `{other_sheet}_id` or `{other_sheet}` (singular of sheet name) |
| Value overlap | Column values are a subset of another sheet's identifier column |
| Foreign key pattern | Column named `*_id` and a matching sheet/class exists |

### Relationship Slot Properties

```yaml
# Single reference (many-to-one)
project_id:
  range: Project       # the referenced class name
  required: true

# Multiple references (many-to-many)
related_samples:
  range: Sample
  multivalued: true
```

## Multivalued Detection

A column likely holds multiple values when:

| Rule | Description |
|------|-------------|
| Delimiter-separated | Values contain `;`, `\|`, or `,` followed by space |
| Plural name | Column name ends in `s`, `_list`, `_items`, `_set` |
| List-like strings | Values look like `["a", "b"]` or `a; b; c` |

### Multivalued Slot Properties

```yaml
tags:
  range: string
  multivalued: true

# If referencing another class:
samples:
  range: Sample
  multivalued: true
  inlined_as_list: true
```

## Complete Mapping Example

Given an Excel sheet `Samples` with columns:

| Column | Sample Values | Inferred Type | Reasoning |
|--------|--------------|---------------|-----------|
| `sample_id` | `S001, S002, S003` | `identifier: true, range: string` | Name + unique |
| `name` | `"Blood draw 1", ...` | `string, required: true` | Free text |
| `sample_type` | `"blood", "tissue", "saliva"` | `SampleTypeEnum` | 3 distinct, short |
| `collection_date` | `2024-01-15, ...` | `date` | ISO date pattern |
| `volume_ml` | `5.0, 10.5, 3.2` | `float` | Python float |
| `project_id` | `P001, P002` | `range: Project` | Matches Projects sheet |
| `tags` | `"urgent; priority", ...` | `string, multivalued: true` | Delimiter-separated |
| `url` | `"https://...", ...` | `uri` | URL pattern |
