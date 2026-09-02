# Observable expression language guide

An **observable expression** is k.LAB's query language for meaning. It states
what should be observed independently of any dataset, model, service, or
digital twin. The same expression is the semantic key used to annotate and
catalogue assets, declare model outputs and dependencies, select observations,
and route semantic values through behaviors.

This guide follows the active
`org.integratedmodelling.languages.Observable` Xtext grammar. Its parsed
service contracts are `KimObservable` and `KimConcept` in `klab-api`. The
grammar is shared by all three user-facing languages:

| Host language | Use of observable syntax |
|---|---|
| [Worldview ontology language](ONTOLOGY_LANGUAGE.md) (`.kwv`) | Directly in concept definitions and relationships; as `{{ ... }}` literals where a value is expected |
| [k.IM](KIM.md) (`.kim`) | Directly for model outputs and dependencies; as `{{ ... }}` literals in parameters and other value positions |
| [k.Actors](AGENTS.md) (`.kactor`) | Only as `{{ ... }}` semantic literals in values and semantic match patterns |

Observable syntax is not a fourth workflow language. It is the common semantic
sublanguage through which the other three refer to the same meaning.

## 1. Observable, observation, and model

- An **observable** is a logical specification of something that could be
  observed.
- An **observation** is its contextualized realization in a digital twin.
- A **model** is one possible strategy for producing an observation.

```observable
probability of hydrology:FloodEvent during calendar:Year;
```

This expression does not identify a raster or endpoint. It asks for a meaning.
In a context scope, the Reasoner interprets it, the Resolver finds compatible
strategies, Resources supplies applicable assets, and Runtime produces or
retrieves an observation. Different contexts may lead to different dataflows
without changing the query.

Observable expressions are consequently the primary semantic catalogue key. A
resource still has a physical URN, but its k.IM models state which observables
it can contribute to. Discovery by meaning can then find resources the
requester did not know by name.

## 2. Concepts and predicates

A worldview concept is written as `namespace.path:ConceptName`:

```observable
earth:Region;
hydrology.physical:WaterFlow;
```

The namespace is a lower-case dotted path and the concept name begins with an
upper-case letter. A concept may be a complete query or be composed with other
concepts and semantic operators. Every expression has one main observable;
other concepts constrain or qualify it.

k.LAB describes observable concepts by dependence and perspective:

| Dependence | Structural perspective | Functional perspective |
|---|---|---|
| Independent | subject or other substantial entity | event |
| Dependent | quality | process |
| Relational | structural relationship or bond | functional relationship |

Configurations describe recognized, observer-dependent patterns emerging from
other observations. Worldviews also define agents, extents, identities, realms,
roles, attributes, domains, quantities, and classes. See the
[worldview guide](ONTOLOGY_LANGUAGE.md) and [ODO-IM](ODO_IM.md).

Predicates refine an observable but do not normally stand alone as an
observation request:

```observable
biology:Eucalyptus biology:Tree;
(ecology:AboveGround ecology:Biomass) of biology:Tree;
```

The active worldview determines whether such sequences are logically
admissible. Parsing alone cannot establish that.

## 3. Observable statements

The base grammar can parse a stand-alone sequence of semicolon-terminated
statements. Observable expressions are not normally published as a separate
k.LAB asset type; deployed declarations are embedded in `.kwv`, `.kim`, or
`.kactor` host documents.

```ebnf
concept-expression
  [observed as concept-expression]
  [in unit | in currency | range-min to range-max]
  [named local-name]
  [optional | required]
  [inline-metadata ...]
;
```

These clauses are unordered in the grammar. The order above is recommended:

```observable
climate:AirTemperature
  observed as earth:AtmosphericCondition
  in degC
  named air_temperature
  required
  :source-kind "station"
;
```

### 3.1 Units, currencies, and ranges

```observable
geography:Elevation in m;
climate:PrecipitationVolume in mm;
economy:Revenue in EUR@2025;
economy:PropertyValue in EUR@2025/m/m;
ecology:HabitatSuitability 0 to 1;
```

