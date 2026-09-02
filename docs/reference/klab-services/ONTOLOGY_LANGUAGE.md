# Worldview ontology language guide

This file is a user-level introduction and reference for the k.LAB worldview ontology language,
whose source files use the `.kwv` extension. It is intended for worldview authors, reviewers,
maintainers, and contributors who need to understand how ontology source becomes executable
semantics in the current k.LAB service stack.

The current Xtext grammar is the authority for accepted source syntax. It lives in the sibling
`klab-languages` repository at
`org.integratedmodelling.languages.worldview/src/org/integratedmodelling/languages/Worldview.xtext`.
The `KimOntology`, `KimConceptStatement`, and `KimConcept` interfaces in `klab.core.api` define
the portable semantic contract after parsing. The `KimOntologyVisitor` and the Reasoner service
show how parsed ontologies are traversed and loaded. Historical worldview files and the older
technical note may use obsolete syntax; use them for domain knowledge, not as the source-syntax
authority.

The three main user-facing languages instrument different parts of the k.LAB stack:

| Language | Extension | Principal role |
| --- | --- | --- |
| Worldview ontology language | `.kwv` | Defines the shared concepts, distinctions, and inference structure of a worldview |
| [k.IM](KIM.md) | `.kim` | Publishes contextual observation strategies by connecting observables to data and computation |
| [k.Actors](AGENTS.md) | `.kactor` | Gives observations, digital twins, users, and sessions reactive behavior |

All three inherit the same [observable expression language](OBSERVABLES.md),
which is k.LAB's semantic query and asset-description syntax. Worldview and
k.IM sources use it directly and may also pass full expressions as
`{{ ... }}` semantic literals; k.Actors uses only the literal form.

## 1. What the worldview language is for

A k.LAB worldview is the common semantic basis used to state observable meaning. It is a modular,
versioned collection of ontologies that defines:

- the kinds of entities, qualities, processes, events, relationships, and predicates that can be
  observed;
- how those concepts specialize or equal other concepts;
- where predicates may apply and what relationships may connect;
- what concepts create, affect, imply, classify, or otherwise describe;
- which distinctions form complete or disjoint child sets;
- which external authority or foundational ontology anchors a concept.

The language does not publish datasets or algorithms. That is the role of k.IM models and the
resource layer. It also does not prescribe event-handling behavior. That is the role of k.Actors
and the runtime layer. A `.kwv` file supplies the semantic rails that make both layers
interoperable.

In service terms:

```text
.kwv source
  -> Resources service parses and distributes a KimOntology
  -> Reasoner loads the ontology into the active worldview
  -> concepts and axioms constrain observable interpretation
  -> Resolver can compare and mediate k.IM strategies by meaning
  -> Runtime observations retain that meaning in the digital twin
```

The language is deliberately more operational than a glossary. Concept types and clauses affect
validation and inference, so changes to a worldview can change which models resolve, which
mediations are valid, and how observations are structured.

## 2. A minimal ontology

```kwv
ontology hydrology
    "Core hydrological concepts for the shared worldview."
    using imod, earth
    in domain imod:Knowledge of imod:Hydrosphere
    version 1.0
;

process WaterFlow
    "Movement of water through a hydrological system."
    is imod:Process
;

volume WaterVolume
    "A volume of water associated with a hydrological subject."
    is imod:Volume
    within earth:Region
;

process Runoff
    "Water flow over land toward a receiving water body."
    is hydrology:WaterFlow
    creates hydrology:WaterVolume
;
```

The preamble names and versions the ontology, imports the ontologies it references, and places it
in a worldview domain. Each following statement declares one concept and ends with a semicolon.

Whitespace and indentation are not semantically significant, but clauses should be placed on
separate lines for reviewability. Xtext's standard single-line `//` and multi-line `/* ... */`
comments are accepted.

## 3. Ontology preamble

The general shape is:

```kwv
ontology <name>
    ["Human-readable description"]
    [using <ontology> [, <ontology> ...]]
    in domain (<concept-expression> | root [with core <core-ontology> [, ...]])
    version <version>
    [metadata <map>]
;
```

