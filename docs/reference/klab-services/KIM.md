# k.IM modeling language guide

k.IM is k.LAB's declarative language for connecting semantic observables to the
resources and computations that can produce them. A `.kim` namespace does not
prescribe an imperative workflow. It publishes observation strategies that the
resolver can discover, rank, combine, and contextualize when an observation is
requested.

This guide follows the active
`org.integratedmodelling.languages.kim.Kim` grammar and the public language
contracts in `klab-api`, principally `KimNamespace`, `KimModel`,
`KimObservable`, and `Contextualizable`. Where the grammar and the current Java
adapter differ, the final section calls that out explicitly.

k.IM is one of three complementary user-facing languages:

| Layer | Language | Primary role |
|---|---|---|
| Semantic commons | [Worldview ontology language](ONTOLOGY_LANGUAGE.md) (`.kwv`) | Define and relate the concepts through which a community describes its domain |
| Semantic modeling | **k.IM** (`.kim`) | Associate observables with reusable strategies, data, and computations |
| Digital twin and interaction | [k.Actors](AGENTS.md) (`.kactor`) | Give observations, digital twins, users, and sessions reactive behavior |

The [observable expression guide](OBSERVABLES.md) documents the semantic query
and asset-description syntax used directly by `.kwv` and `.kim` and embedded as
`{{ ... }}` literals in all three languages.

## 1. What k.IM contributes

A worldview states what can be observed. A k.IM namespace states how some of
those observables may be produced in particular contexts. At resolution time,
k.LAB can:

1. interpret a requested observable against the active worldview;
2. discover compatible models and resources;
3. evaluate their coverage, dependencies, provenance, and permissions;
4. assemble a contextualization dataflow; and
5. submit the resulting observations to a digital twin, where k.Actors
   behaviors may react to them.

This separation is central to the semantic commons. A model author publishes
the meaning, applicability, and dependencies of a strategy without deciding in
advance which application, institution, or runtime will use it.

## 2. A minimal namespace

```kim
namespace examples.hydrology
  "Small illustrative hydrology namespace."
  using imod, earth, hydrology
  version 1.0
;

model public.data:hydrology:climate:rainfall
  as hydrology:RainfallVolume in mm
;

model hydrology:RunoffVolume in m*m*m
  observing
    hydrology:RainfallVolume in mm named rainfall,
    geography:Slope in degree_angle named slope
  set to [runoff(rainfall, slope)]
;
```

The first model exposes a network resource as an observation strategy. The
second declares two semantic dependencies and an expression that produces the
requested output. The expression is evaluated by a runtime component; its
function names are not built into the k.IM grammar.

## 3. Namespace preamble

Every file begins with one namespace declaration:

```ebnf
[visibility] [void] (namespace | scenario | worldview) name [documentation]
  [using imports]
  [over functions]
  [disjoint with namespace-paths]
  [version version]
  [observed as concept]
  [metadata]
;
```

### 3.1 Namespace identity and kind

```kim
namespace ecology.vegetation version 1.2;
scenario policy.rewilding using ecology.vegetation;
worldview local.extensions using earth;
```

- `namespace` publishes ordinary models and definitions.
- `scenario` groups alternative or overriding strategies that only participate
  when the scenario is active.
- `worldview` marks a k.IM namespace as bound to a worldview. It does **not**
  define ontology concepts; those belong in a `.kwv` ontology.

Namespace names are lower-case dotted paths. A documentation string may follow
the name. `version` is currently optional in the k.IM grammar, although a
stable version is strongly recommended for published namespaces.

### 3.2 Visibility and inactivity

The namespace can be `private` or `project private`. A leading `void` marks it
inactive without deleting its contents:

```kim
project private namespace project.calibration version 0.4;
void namespace experiments.retired version 0.1;
```

Use project visibility for implementation details that should be shared inside
one project but not exposed as part of its public modeling interface.

### 3.3 Imports

Imports may expose an entire namespace, all of its exported symbols, or a
selected list:

```kim
namespace examples.imports
  using earth,
        * from ecology.vegetation,
        (forest_cover, habitat_class) from project.shared
  version 1.0
;
```

Concept prefixes in observables must be resolvable through the active worldview
and imports. Imported model and definition names are subject to namespace
visibility.

### 3.4 Coverage and compatibility

