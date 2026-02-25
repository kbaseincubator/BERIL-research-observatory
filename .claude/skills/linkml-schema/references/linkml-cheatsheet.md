# LinkML Schema YAML Cheatsheet

## Minimal Valid Schema

```yaml
id: https://w3id.org/my_schema
name: my_schema
prefixes:
  linkml: https://w3id.org/linkml/
  my_schema: https://w3id.org/my_schema/
imports:
  - linkml:types
default_range: string

classes:
  MyClass:
    attributes:
      id:
        identifier: true
      name:
        required: true
```

## Schema-Level Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | URI identifier for the schema (e.g., `https://w3id.org/my_schema`) |
| `name` | Yes | Short name, `snake_case` |
| `prefixes` | Yes | At minimum `linkml` prefix; add schema prefix for CURIEs |
| `imports` | Yes | Always include `linkml:types` for built-in types |
| `default_range` | No | Default type for slots without explicit range (usually `string`) |
| `description` | No | Human-readable description of the schema |
| `default_prefix` | No | Default prefix for CURIEs in this schema |

## Class Definition

```yaml
classes:
  Person:
    description: "A human being"
    is_a: NamedThing          # single inheritance
    mixins:                   # multiple inheritance via mixins
      - HasAliases
    tree_root: true           # marks this as the container/root class
    attributes:               # inline slot definitions (preferred for simple schemas)
      id:
        identifier: true
        range: uriorcurie
      full_name:
        required: true
        range: string
      age:
        range: integer
        minimum_value: 0
    slots:                    # reference to top-level slot definitions
      - email
```

### Class Fields

| Field | Description |
|-------|-------------|
| `description` | Human-readable description |
| `is_a` | Parent class (single inheritance) |
| `mixins` | List of mixin classes |
| `tree_root` | `true` if this is the root/container class |
| `attributes` | Inline slot definitions (scoped to this class) |
| `slots` | References to top-level `slots:` section |
| `abstract` | `true` if class cannot be instantiated directly |

## Slot Definition

Slots can be defined inline under `attributes:` or at the top level under `slots:`.

```yaml
slots:
  email:
    description: "Email address"
    range: string
    pattern: "^\\S+@[\\S+\\.]+\\S+"
    required: false
  birth_date:
    range: date
  has_samples:
    range: Sample
    multivalued: true
    inlined_as_list: true
```

### Slot Fields

| Field | Type | Description |
|-------|------|-------------|
| `range` | string | Target type or class name |
| `required` | boolean | Whether the slot must have a value |
| `identifier` | boolean | `true` if this is the unique identifier for the class |
| `multivalued` | boolean | `true` if the slot can hold a list |
| `inlined` | boolean | `true` to nest the object inline (for object ranges) |
| `inlined_as_list` | boolean | `true` to inline as a list instead of a dict |
| `pattern` | string | Regex pattern the value must match |
| `minimum_value` | number | Minimum numeric value |
| `maximum_value` | number | Maximum numeric value |
| `description` | string | Human-readable description |
| `comments` | list | Additional comments |
| `examples` | list | Example values (`- value: "..."`) |
| `recommended` | boolean | `true` if slot should ideally be filled |
| `deprecated` | string | Deprecation notice |
| `ifabsent` | string | Default value expression |

## Built-in Types

Always available after `imports: [linkml:types]`.

| LinkML Type | Python | JSON Schema | Description |
|------------|--------|-------------|-------------|
| `string` | `str` | `string` | Text |
| `integer` | `int` | `integer` | Whole number |
| `float` | `float` | `number` | Decimal number |
| `double` | `float` | `number` | Double-precision float |
| `decimal` | `Decimal` | `number` | Arbitrary precision decimal |
| `boolean` | `bool` | `boolean` | True/false |
| `date` | `date` | `string` (format: date) | ISO 8601 date (YYYY-MM-DD) |
| `datetime` | `datetime` | `string` (format: date-time) | ISO 8601 datetime |
| `time` | `time` | `string` (format: time) | ISO 8601 time |
| `uri` | `URI` | `string` (format: uri) | Full URI |
| `uriorcurie` | `URIorCURIE` | `string` | URI or CURIE |
| `curie` | `Curie` | `string` | Compact URI (prefix:local) |
| `ncname` | `NCName` | `string` | XML NCName |

## Enum Definition

```yaml
enums:
  SampleTypeEnum:
    description: "Type of biological sample"
    permissible_values:
      blood:
        description: "Whole blood sample"
      tissue:
        description: "Tissue biopsy"
      saliva:
        description: "Saliva sample"
      urine:
        description: "Urine sample"
```

### Enum Fields

| Field | Description |
|-------|-------------|
| `description` | Human-readable description of the enum |
| `permissible_values` | Map of value name → metadata |
| `permissible_values.*.description` | Description of individual value |
| `permissible_values.*.meaning` | Ontology term CURIE (e.g., `OBI:0000880`) |

## Common Patterns

### One-to-Many Relationship

```yaml
classes:
  Project:
    attributes:
      id:
        identifier: true
      samples:
        range: Sample
        multivalued: true
        inlined_as_list: true

  Sample:
    attributes:
      id:
        identifier: true
      project_id:
        range: Project
```

### Foreign Key Reference

```yaml
classes:
  Observation:
    attributes:
      sample_id:
        range: Sample       # references the Sample class
        required: true
```

### Container / Root Class

```yaml
classes:
  Database:
    tree_root: true
    attributes:
      projects:
        range: Project
        multivalued: true
        inlined_as_list: true
      samples:
        range: Sample
        multivalued: true
        inlined_as_list: true
```

### Identifier Slot

```yaml
classes:
  NamedThing:
    abstract: true
    attributes:
      id:
        identifier: true
        range: uriorcurie
        required: true
      name:
        range: string
```

## CLI Validation Commands

```bash
# Validate schema structure
linkml-validate -s schema.yaml

# Validate data against a schema
linkml-validate -s schema.yaml data.yaml

# Generate JSON Schema from LinkML
gen-json-schema schema.yaml > schema.json

# Generate Python dataclasses
gen-python schema.yaml > model.py
```