`in domain` and `version` are mandatory. `using` and the description are optional. The grammar
uses an unordered group for `using`, `in domain`, and `version`, so those clauses may appear in
any order. Consistent projects should still adopt one order; this guide uses imports, domain, then
version.

Ontology names are lowercase identifiers or dot-separated lowercase namespace paths:

```kwv
ontology ecology
ontology ecology.freshwater
```

Metadata, when present, follows the preamble clauses and precedes the semicolon:

```kwv
ontology ecology.freshwater
    "Freshwater ecological concepts."
    using ecology, hydrology
    in domain imod:Knowledge of imod:Hydrosphere
    version 1.2.0
    metadata {
        dc.creator: "Freshwater domain group"
        status: "review"
    }
;
```

### 3.1. Imports

`using` imports complete ontology namespaces:

```kwv
using imod, earth, ecology
```

Selective symbol imports are not part of the worldview grammar. Every imported ontology must be
available before this ontology can be fully resolved and loaded. Avoid circular imports and avoid
imports made only for convenience: dependencies are part of worldview load order and should
express real semantic reliance.

### 3.2. Domain ontologies

Most ontologies are located in a domain expressed with the shared observable grammar:

```kwv
in domain imod:Knowledge of imod:Biosphere
```

The domain says which perspective and system the ontology articulates. It is not a folder label.
Reasoner and worldview governance may use it to check coherence, ownership, and allowable
specialization.

### 3.3. The root ontology and core imports

One ontology may declare the worldview root:

```kwv
ontology imod
    "Foundational concepts for the worldview."
    in domain root
    version 1.0
;
```

The root may name external foundational OWL ontologies:

```kwv
ontology imod
    "Foundational concepts for the worldview."
    in domain root with core
        "https://example.org/odo.owl" as odo
    version 1.0
;
```

Each core import is a quoted URL followed by a lowercase alias. The grammar permits several,
separated by commas. Root-domain exclusivity, dependency restrictions, and completeness of core
bindings are semantic validation responsibilities; the parser alone does not establish them.

## 4. Concept declarations

Every top-level concept statement has this shape:

```kwv
<annotation>*
[abstract] [subjective] <concept-type> <ConceptName>
    ["Human-readable definition"]
    <clauses>
    [metadata <map>]
;
```

Concept names begin with an uppercase letter. Their full identifiers combine the ontology name and
local name, such as `hydrology:Runoff`. Top-level `abstract` and `subjective` are modifiers on the
concept type.

`abstract` declares a concept that organizes or constrains descendants but is not intended as a
directly instantiated concrete observable. `subjective` marks a distinction whose interpretation
depends on an observer or perspective. The parser records both; the active Reasoner and validators
determine their full operational effect.

Annotations precede the type:

```kwv
@deprecated
process LegacyFlow
    is hydrology:WaterFlow
;
```

Annotations and metadata are extensible conventions. Their recognized names and effects depend on
the active language and service implementation.

## 5. Concept types

Types are observational commitments, not cosmetic labels. They influence what an observation is,
how it can be contextualized, and which semantic operators apply.

### 5.1. Substantials and occurrents

| Declaration | Meaning |
| --- | --- |
| `thing` | A non-agentive substantial that can bear qualities |
| `configuration` | A recognizable arrangement or system of related observations |
| `agent` | An agentive substantial; may be `deliberative`, `interactive`, or `reactive` |
| `process` | An open-ended dynamic occurrence |
| `event` | A bounded occurrence with temporal identity |
| `relationship` | A directed relationship; normally `functional` or `structural` |
| `bond` | A bond-like connection; normally `functional` or `structural` |

```kwv
thing Watershed;

reactive agent ReservoirOperator;

process Infiltration;

event Flood;

functional relationship DrainsTo
    links earth:Region to earth:WaterBody
;
```

The grammar permits an unqualified `agent`, `relationship`, or `bond`. Semantic validators may
require a qualifier for concrete declarations where the distinction matters.

### 5.2. Qualities and properties

The generic declarations are `quality`, `class`, `quantity`, `ordering`, and `extent`. The grammar
also provides property keywords whose physical behavior is known:

| Extensive properties | Intensive properties |
| --- | --- |
| `amount`, `area`, `duration`, `length`, `mass`, `money`, `volume`, `weight` | `acceleration`, `angle`, `charge`, `electric-potential`, `energy`, `entropy`, `pressure`, `priority`, `resistance`, `resistivity`, `temperature`, `velocity`, `viscosity` |

This distinction matters in mediation. Extensive properties can generally be aggregated over
their support; intensive properties generally cannot be summed meaningfully.

```kwv
volume RainfallVolume
    is imod:Volume
    within earth:Region
;

temperature AtmosphericTemperature
    is imod:Temperature
    within earth:Location
;
```

### 5.3. Predicates and organizing concepts

| Declaration | Meaning |
| --- | --- |
| `attribute` | An accidental descriptive predicate; may be `deniable` or `rescaling` |
| `identity` | A classificatory identity; may be `individual` |
| `role` | A context-dependent role |
| `realm` | A realm or broad contextual predicate |
| `domain` | A worldview domain |

```kwv
deniable attribute Managed
    applies to earth:Region
;

individual identity NamedReservoir;

role WaterSupplier
    applies to infrastructure:Reservoir
;
```

`deniable attribute` records that negation can be represented meaningfully. The separate
`deniable as` clause assigns an explicit negated alias.

## 6. Concept references and observable expressions

Most clauses accept a `ConceptRef`, which is either:

- a local uppercase concept name such as `WaterFlow`; or
- a full compositional expression such as `imod:Volume of earth:WaterBody`.

Qualified names are preferable in documentation and examples because they remain clear outside
the source file. Local references must name concepts known at that point in the ontology.

The worldview grammar inherits `ConceptExpression` and `ContextualizedExpression` from the
observable language. This permits expressions such as:

```kwv
is imod:Configuration of hydrology:StreamConnection
in domain imod:Knowledge of imod:Hydrosphere
emerges from presence of earth:Water within earth:Region
```

See [Observables](OBSERVABLES.md) for unary operators, relationships such as `of`, `caused by` and
`during`, query selectors, value operators, and the distinction between
concepts and complete observable specifications. When an annotation, map, or
other value position needs a full observable rather than a direct concept
expression, enclose it in `{{ ... }}`.

## 7. Definition clauses

A definition may contain each clause family at most once. Because the grammar uses an unordered
group, clause order is flexible. Use a stable editorial order—parentage first, restrictions and
effects next, children last—to keep reviews intelligible.

### 7.1. `is`, `is core`, and `equals`

```kwv
is <concept-ref> [within <concept-ref>]
is core <concept-ref> [within <concept-ref>]
equals <concept-ref> [within <concept-ref>]
```

`is` declares specialization. `equals` declares an alias or semantic equivalence. `is core`
connects a worldview concept to a foundational concept imported by the root ontology.

```kwv
process Runoff
    is hydrology:WaterFlow
;

temperature AirTemperature
    is imod:Temperature
    within earth:Atmosphere
;

abstract process Process
    is core odo:Process
;
```

Use `equals` only for genuine equivalence. A related or narrower concept should use `is`.

### 7.2. `deniable as`

```kwv
attribute Intentional
    deniable as Unintentional
;
```

This gives a predicate an explicit negated form. The grammar identifies this as a trait-oriented
construct; validation must ensure that the type and alias are appropriate.

### 7.3. `inherits`

```kwv
identity Snow
    inherits physical:Solid, earth:Frozen
;
```

`inherits` attaches predicate-like concepts. It is not the taxonomy clause: use `is` for
parentage.

### 7.4. `applies to`

```kwv
role WaterSupplier
    applies to infrastructure:Reservoir, infrastructure:Utility
;
```

This restricts the concepts that may bear a predicate or participate in the declared meaning. It
is especially important for attributes, roles, realms, and configurations.

### 7.5. `links ... to ...`

```kwv
functional relationship DrainsTo
    links earth:Region to earth:WaterBody
;
```

This establishes relationship source and target. The current grammar accepts one source reference
and one target reference in a single `links` clause.

### 7.6. `creates` and `affects`

```kwv
process Precipitation
    creates hydrology:WaterVolume
;

process Heating
    affects earth:AtmosphericTemperature
;
```