The preamble can declare additional functions with `over`, namespace
incompatibilities with `disjoint with`, and a semantic subject with
`observed as`:

```kim
namespace regional.forestry
  using earth, forestry
  over space(shape = "administrative"), time(year = 2025)
  disjoint with experimental.forestry
  observed as earth:Region
  version 2.0
;
```

The exact functions available to `over` are supplied by installed components,
not enumerated by the grammar.

### 3.5 Metadata and annotations

Namespace annotations precede the preamble; metadata belongs to the preamble:

```kim
@documentation(category = "examples")
namespace examples.metadata
  version 1.0
  metadata {creator: "Modeling team", license: "CC-BY-4.0"}
;
```

Annotation names and parameters are extensible. Consumers should preserve
unknown annotations and metadata rather than silently discarding them.

## 4. Model declarations

The general semantic model form is:

```ebnf
[void] model [visibility]
  [source as]
  output-observable [, output-observable ...]
  [observing dependency-observable [, dependency-observable ...]]
  [action ...]
;
```

### 4.1 Outputs

A model has one or more output observables:

```kim
model earth:Elevation in m;

model hydrology:RainfallVolume in mm,
      hydrology:SnowfallVolume in mm;
```

An output may be annotated and can use the full observable syntax: semantic
operators, units, currencies, ranges, values, predicates, and other clauses
defined by the observable grammar. Prefer the smallest declaration that
captures the intended semantics.

### 4.2 Model visibility and `void`

Models can be `private`, `project private`, or `public`. A `void model` remains
parseable and documentable but does not provide an active resolution strategy:

```kim
private model calibration:Coefficient;
void model earth:DeprecatedIndicator;
```

Visibility affects discoverability; it does not change the semantics of the
model's observable.

### 4.3 Dependencies

Dependencies follow `observing`:

```kim
model vegetation:NetPrimaryProductivity in kg/(m*m)/year
  observing
    climate:AirTemperature in degC named temperature,
    climate:Precipitation in mm named precipitation,
    optional geography:Slope in degree_angle named slope
  set to [npp(temperature, precipitation, slope)]
;
```

Names make dependencies available to expressions and contextualizers.
`required` and `optional` express availability requirements. Dependencies are
semantic requests, so the resolver may satisfy them with any compatible
strategy available in the current context.

For the exact observable clauses, see [OBSERVABLES.md](OBSERVABLES.md).

## 5. Sources and contextualizables

A source before `as` supplies the primary contextualizable for the model.
Current grammar forms include:

- network resource URNs, optionally with a parameter map;
- local resource paths;
- expressions in brackets;
- numeric and Boolean literals;
- concept references or concept expressions in braces; and
- string literals.

Examples:

```kim
model public.data:climate:stations:temperature
  as climate:AirTemperature in degC
;

model public.data:landcover:global:esa {year: 2020}
  as ecology:LandCoverClass
;

model "data/local/reference.csv"
  as geography:ReferenceValue
;

model [normalize(raw)]
  as statistics:NormalizedValue
  observing statistics:RawValue named raw
;

model 0
  as hydrology:RunoffVolume in m*m*m
;

model {presence of earth:Water}
  as ecology:AquaticCondition
;
```

Whether a source can actually be used depends on a resource or runtime service
capable of resolving its adapter, service call, or expression language.
Parsing establishes structure; it does not prove runtime availability.

## 6. Contextualization actions

Actions refine how a model produces its outputs. They are adjacent clauses in
the model declaration; the current grammar does not use an `==` action
delimiter.

### 6.1 Set and expression actions

```kim
model hydrology:RunoffCoefficient
  observing ecology:LandCoverClass named cover
  set to [coefficient(cover)]
;

model hydrology:WaterBalance
  observing
    hydrology:PrecipitationVolume named precipitation,
    hydrology:EvapotranspirationVolume named evapotranspiration
  do [precipitation - evapotranspiration]
;
```

`set` may name one or more targets. The `do` keyword is optional for the bare
expression form, but writing it makes intent clearer.

Only `set` actions currently accept an event trigger:

```kim
model ecology:DisturbanceState
  on event ecology:FireEvent
  set to [afterFire()]
;
```