A currency requires a reference year. Units may contain multiplication,
division, `^` connectors, and parenthesized parts, such as `kg/(m*m*m)` and
`(J/s)/(m*m)`. In the current grammar, the operand after `^` is a unit element,
not a numeric exponent, so use explicit products rather than forms such as
`m^2`. A numeric range is an alternative to a unit or currency.

Mediators constrain representation; they do not replace meaning. Compatible
unit conversion must remain visible in dataflow provenance.

### 3.2 Observation semantics

`observed as` states an observation lens:

```observable
ecology:LandCoverClass
  observed as remote_sensing:SatelliteObservation;
```

This is distinct from inherency expressed with `of` and from a runtime user or
actor. Its validity depends on the worldview.

### 3.3 Names and optionality

`named` gives a host construct a lower-case local identifier. `optional` and
`required` are most useful on k.IM dependencies:

```kim
model hydrology:WaterBalance
  observing
    climate:PrecipitationVolume in mm named precipitation required,
    hydrology:EvapotranspirationVolume in mm named evapotranspiration optional
  set to [precipitation - evapotranspiration]
;
```

These clauses express host-level resolution needs; they do not change the
concept.

### 3.4 Inline metadata

```observable
climate:AirTemperature :preferred true :source-kind "station";
hydrology:DischargeRate !deprecated;
```

Keys beginning with `:` may carry a value. Keys beginning with `!` are negative
flags. Metadata is extensible; do not use it to hide distinctions that belong
in the semantics.

## 4. Concept-expression base forms

### 4.1 Plain sequences and grouping

```observable
geography:Elevation;
biology:Eucalyptus biology:Tree;
(ecology:AboveGround ecology:Biomass) of biology:Tree;
```

Parentheses group an expression so a later modifier applies to the whole. Use
them whenever scope would otherwise be unclear.

### 4.2 Distribution

```observable
each biology:Tree;
count of biology:Tree;
```

`each` requests individual or distributed observations. The second expression
requests one derived count. Validity depends on concept type and context.

### 4.3 Unary operators

| Syntax | Typical intent |
|---|---|
| `presence of X` | whether or where X is present |
| `magnitude of X` | magnitude associated with X |
| `distance to X` or `distance from X` | distance relative to X |
| `probability of X` | probability of X |
| `change in X` | change in X |
| `change rate of X` | rate of change |
| `uncertainty of X` | uncertainty associated with X |
| `level of X` | level representation |
| `type of X` | classification of X |
| `occurrence of X` | occurrence of an event or process |
| `count of X` | count of instances |

```observable
presence of biology:Tree;
distance to infrastructure:Road;
probability of hydrology:FloodEvent;
change rate of climate:AirTemperature;
uncertainty of ecology:HabitatSuitability;
```

Operators are semantic, not merely syntactic functions. Their valid operands
and inference behavior come from the worldview and Reasoner.

### 4.4 Explicit change

```observable
changed ecology:LandCoverClass;
changed ecology:LandCoverClass
  from ecology:Forest
  to ecology:UrbanArea;
```

This differs from `change in X`: `changed` describes a transition and may
constrain its endpoints.

### 4.5 Proportion, percentage, and ratio

```observable
proportion ecology:Forest in earth:Region;
percentage ecology:Wetland in earth:Watershed;
ratio of ecology:Input to ecology:Output;
```

The `in` operand of proportion or percentage states the whole. Do not insert
`of` after those keywords; it is not in the current grammar. A ratio requires
both operands.

### 4.6 Value

```observable
value of ecology:Pollination;
monetary value of ecology:Pollination;
monetary value of ecology:Pollination over agriculture:Crop;
```

`over` here states the comparison or beneficiary operand. It differs from the
numeric `over number` value operator.

## 5. Semantic modifiers

Expressions may chain binary modifiers:

| Operator | Relationship expressed |
|---|---|
| `of [each] X` | inherency or attribution |
| `and X` / `or X` | intersection or union |
| `causing [each] X` / `caused by [each] X` | causal direction |
| `for [each] X` | goal or beneficiary |
| `adjacent to [each] X` | adjacency |
| `contained in [each] X` / `containing [each] X` | containment |
| `with [each] X` | compresence |
| `during [each] X` | temporal co-occurrence |