`creates` declares produced observables. `affects` declares observables whose state may be
modified. Several targets may be comma-separated. These clauses express semantic potential, not
executable equations; k.IM models provide the computation.

### 7.7. `emerges from` and `implies`

Both clauses accept contextualized expressions:

```kwv
configuration StreamNetwork
    emerges from hydrology:StreamConnection within earth:Region
;

realm Floodplain
    implies earth:Terrestrial within hydrology:Watershed
;
```

`emerges from` identifies conditions from which an emergent concept may be recognized. `implies`
records an entailment associated with the declaration. Multiple expressions may be comma-separated.

### 7.8. Description clauses

Only one description clause may occur in a definition. The grammar supports:

```kwv
describes <concept-ref>
describes <concept-ref> as <number> [to <number>]
describes <concept-ref> as <concept-ref>
describes <concept-ref> as true
describes <concept-ref> as false
increases with <concept-ref>
decreases with <concept-ref>
marks <concept-ref>
classifies <concept-ref>
discretizes <concept-ref>
```

| Clause | Intended relationship |
| --- | --- |
| `describes` | Generic description of another observable, optionally with a value constraint |
| `increases with` | Direct qualitative proportionality |
| `decreases with` | Inverse qualitative proportionality |
| `marks` | Deniable marker associated with a nonzero or satisfied quality |
| `classifies` | Classification of a quality |
| `discretizes` | Ordering or discretization of a quantitative quality |

```kwv
ordering FloodSeverity
    discretizes hydrology:FloodDepth
;
```

Type compatibility and the exact inferences derived from these clauses belong to semantic
validation and Reasoner behavior.

### 7.9. `requires`

The predicate requirement forms are:

```kwv
requires identity <concept-ref> [, ...]
requires realm <concept-ref> [, ...]
requires extent <concept-ref> [, ...]
requires attribute <concept-ref> [, ...]
```

An authority requirement uses an uppercase authority identifier and optional parameters:

```kwv
identity ChemicalSpecies
    requires authority IUPAC {language: "en"}
;
```

Authorities let a worldview validate and use large external identity spaces without copying every
identifier into the Reasoner.

### 7.10. Child taxonomies

The compact form is:

```kwv
abstract identity PrecipitationType
    has disjoint children Rain, Snow, Hail
;
```

A simple child may include a `within` specialization and description. Use a parenthesized full
definition when a child needs its own annotations or clauses:

```kwv
abstract realm AquaticEnvironment
    has disjoint children
        (Marine
            "Saltwater marine environments."
        ),
        (abstract Freshwater
            "Freshwater environments."
            has children Riverine, Lacustrine
        )
;
```

Nested definitions inherit the parent's concept type. They may use `abstract` or
`sealed abstract`. `sealed abstract` is intended for partitions in which only children are usable
and the children cover the parent's semantic space. Coverage and direct-instantiation rules
require semantic validation.

## 8. Metadata, annotations, and documentation

Annotations precede a concept statement or nested concept. Metadata follows the definition
clauses:

```kwv
@deprecated
thing LegacyWatershed
    metadata {
        dc.creator: "Hydrology community"
        review_status: "deprecated"
    }
;
```

The parser preserves extension-defined annotations and metadata. Do not assume that an annotation
has an effect unless the active Resources and Reasoner services recognize it.

An annotation value may carry a complete observable as a semantic literal:

```kwv
@example(query = {{presence of hydrology:River}})
thing RiverMonitor
;
```

Descriptions should define the concept, state important boundaries, and avoid circular wording.
For community-governed worldviews, accompany difficult concepts with examples, counterexamples,
decision records, and semantic tests in the surrounding project documentation.

## 9. Authorities and external ontologies

Core OWL imports and authorities solve different problems:

- a **core ontology import** anchors foundational worldview concepts to an external OWL ontology;
- an **authority** validates identifiers from a potentially large external vocabulary when used.

Authority concepts appear in ordinary observable syntax with an uppercase namespace:

```text
IUPAC:H2O
GBIF:2877951
```