The other trigger forms are `on initialization`, `on termination`, and
`on transition`. Triggered model actions are contextualization hooks, not a
substitute for sustained reactive behavior; use
[k.Actors](AGENTS.md) for observation and digital-twin lifecycles.

### 6.2 Integrate

```kim
model hydrology:AccumulatedRunoffVolume
  observing hydrology:RunoffRate named runoff
  integrate value as [runoff]
;
```

An `integrate` action associates a target with an expression to be accumulated
over the contextual scale.

### 6.3 Service calls with `using` and `over`

```kim
model geography:TravelTime
  observing
    geography:Origin named origin,
    geography:Destination named destination
  using routing(mode = "walking")
;

model climate:RegionalMeanTemperature
  observing climate:AirTemperature named temperature
  over aggregate(method = "mean")
;
```

Function calls are resolved through registered language and component
services. Their parameters, return types, and side effects are service
contracts rather than grammar-defined behavior.

### 6.4 Classification and discretization

Inline classifications map classifiers to semantic concepts:

```kim
model ecology:VegetationCondition
  observing ecology:VegetationIndex named index
  classified into
    ecology:LowVegetation if < 0.2,
    ecology:MediumVegetation if >= 0.2,
    ecology:HighVegetation if >= 0.6
;
```

The grammar supports Boolean, numeric, range, string, concept, set-membership,
relational, wildcard, and unknown classifiers. A classification can also be
referenced by name with `according to`. `discretized into` uses the same
classification structure for continuous-to-class conversion.

### 6.5 Lookup and match tables

One-way lookup actions use an inline table or a named table:

```kim
model ecology:HabitatSuitability
  observing ecology:LandCoverClass named cover
  lookup(cover) into
  ===
  ecology:Forest | 1,
  ecology:Grassland | 0.6,
  * | 0
  ===
;
```

Two-way matching uses `match` and a two-way table. The exact table header,
classifier, and result syntax is defined by the grammar; named tables can be
declared once with `define` and reused.

## 7. Resource URNs

Network resources use a structured URN, conventionally:

```text
urn:klab:<node>:<catalog>:<namespace>:<resource>[@<version>][#<fragment>]
```

The grammar also accepts the compact four-section form without the
`urn:klab:` prefix. Published documentation should normally use the full form
to make network identity explicit.

```kim
model urn:klab:institution:climate:observations:temperature@2.1
  as climate:AirTemperature in degC
;
```

URN identity is not a promise that every service can access the resource.
Catalog discovery, authorization, adapter compatibility, and runtime capacity
remain part of resolution.

## 8. Learned and nonsemantic models

### 8.1 Learned resources

A `learn` declaration describes a learned strategy and names the resource that
will hold or identify its learned state:

```kim
learn ecology:HabitatSuitability
  observing
    ecology:SpeciesPresence named presence,
    ecology:LandCoverClass named cover
  as project.models.habitat_learned
;
```

In the current grammar the `as` learned-resource target is mandatory. Training
and update mechanics depend on the runtime service supporting that resource.

### 8.2 Nonsemantic outputs

k.IM can also type products that are intentionally nonsemantic:

```kim
model number sampleCount;
model text reportTitle;
model boolean as convergenceFlag;
model subjects generatedSites;
model events detectedChanges;
model relationships inferredLinks;
```

Use these forms for implementation products that should not masquerade as
worldview concepts. Semantic outputs remain preferable whenever the product is
intended for discovery and reuse.

## 9. Definitions and reusable tables

`define` introduces a named value, classifier table, or two-way table:

```kim
define defaultThreshold as 0.5;

define HABITAT_SCORES as
===
ecology:Forest | 1,
ecology:Grassland | 0.6,
* | 0
===
;
```

Definition names and permitted bodies depend on their definition class in the
active grammar. Definitions are namespace symbols, so imports and visibility
govern their reuse.

## 10. Scenarios and worldview-bound namespaces

A scenario is a selectable layer of strategies:

```kim
scenario policy.low_emissions
  using climate.baseline
  version 1.0
;

model climate:EmissionRate
  observing economy:ActivityLevel named activity
  set to [lowEmissionRate(activity)]
;
```

The model participates when the scenario is active. Scenarios should express a
coherent assumption set, not duplicate an entire base namespace.