```observable
ecology:Biomass of each biology:Tree;
hydrology:WaterFlow caused by climate:Precipitation;
ecology:HabitatSuitability for biology:Species;
infrastructure:Road adjacent to hydrology:River;
biology:Tree contained in earth:Forest;
hydrology:FloodEvent during time:AnnualPeriod;
```

The grammar also admits another concept expression as a modifier, enabling
predicate sequences and higher-order composition. Prefer explicit parentheses
in complex expressions.

### 5.1 Relationship endpoints

```observable
infrastructure:TransportLink
  linking geography:Origin
  to geography:Destination;
```

The head must have relationship semantics in the active worldview.

## 6. Value operators

Value operators constrain or transform values. They are part of the concept
expression and precede statement clauses such as `in unit` and `named`.

### 6.1 Comparisons

```observable
geography:Elevation > 500.m;
climate:AirTemperature >= 0.degC;
ecology:HabitatSuitability <= 0.8;
hydrology:DischargeRate == 12.m*m*m/s;
```

Supported comparisons are `>`, `>=`, `<=`, `<`, and `==`. The operand is a
number or quantity; quantities join a number to a unit or currency with `.` or
`/`.

### 6.2 Semantic and contextual filters

```observable
ecology:LandCoverClass is any ecology:Forest;
presence of biology:Tree when climate:PrecipitationVolume > 0.mm;
biology:Tree whose ecology:Biomass > 100.kg;
biology:Tree without ecology:Disease;
```

The grammar provides `is`, `where`, `when`, `whose`, `without`, `by`, and
`down to`. Their condition operand is itself a concept expression. A grammar
comment calls for conditions to contain a value operator, but the current
parser rule does not enforce that restriction.

### 6.3 Aggregation and existence

```observable
hydrology:WaterVolume total;
presence of biology:Tree exists;
climate:AirTemperature averaged;
hydrology:RunoffVolume summed;
```

Applicability depends on observable type and scale. Parseability is not proof
of semantic validity.

### 6.4 Arithmetic transforms

```observable
statistics:Index plus 1;
statistics:Score minus 10;
statistics:Score times 100;
economy:Amount over 1000;
```

Use these only when rescaling is part of the requested observable. Model
implementation math normally belongs in k.IM contextualization.

The grammar also admits a bare `!=` with no operand and specialized `by` and
`down to` forms. Treat these as provisional until validator and runtime
contracts define their intended use.

## 7. References, authorities, and selectors

A reference is a worldview concept, an authority identity, or a pattern
variable:

```observable
hydrology:River;
IUPAC:water;
GBIF:2435099;
presence of $target;
```

Authority prefixes are upper case and require an available authority component.
Parsing does not prove that the authority can resolve the identifier.

`not` may prefix a deniable attribute:

```observable
not ecology:Managed ecology:Forest;
```

The worldview must declare that attribute deniable.

The selectors `any`, `all`, and `no` alter matching:

- `any X` selects X or its children;
- `all X` enables generalized, primarily model-side matching; and
- `no X` selects compatible siblings without X or its descendants.

They are query selectors, not new concepts. Pattern variables require
substitution before an expression becomes concrete; `KimObservable` exposes
the pattern and variable collection.

## 8. Semantic literals in host languages

Where a host grammar expects a value, wrap observable semantics in double
braces:

```text
{{ <observable-semantics> }}
```

No semicolon appears inside the braces.

### 8.1 k.IM

k.IM uses observables directly for model outputs and dependencies, but braces
in literal and parameter positions:

```kim
@documentation(subject = {{probability of hydrology:FloodEvent}})
model probability of hydrology:FloodEvent;

define elevation_query as {{geography:Elevation in m}};
```

### 8.2 Worldview ontologies

Worldview clauses use expressions directly:

```kwv
process Flooding
  affects geography:Region
  emerges from probability of hydrology:FloodEvent
;
```

Annotations, maps, and other value positions can carry `{{ ... }}`.

### 8.3 k.Actors

k.Actors accepts observables only as semantic literals:

```kactors
action main:
    def query {{probability of hydrology:FloodEvent}}
    runtime.observe(query)
```

They can also be semantic match patterns:

```kactors
runtime.observe({{each biology:Tree}}):
    {{biology:Tree}} as tree -> console.info(tree)
```

The runtime decides whether the literal acts as a query, classifier, message
value, or observation request.

## 9. Annotations and shared literals

Derived host grammars can accept one or more annotations before an observable.
For example, k.IM model outputs are `AnnotatedObservable` values:

```kim
model @predictor(weight = 0.7)
  distance to infrastructure:Road;
```

A stand-alone `ObservableSequence` does not accept annotations before its
statements.

The shared grammar also defines numbers, ranges, quantities, strings, Booleans,
lists, maps, concepts, functions, parameters, and URNs for derived languages.
The host grammar still decides which value rule is accepted in each position:

- `Value` admits naked concept references;
- `Literal` admits `{{ observable }}` but not naked concept expressions; and
- `Variable` adds identifiers and constants.

## 10. Contextualized expressions

The shared grammar defines this host-only construct:

```ebnf
concept-expression [within concept-expression]
```

```kwv
quality UpstreamArea
  is geography:Area within hydrology:Watershed
;
```

`within` is not part of a stand-alone observable statement. It is accepted only
where the host asks for a `ContextualizedExpression`.

## 11. Common query patterns

```observable
// Direct concept
geography:Elevation;

// Qualified and distributed quality
(ecology:AboveGround ecology:Biomass) of each biology:Tree in kg;

// Derived observables
presence of biology:Tree;
count of biology:Tree;
probability of hydrology:FloodEvent;

// Relational query
infrastructure:TransportLink
  linking geography:Origin
  to geography:Destination;

// Filtered individual query
each biology:Tree whose ecology:Biomass > 100.kg;
```

In a model, the same language annotates a resource:

```kim
model urn:klab:agency:elevation:global:dem
  as geography:Elevation in m
;
```

The URN identifies the asset; the observable says what it can contribute.
Semantic discovery and ranking need both.

## 12. Authoring guidance

- **Express meaning before implementation.** Write what a user would ask for,
  not the filename, algorithm, provider, or storage layout.
- **Use the active worldview.** Reuse stable concepts and import the namespaces
  required by the host document.
- **Parenthesize complex expressions.** Human review should not depend on
  guessed operator scope.
- **Separate semantics from mediation.** Put meaning in the expression and
  units or currency in `in`.
- **Keep metadata secondary.** If a distinction affects compatibility or
  resolution, represent it semantically rather than only as a tag.

## 13. Review checklist

Check that:

- the expression has one clear main observable;
- every namespace and authority resolves under the intended worldview;
- predicates and operators are valid for their operands;
- parentheses make complex scope unambiguous;
- `each` reflects the intended distributed observation;
- units, currencies, ranges, and filters are compatible with the semantics;
- optionality and local names serve only their host-level purpose;
- `within` appears only where the host admits contextualized expressions;
- `{{ ... }}` is used whenever the host expects a semantic literal;
- metadata does not substitute for semantic distinctions; and
- both the parser and Reasoner validate the expression.

## 14. Current implementation status

The grammar defines source structure; full validity requires semantic services:

- `ObservableSemanticsForCondition` accepts any concept expression although its
  comment describes a required value operator;
- the bare `!=` form has no operand;
- numeric exponents such as `m^2` are not accepted by the current `Unit` rule
  because `^` is followed by a unit element;
- authorities, units, and semantic relationships need runtime registries or
  worldview reasoning;
- `KimObservableImpl.namespaces()` currently returns an empty set, and its
  formatter omits units, currency, range, formal name, and optionality; and
- parser acceptance does not prove that a compatible model, resource, adapter,
  or runtime exists.

Language evolution must keep `Observable.xtext`, `KimConcept`,
`KimObservable`, adapters and validators, Reasoner tests, and this guide in
sync. Because `.kwv`, `.kim`, and `.kactor` inherit this grammar, regression
fixtures should cover stand-alone expressions and every host embedding form.