An authority adapter validates the identifier and aligns it with observational semantics. This
avoids loading millions of species, chemicals, administrative units, or other identities into
every Reasoner.

## 10. How `.kwv`, `.kim`, and `.kactor` work together

Consider a simplified flood application:

1. A `.kwv` ontology defines `hydrology:Flood`, `hydrology:FloodDepth`, applicable subjects, and
   relationships.
2. An [observable expression](OBSERVABLES.md) such as
   `hydrology:FloodDepth of earth:Region` states a query independently of any
   implementation.
3. A [k.IM model](KIM.md) states how that observable can be produced from data and model
   dependencies in a context.
4. Reasoner interprets the observable; Resolver selects and composes k.IM strategies; Runtime
   creates the observation in a digital twin.
5. A [k.Actors behavior](AGENTS.md) bound to a flood-management agent reacts when an observation
   crosses a threshold, sends a message, or requests another observation.

```text
worldview meaning (.kwv)
        |
        v
observable query
        |
        v
observation strategies (.kim)
        |
        v
digital-twin observations
        |
        v
reactive behavior (.kactor)
```

No language replaces the others. The ontology language defines shared vocabulary and logic; k.IM
connects that logic to ways of observing; k.Actors gives selected runtime agents behavior.

## 11. Authoring and review guidance

A worldview contribution should:

- declare one clear domain and a meaningful version;
- import only ontologies it semantically depends on;
- choose the observational type before choosing a parent;
- use `is` for specialization, `equals` only for equivalence, and `inherits` for predicates;
- state applicability, relationship endpoints, and required dimensions explicitly;
- use disjoint or sealed partitions only when completeness and exclusivity are defensible;
- provide definitions with boundaries, examples, and counterexamples;
- preserve external identifiers through authorities instead of recreating large vocabularies;
- include migration guidance when deprecating or replacing stable concepts;
- test operational consequences in representative k.IM resolution workflows.

Review must cover both logical coherence and downstream effects. A syntactically small ontology
change can alter model matching, mediation, classification, or the identity of observations
already stored in digital twins.

## 12. Validation checklist

Before publishing a `.kwv` source, check at least:

- exactly one ontology preamble is present;
- `in domain` and `version` are present;
- ontology and import names use valid lowercase namespace syntax;
- concept names begin with an uppercase letter;
- every statement ends with a semicolon;
- imported and referenced ontologies are available;
- each concept has the correct observational type;
- local and qualified concept references resolve;
- each clause family occurs no more than once per concept;
- `links` appears only where relationship semantics make sense;
- `creates`, `affects`, `applies to`, and `requires` use compatible targets;
- disjoint children can actually be mutually exclusive;
- sealed partitions are complete;
- aliases are genuinely equivalent;
- core bindings and authority requirements can be resolved by active services.

Parser acceptance is only the first gate. Semantic consistency is established when the ontology is
adapted, loaded into the Reasoner, and checked with the rest of its worldview.

## 13. Running and evolution

The Resources service recognizes `.kwv` as the `WORLDVIEW` language and adapts a parsed ontology
to `KimOntology`. A worldview-providing Resources service distributes those assets to a Reasoner,
which loads them into its OWL-backed semantic model. The active worldview then governs observable
interpretation and strategy matching for scoped workflows.

The parser grammar is ahead of parts of the Java adaptation and validation layer. Notable examples
in the current implementation include incomplete adaptation of local `ConceptRef` values,
description clauses, and requirement clauses. Several semantic constraints described in grammar
comments—such as root exclusivity and sealed-partition completeness—also need stronger validators.
Therefore:

1. use `Worldview.xtext` for accepted source syntax;
2. use `KimOntology`, `KimConceptStatement`, and the syntax adapters for the portable parsed
   contract;
3. use `KimOntologyVisitor` and Reasoner loading for implemented semantic traversal;
4. prove important constructs with real `.kwv` parser/adaptation tests before relying on them;
5. treat older `namespace ...` worldview headers as pre-current syntax—the current grammar uses
   `ontology ...`.

When adding or completing a construct, update the grammar, syntax adapter, public API model,
visitor/validator, Reasoner translation, and real-file tests together. A clause is not operational
merely because the parser accepts it.