A `worldview` k.IM namespace packages modeling content that is coupled to a
particular worldview. Concept declarations still belong in the corresponding
[`.kwv` ontology](ONTOLOGY_LANGUAGE.md). Keeping this boundary explicit lets a
community evolve shared meanings separately from implementations that observe
them.

## 11. Binding behavior with k.Actors

Annotations are the extension point through which models and observations can
be connected to UI, provenance, documentation, and behavior conventions. In
deployments that support it, a binding annotation can associate observations
with a k.Actors behavior:

```kim
@bind(behavior = "project.behaviors.monitor")
model hydrology:RiverCondition
  observing hydrology:DischargeRate named discharge
  set to [condition(discharge)]
;
```

`@bind` is a platform convention interpreted by adapters and services, not a
hard-coded k.IM model clause. The behavior itself is written and validated as
a `.kactor` resource; see the [k.Actors guide](AGENTS.md).

This preserves a useful contract:

- `.kwv` says what `hydrology:RiverCondition` means;
- `.kim` says how an observation of it can be produced; and
- `.kactor` says how an actor reacts when that observation or its digital twin
  changes.

## 12. Resolution, services, and provenance

A k.IM model is a published candidate, not a command sent directly to one
machine. In a service network:

1. resource services expose namespaces, models, metadata, and resource
   descriptors;
2. reasoners compare requested and provided semantics under the active
   worldview;
3. resolvers select and compose applicable strategies for the context;
4. runtime services execute the resulting contextualizables and preserve
   provenance; and
5. digital-twin services receive observations and route lifecycle events to
   k.Actors behaviors.

Different institutions may host the ontology, models, referenced datasets,
adapters, and execution capacity. Stable semantic identity and explicit
dependencies allow discovery to improve without changing the model's meaning.

## 13. Authoring guidance

### 13.1 Start from the observable

Define or reuse the worldview concept first, then state the most precise output
observable the strategy actually provides. Avoid choosing a vague output merely
to make a resource appear broadly applicable.

### 13.2 Declare semantic dependencies

Use `observing` for information the resolver may satisfy independently. Use a
resource parameter only when it configures that specific resource. This
distinction is what allows alternate data and model providers to interoperate.

### 13.3 Keep expressions portable

Expressions and function calls depend on installed runtime components. Publish
the language, service, or adapter requirement in project metadata and avoid
assuming that a local function is universally available.

### 13.4 Preserve provenance

Prefer stable, versioned resource URNs for shared data. Provide creator,
license, temporal validity, and methodological metadata where appropriate.
Resolution can only communicate fitness and provenance that authors expose.

### 13.5 Put reactivity in k.Actors

Use k.IM actions to contextualize an observation. Use k.Actors for conversations,
stateful interaction, event handling, user sessions, and long-lived digital
twin behavior.

## 14. Review checklist

Before publishing a `.kim` namespace, check that:

- the namespace kind, identity, visibility, and version are intentional;
- imports are minimal and all concept prefixes resolve;
- output observables match the actual semantics, units, and scale of the
  produced data;
- dependencies are named and correctly marked required or optional;
- resource URNs are stable and parameter maps are reproducible;
- expressions and service calls name runtime capabilities available to the
  intended deployment;
- scenario and worldview-bound content is not confused with ontology
  definition;
- model visibility matches the intended discovery scope;
- provenance, license, and authorship metadata are present for shared models;
- any k.Actors binding names an available behavior; and
- the namespace parses and is exercised through the services that will
  resolve and run it.

## 15. Current implementation status

The grammar is the authoritative statement of accepted source syntax, while the
Java syntax objects are the contract consumed by services. They are not yet
perfectly aligned:

- `ModelSyntaxImpl` adapts model outputs, dependencies, sources, expressions,
  `set`, `integrate`, `using`, and `over` actions;
- adaptation of inline classification, classification references, lookup
  tables, and named lookup tables is still marked incomplete in the current
  implementation;
- semantic validation is evolving and does not prove that referenced resources,
  adapters, functions, or runtime services are available; and
- the repository currently lacks broad real-file regression coverage for
  `.kim` namespaces comparable to the k.Actors behavior tests.

For language evolution, keep four artifacts synchronized: the Xtext grammar,
the `KimNamespace`/`KimModel`/`Contextualizable` API contracts, the syntax
adapters and validators, and this guide. Add parser-to-API fixtures for each
new clause before presenting it as generally supported.
