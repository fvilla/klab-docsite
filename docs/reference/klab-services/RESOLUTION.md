# Observation resolution in k.LAB

This document describes the observation-resolution path implemented by `ResolverService`, starting
at `ResolverService.resolve(Observation, ContextScope)`. It records the current behavior, the
contracts at the resolver/runtime boundary, the state that survives between calls, and known gaps.
It is intended as a baseline for changes to resolution logic, dataflow encoding, inter-resolution
state, and reentrancy.

The description reflects the source in this repository as inspected on 2026-07-30. Statements
marked **implemented** describe code that runs now. Statements marked **incomplete** or **risk**
describe code that exists but does not yet fulfill the apparent contract. “Should” is reserved for
recommendations, not current behavior.

## 1. Executive summary

Resolution is a planning phase between runtime observation registration and runtime
contextualization:

1. `RuntimeService` registers an unresolved observation and opens submission/resolution
   transactions.
2. It calls `Resolver.resolve(...)`, locally or through `ResolverClient`.
3. `ResolverService` asynchronously creates a fresh `ResolutionCompiler`.
4. `ResolutionCompiler` queries existing runtime knowledge, asks the reasoner for observation
   strategies, asks resource services for candidate models, validates contextualizers with the
   runtime, and builds a `ResolutionGraph`.
5. `DataflowCompiler` turns the successful graph into nested `Actuator` objects and `ServiceCall`
   computations.
6. The runtime compiles those actuators into executors, commits the resolution transaction, runs
   contextualization, and commits the submission transaction.

Two different graphs are involved and must not be confused:

- `ResolutionCompiler.resolutionCache` is a per-call graph of runtime assets used to record
  parent/child registration during one compilation. It currently has no read side.
- `ResolutionGraph` is the resolver's semantic proof/plan: observations, strategies, models, and
  references connected by coverage-bearing edges. A root instance is stored in the context scope,
  but its intended cross-call catalog is not implemented.

The dataflow produced by one resolution is an incremental plan against the knowledge graph as it
exists at that moment. A separate runtime workflow must eventually assemble those fragments,
explicitly encode submitted inputs, close internal references, and export a reconstruction
dataflow that can recreate an entire selected knowledge graph without resolving each observation
again. The extraction and external-execution APIs for that workflow currently exist only as
stubs.

The runtime HTTP exchange currently uses Jackson polymorphic JSON for the executable `Dataflow`.
The architectural persistence format is instead the **observation language** defined by
`../klab-languages/org.integratedmodelling.languages.observation/src/org/integratedmodelling/languages/Observation.xtext`.
The text currently saved in activity metadata is only a
demonstrational, incomplete encoding of that language; the runtime does not yet rebuild and
re-execute a dataflow from it.

## 2. Main classes and responsibilities

| Class | Current responsibility |
| --- | --- |
| `ResolverService` | Service lifecycle, asynchronous root entry point, context instrumentation, model ingestion, submitted-resource handling, and an incomplete observation-language encoder |
| `ResolutionCompiler` | Recursive resolution policy: runtime query, strategies, models, dependencies, coverage, and runtime requirement checks |
| `ResolutionGraph` | Mutable intermediate graph and shared context-level resolver state |
| `PrioritizerImpl` | Orders models using configured/model-specific ranking criteria |
| `DataflowCompiler` | Converts a successful `ResolutionGraph` into `DataflowImpl` and nested actuators |
| `ResolverClient` / `ResolverController` | Remote request construction and asynchronous job transport |
| `RuntimeService` | Owns observation registration, transactions, resolver invocation, executable compilation, contextualization, and commit/failure handling |
| `CompiledDataflow` | Runtime-side validation, observation binding, storage creation, dependency ordering, and executor construction |
| `DataflowGraph` | Planned server-side extraction and adaptation of a cumulative provenance/dataflow graph; currently a stub |
| `DataflowEncoder` | Produces the current demonstrational observation-language representation stored for diagnostics/provenance |

Important contracts are in `Resolver`, `Dataflow`, `Actuator`, `ContextScope`,
`ResolutionConstraint`, and `Coverage`.

## 3. Entry conditions established by the runtime

The normal caller is `RuntimeService.submit(...)`, not application code calling the resolver
directly.

Before calling the resolver, the runtime:

- validates or registers the submitted observation;
- establishes submission and resolution activities and transactions;
- links the observation, context, observer, cohort, and activities in the pending knowledge-graph
  transaction;
- creates a resolution scope with `executing(...).contextualizeFor(observation)`;
- serializes the active resolution constraints into resolution-activity metadata;
- handles predefined `Observation.ContextualizationData` itself when the adapter is available,
  bypassing `ResolverService.resolve(...)`.

Observation IDs are semantically significant:

- `id > 0`: an existing, resolved runtime observation;
- `id == Observation.QUERY_ID` (`0`): a transient query or query result, never a stored graph
  asset;
- `id < 0`: a registered but unresolved observation;
- `id == Observation.UNASSIGNED_ID` (`-1`): not registered and illegal for normal submission.

The resolver assumes that `declareContextScope(...)` has already instrumented the context with a
root `ResolutionGraph`. Calling `resolve(...)`, `submitResource(...)`, or
`getSubmittedResources(...)` without that declaration currently leads to a null dereference.

## 4. Root method: `ResolverService.resolve`

`ResolverService.resolve(observation, contextScope)` returns a `CompletableFuture<Dataflow>` built
with `CompletableFuture.supplyAsync(...)`.

No executor is supplied, so work runs on Java's default asynchronous executor (normally the common
fork-join pool). Each call constructs:

```text
new ResolutionCompiler(service)
    -> resolve(observation, scope)
    -> ResolutionGraph
    -> new DataflowCompiler(observation, graph, scope).compile()
    -> Dataflow
```

If the returned graph is empty, the fallback is exact:

- a non-collective observable with `SemanticType.SUBJECT` receives a non-empty, computation-free
  `Dataflow.trivial(...)`, meaning its unexplained existence is accepted;
- every other observable receives `Dataflow.empty(...)`, meaning mandatory resolution failed.

This check is narrower than `SemanticType.isSubstantial(...)`: it only tests `SUBJECT`.

Exceptions are not converted to resolver notifications here. They complete the future
exceptionally. In the normal runtime path, `RuntimeService` catches that exceptional completion,
fails the resolution scope, and substitutes an empty dataflow with an error notification.

### Reentrancy consequence

The compiler object is per call, which is good isolation. The context-level `ResolutionGraph`
objects and their shared collections are not isolated, and the future runs concurrently by
default. Section 11 details the resulting risks.

## 5. ResolutionCompiler: root observation path

### 5.1 Per-call initialization

A fresh compiler creates a directed `resolutionCache`, inserts `RuntimeAsset.CONTEXT_ASSET`, and
keeps a reference to the resolver service. This graph is populated by `getObservationGeometry(...)`
and `requireObservation(...)`, but no code consults it to detect recursion, duplicate work, or
cycles. It is currently write-only bookkeeping.

The compiler also declares a local minimum worthwhile contribution of `0.15`. A second static
field with the same value exists in `ResolverService` but is unused.

### 5.2 Obtaining the parent graph

The public compiler entry point calls:

```text
resolve(observation, scope, ResolverService.getResolutionGraph(scope))
```

The retrieved object is the root graph installed in `declareContextScope(...)`. Recursive work
usually happens in child `ResolutionGraph` instances, which share selected maps/lists with that
root.

### 5.3 Positive-ID short circuit

The first recursive observation check is:

```text
if observation.id > 0: return parentGraph
```

At the root this produces a valid non-empty dataflow with no computation. Inside other branches,
positive observations are normally handled earlier as references, so this short circuit is mostly
a root “nothing to resolve” path.

### 5.4 Geometry selection

`getObservationGeometry(...)`:

1. records a parent-to-observation edge in the per-call `resolutionCache`;
2. starts from `observation.getGeometry()`;
3. if geometry is null and the semantics are dependent and a context observation exists, inherits
   the context observation's geometry;
4. returns null otherwise.

A null or empty geometry makes resolution return an empty graph without adding an explanatory
notification.

The geometry becomes a worldview-bound `Scale` through `GeometryRepository.scale(geometry,
scope)`.

### 5.5 Querying knowledge that already exists

Before model resolution, `query(...)` asks the runtime for existing knowledge only for:

- contextual qualities, using direct positive-ID lookup; and
- enumerable collective substantials: subjects, agents, events, and relationships.

Other semantics receive a synthetic zero-coverage `QueryMatch` without a runtime call.

For a quality, the compiler builds a probe with the requested observable and scale, then calls
`scope.getObservation(probe)`. A match is treated as complete by definition and becomes the
positive-ID reference. Quality presence is not estimated by intersecting geometries.

For an enumerable collective, the detached query is:

```text
scope.observation(observable)
    .geometry(requestedScale)
    .query()
    .submit()
    .join()
```

Although the outer resolver API is asynchronous, this step blocks the resolver worker until the
runtime query future completes.

The result is normalized into:

- the returned query observation;
- the observation to reference in the dataflow;
- requested and covered scales;
- a `Coverage` measured by unioning the covered scale into a zero-initialized requested scale.

A collective query view may remain an ID-0 reference; `ResolutionGraph` assigns it a synthetic
negative key for the duration of graph compilation.

Complete existing coverage creates a reference-only child graph and stops semantic resolution.

Partial coverage is retained as a reference and resolution continues for `missingScale(...)`.
Scale exclusion is not universally representable because a `Scale` is a Cartesian product of
extents and not all extents implement exclusion. The compiler checks the proportions of the
computed complement. If they do not add up, it deliberately resolves the full requested scale
again instead of risking under-resolution.

### 5.6 Reuse from previous resolutions

After the runtime query, the compiler calls:

```text
parentGraph.getResolving(observable, scale)
```

It would accept cached resolvables whose gain is at least `0.15`, unioning contributions until
coverage is complete.

**Incomplete:** `ResolutionGraph.getResolving(...)` always returns an empty list and
`ResolutionGraph.accept(...)` does nothing. No previous semantic plan is reused.

### 5.7 Root strategy loop

The compiler adds a k.LAB provenance constraint to a derived scope, then asks:

```text
Reasoner.computeObservationStrategies(observation, scope)
```

Strategies are tried in returned order. Each is resolved into its own child graph. Irrelevant
coverage is discarded. The loop stops at the first strategy graph considered complete.

Only after a complete strategy is found are the retained strategy graphs merged into the
observation graph. If no strategy completes, the method returns a new empty graph, discarding the
partially built graph and its query reference from the result.

`Observation.ContextualizationData` branches remain in this method but are TODOs. In the standard
runtime submission path, direct predefined contextualization is intercepted before calling the
resolver, so these TODOs primarily affect alternative/direct resolver use.

## 6. Strategy operations

Each `ObservationStrategy` creates a child graph initialized at zero coverage. Operations are
processed in declaration order.

### 6.1 `RESOLVE`

`RESOLVE` means resolve another observable:

1. `contextualizeScope(...)` validates that a dependent has a context observation, reporting a
   scope error if it does not.
2. It adds a `Geometry` resolution constraint containing the requested scale.
3. The observable is queried against runtime knowledge.
4. If needed, an unresolved observation is registered for the missing geometry.
5. That observation is recursively resolved.
6. Relevant results are merged into the strategy graph with the operation ID as the edge's local
   name.

`contextualizeScope(...)` currently does not alter the scale for collective semantics or use the
`resolutionSoFar` argument.

### 6.2 `OBSERVE`

`OBSERVE` searches for models that can produce the operation's observable:

1. contextualize the scope;
2. call `ResourcesService.resolveModels(observable, scope)`;
3. ingest returned namespace documents into runtime `Model` objects;
4. rank models with `PrioritizerImpl`;
5. try models in sorted order;
6. retain relevant models and stop when coverage is complete;
7. merge accepted model graphs with `operation.getTransformationTarget()` as the local name.

The notifications carried by the `ResourceSet` are currently not copied into resolver output.

### 6.3 `APPLY`

`APPLY` sends all operation contextualizables to
`RuntimeService.resolveContextualizables(...)`. An empty requirement set rejects the strategy.
Otherwise, service prototypes are fetched as needed, and the external requirements are accumulated
in the root resolution graph.

**Incomplete:** the accepted APPLY contextualizables are not emitted by `DataflowCompiler`.
`compileStrategy(...)` ends with a TODO to add APPLY work to the observation actuator. A strategy
can therefore pass capability validation and contribute dependencies without producing the
corresponding computation.

## 7. Model resolution and ranking

### 7.1 Ingesting model documents

`ResolverService.loadModel(...)` adapts `KimModel` into `ModelImpl`:

- resolves output observables and dependencies with the reasoner;
- copies annotations and metadata;
- records namespace, project, scope, and scenario status;
- converts model resource URNs into a contextualizable;
- appends declared contextualization;
- assigns `Coverage.universal()`.

Actual namespace/model coverage, learners, annotation processing, and processed symbol metadata are
TODOs. Assigning universal coverage means model coverage filtering cannot currently express the
source model's true spatial or temporal limits unless other code reconstructs them.

### 7.2 Ranking

`PrioritizerImpl` builds a lexicographic comparator chain from service defaults overridden by each
model's resolution criteria. Implemented standard scores include lexical scope and
space/time coverage, specificity, and coherency. Many declared criteria return `0`.

Lexical scope gives scenarios the highest score, followed by the active resolution namespace and
project. The namespace/project constraints are added while recursively resolving a model, so they
influence that model's dependencies.

**Risk:** `compare(o1, o2)` uses the criterion order from `o1`. If candidate models declare
different criterion orders, reversing the operands can use a different comparator chain, violating
the symmetry/transitivity required by Java sorting.

Blacklist, whitelist, `UsingModel`, parameters, additional observables, and several other
documented resolution constraints are not visibly enforced by this resolver path.

### 7.3 Resolving one model

For each model:

1. add `ResolutionNamespace` and `ResolutionProject` constraints;
2. ask the runtime to resolve/validate all model contextualizers;
3. reject the model if requirements are empty;
4. cache runtime `ServiceInfo` prototypes used later to bind tagged inputs;
5. merge external requirements into the root graph;
6. recursively resolve every model dependency;
7. ignore unresolved optional dependencies and reject the model on unresolved mandatory ones;
8. merge successful dependencies with their stated names.

Geometry/semantic constraints returned with runtime requirements are not filtered here.

## 8. ResolutionGraph semantics

### 8.1 Nodes and edges

Nodes are `Resolvable` objects:

- `Observation`;
- `Observable` reference targets;
- `ObservationStrategy`;
- `Model`.

Edges point from a target to what resolves it. Each `ResolutionEdge` contains:

- coverage;
- a local name used to bind model/strategy inputs;
- an observation lookup ID for reference edges.

The graph uses JGraphT `DefaultDirectedGraph`, which does not allow parallel edges.

**Risk:** the same node cannot be connected twice to the same parent with different local names or
coverage records. Repeated use of one semantic/model object can silently lose edge-specific
binding information unless distinct node identities are guaranteed.

### 8.2 Coverage algebra

A child graph starts:

- at coverage `1.0` for a `Model`, because all mandatory dependencies intersect its validity;
- at coverage `0.0` for observations, observables, and strategies, because alternatives union
  their contributions.

The target's native model/observation coverage is then intersected into the initial coverage when
available.

Merging a child:

1. copies all child vertices and edges;
2. adds an edge from the parent target to the child target;
3. assigns either the child's resolved reference ID or a synthetic internal ID;
4. intersects coverage for a model parent or unions it otherwise.

The graph reports proportional coverage through `getResolvedCoverage()` and the complete
`Coverage` object through `getCoverage()`.

### 8.3 Shared versus child-local state

Child graphs share these objects with their parent:

- `observations`, used to recover referenced observations by edge ID;
- `localResources`;
- `serviceInfos`;
- `rootScope`.

Dependencies are held only on the root graph and accessed through `rootGraph()`.

Each child has its own JGraphT graph, target, coverage, notification list, and parent pointer.

### 8.4 What actually survives between calls

`ResolverService.declareContextScope(...)` stores one root `ResolutionGraph` under the private
`__RESOLUTION_GRAPH__` scope-data key. It also reloads persistent submitted resources into that
graph's `localResources`.

What survives:

- submitted local resources;
- any observation/service-info entries added through child graphs because their maps are shared;
- the latest root dependency set.

What does not currently become reusable resolution state:

- successful child graph vertices and edges are never merged back into the stored root graph;
- `getResolving(...)` is a stub;
- `accept(...)` is a stub;
- the per-call `resolutionCache` is discarded;
- no completed dataflow catalog is supplied to `DataflowCompiler`;
- local submitted resources are stored but not converted into immediate models.

Consequently, the current implementation effectively resolves afresh on each call, apart from
runtime knowledge queries and incidental shared metadata.

## 9. Dataflow compilation

`DataflowCompiler.compile()` now copies the following resolution output into `DataflowImpl`:

- a context-specific name;
- a transport-safe `Geometry` projection of the requested coverage;
- proportional `resolvedCoverage`;
- accumulated `ResourceSet` requirements;
- root actuator computation;
- resolver notifications.

Each actual root node returned by `ResolutionGraph.rootNodes()` is compiled. A non-observation root
is rejected as an illegal state.

### 9.1 Observation compilation

An observation becomes a reference actuator when:

- its ID is positive; or
- its ID is already in the compiler's per-dataflow catalog.

Otherwise the compiler walks outgoing resolution edges:

- `ObservationStrategy` creates an `OBSERVE` actuator and recursively compiles strategy content;
- `Observable` creates a `REFERENCE` actuator from the graph's observation lookup.

When strategies and existing references both contribute, references become children of every
strategy actuator. When there are only references, they become the returned root actuators.

### 9.2 Strategy and model compilation

A strategy compiles:

- model children through `compileModel(...)`;
- observation children through recursive `compileObservation(...)`.

A model:

- compiles dependent observations/references as children of the observation actuator;
- adapts its contextualizers into runtime `ServiceCall`s;
- uses cached `ServiceInfo` input tags/local names to override a call parameter with an
  `Identifier`;
- builds quality sharding hints from `@type`, `@split`, `@maxSize`, `@minSplitSize`, and
  `@fillCurve` annotations.

Contextualizable adaptation supports:

- direct service calls;
- resource URNs;
- according-to/classification/lookup tables;
- expressions;
- literals;
- target metadata (`_target`, `_targetId`).

**Risk:** an unsupported or structurally empty contextualizable produces `null`, which is added to
the actuator computation. Failure then occurs later and less clearly during encoding or runtime
compilation.

**Incomplete:** strategy APPLY computations, transformation-target internal IDs, explicit actuator
dependency links, inherited parent dataflow catalogs, and several contextualizable metadata fields
remain TODO.

### 9.3 Fixed while producing this document

Three circumscribed issues were corrected:

1. compilation used to iterate each graph root but repeatedly compile the original requested
   observation; it now compiles the actual root node and its geometry;
2. resolver requirements and coverage were dropped when constructing `DataflowImpl`; requirements,
   a plain `Geometry` projection, and proportional coverage are now copied;
3. unconditional debug/profane `System.out` output was removed from the graph/compiler.

`Coverage` is resolver-local state and must not cross a service boundary. An initial version of fix
2 assigned the live `CoverageImpl` to `DataflowImpl`. Remote JSON decoding then failed because the
polymorphic decoder attempted to instantiate that runtime implementation. `DataflowImpl` and
`EmptyDataflow` now type their coverage property as `Geometry`, matching the `Dataflow` interface,
and `DataflowCompiler` explicitly calls `coverage.as(Geometry.class)`. The numeric fraction remains
available separately as `resolvedCoverage`.

This also establishes a broader DTO rule for resolution work: transported DTOs and their nested
values should be ordinary mutable POJOs with no live resolver/runtime implementation state. Records
are deliberately avoided in this implementation.

These fixes are covered by `DataflowCompilerTest` and `DataflowCoverageSerializationTest`.

### 9.4 Incremental resolver output versus context reconstruction

The dataflow returned by one call to the resolver is **incremental**. It is compiled for the
current runtime context and may contain `REFERENCE` actuators pointing to observations that already
exist in the runtime knowledge graph. Re-executing that fragment in an empty digital twin is not
expected to reconstruct its prerequisites.

This is also reflected in the `ContextScope.getDataflow()` contract: a scope-level view may be a
subgraph focused on one observation and may reuse information available in upstream scopes. The
same contract also anticipates a root context dataflow assembled from all incremental resolutions,
capable of recreating the context when run again. That assembly path is not implemented yet.

Future code must keep these two artifacts explicit:

- **incremental resolution dataflow:** the minimal delta needed to resolve one request against a
  particular knowledge-graph state;
- **reconstruction dataflow:** an assembled, self-sufficient plan (plus declared external
  prerequisites) that can reconstruct an entire selected knowledge graph without repeating the
  original sequence of incremental resolution decisions.

Conflating them would either make ordinary resolutions unnecessarily large or produce persisted
dataflows with dangling references that only work in the original runtime.

## 10. Transport, encoding, and decoding

### 10.1 Executable service transport

For a remote resolver:

1. `ResolverClient` creates a `ResolutionRequest` containing the observation and all scope
   resolution constraints.
2. If the context observation is unresolved, it adds an
   `UnresolvedContextObservation` constraint because the remote resolver cannot retrieve it from
   the runtime knowledge graph.
3. The controller restores constraints into the authorized service context and submits the
   resolver future to the context job manager.
4. The client job protocol ultimately decodes the result as `Dataflow.class`.

`JacksonConfiguration` registers polymorphic serializers/deserializers for `Dataflow`, `Actuator`,
`Observation`, `ServiceCall`, `Geometry`, and their nested assets. This JSON representation is the
current service wire format. Resolver `Coverage` objects are not DTOs and cannot cross this
boundary; only their plain geometry projection and scalar resolved fraction can. The JSON form is
not the intended durable, editable, or resource-level representation of a dataflow.

`DataflowSerializationTest` pins name, requirements, and scalar resolver coverage through a JSON
round-trip. `DataflowCoverageSerializationTest` additionally pins the non-null geometry projection
and verifies that no `Coverage` implementation leaks onto the wire. These are only seed contracts;
actuator trees, calls, geometries, identifiers, notifications, and all subtype variants need
broader coverage.

Scope propagation also depends on one runtime invariant: all child `ServiceContextScope` instances
share one observation cache, but a cache miss must load through the child that made the request.
The cache therefore stores values only and does not retain a loader bound to the scope constructor.
This matters when identity adjustment creates a copy before the digital twin is instrumented. The
runtime now creates and assigns the digital twin before publishing the root scope in `ScopeManager`;
remote creation still declares the server-side scope first, applies the returned configuration to
the client peer, and then instruments/registers that peer in its owning service.

### 10.2 Observation language: architectural role

References to k.DL as the dataflow language are obsolete. Dataflows are represented in the
**observation language**, whose grammar is:

```text
grammar org.integratedmodelling.languages.Observation
```

The top-level grammar deliberately hosts two closely related document forms:

```text
strategies <preamble> <observation-strategy definitions>
dataflow   <preamble> <definitions and actuators>
```

This is not merely a shared parser implementation. Observation strategies are a key architectural
element: they express how semantic observations and identifications are obtained, and their
syntactic definitions use the same observation language that represents the resolved executable
plan. Strategy knowledge can be extended together with semantic ontologies, allowing a worldview
or project to add new resolution behavior without hard-coding it into the resolver.

The grammar already gives a dataflow document explicit slots for:

- name, documentation, imports, and version;
- worldview, resource, component, and namespace requirements;
- metadata and coverage;
- definitions;
- nested `reference`, `resolve`, and `observe` actuators;
- the observation strategy used by an actuator;
- child actuators and applied computations.

The intended end state is a lossless bidirectional path:

```text
resolution graph
    -> compiled Dataflow/Actuator model
    -> observation-language source
    -> parsed and validated dataflow
    -> rebuilt executable dataflow
    -> runtime compilation and re-execution
```

Compiled dataflows will be persistable as k.LAB `Resource` objects. Once resource-backed, they can
be catalogued, versioned, transported with their requirements, and annotated or otherwise reused
from k.IM like other k.LAB resources. This closes an important architectural loop: a dynamic
resolution can become curated knowledge, and k.IM can add semantics and annotations to the
persisted executable plan.

The observation-language source must therefore preserve semantics, references, local names,
strategy identity, coverage, requirements, computation order, and every value needed to rebuild
the same executable behavior. Human readability is useful, but reliable reconstruction and
re-execution are the governing contract.

### 10.3 Reconstruction export and external execution

The runtime must eventually be able to extract the provenance/dataflow subgraph for a context,
assemble its incremental resolution fragments, close references over the selected knowledge graph,
and serialize the result in the observation language. This workflow must bypass semantic
resolution when replayed: it reconstructs the already chosen plan and graph rather than asking the
resolver to discover those choices again.

Reference closure needs an explicit rule:

- a reference to an observation inside the exported graph becomes part of the reconstruction
  document;
- a reference intentionally supplied by the target knowledge graph remains external, but must be
  declared as a prerequisite with a stable identity and validity requirement;
- any unresolved reference makes the exported dataflow invalid.

#### Explicitly submitted values

Computed observations can be recreated by re-running their actuators. Objects explicitly submitted
to the knowledge graph have no producing actuator, so their values are inputs to reconstruction
and must be encoded as such. This includes root observations and any other submitted objects,
preserving at least:

- semantic observable;
- geometry;
- metadata;
- identity and relationships required by downstream references;
- the submitted value or a lossless resource-backed representation of it.

At source level these explicitly submitted objects, including roots, are defined in k.IM through
`define` statements. The reconstruction artifact must encode the corresponding definitions. The
observation grammar already has a `DefinitionBody`/`define ... as ...` facility, making it the
natural integration point, although the exact division between the dataflow document and a sibling
definitions document remains a design choice. The encoder/adaptor contract must ensure that the
definition carries enough information to rebuild the runtime object. Large or externally stored
values may be represented through resource references, but the exported artifact must still be
complete: it must carry or declare every value needed for reconstruction.

#### Validity envelope

A replayable dataflow must also say where and when it is valid. These constraints may live in the
dataflow preamble or in a tightly versioned sibling manifest/document, but they must be
machine-readable and validated before execution. At minimum the envelope must be able to constrain:

- worldview and semantic ontology versions;
- required namespaces, components, services, adapters, and resources;
- spatial, temporal, and other coverage;
- required existing observations or knowledge-graph identities;
- contextual assumptions, parameters, and resolution constraints that affect behavior;
- compatible observation-language and runtime versions.

Validity is different from availability: loading all named resources is not sufficient if the
target graph, geometry, worldview, or versions do not satisfy the conditions under which the plan
was compiled.

#### Current stubs

The API already sketches this workflow:

- `ContextScope.getDataflow()` promises a scope-focused view of the cumulative context dataflow;
- `DigitalTwin.getDataflowGraph(context)` promises extraction from provenance;
- `DigitalTwinImpl.getDataflowGraph(...)` constructs a server-side `DataflowGraph`;
- `DataflowGraph.adapt()` is intended to produce a serializable `DataflowImpl`;
- `ClientDigitalTwin.getDataflowGraph(...)` is the client-side access point;
- `RuntimeService.runDataflow(...)` and the dataflow-taking `CompiledDataflow` constructor sketch
  independent/external execution.

The implementation is presently empty or demonstrational:

- `DataflowGraph` returns null requirements and coverage, an empty computation, and null from
  `adapt()`;
- `DigitalTwinImpl.getDataflowGraph(context)` currently ignores the requested context and always
  passes the root scope;
- `ClientDigitalTwin.getDataflowGraph(...)` returns null;
- the independent `CompiledDataflow` constructor is marked unused;
- `RuntimeService.runDataflow(...)` compiles root actuators but does not execute them and returns
  null.

These are parts of one architectural feature: extract, close, assemble, encode, persist, validate,
load, bind to an existing or empty knowledge graph, and execute.

### 10.4 Current demonstrational encoding

The runtime stores:

```text
Utils.Dataflows.encode(dataflow, resolutionScope)
```

in resolution activity metadata. That uses
`org.integratedmodelling.common.services.client.resolver.DataflowEncoder`, which writes:

- a `dataflow <sanitized-name>;` preamble;
- nested actuator type, target/observable, alias, strategy, children, and apply calls.

This output resembles the `dataflow` branch of `Observation.xtext`, but it is incomplete.
Definitions and most preamble fields are TODO, and computations are currently asked to encode with
`KlabLanguage.KIM` rather than consistently using the observation-language context.

Although the sibling language repository defines and parses the grammar, the current resolver and
runtime do not provide an end-to-end source-to-`Dataflow` adaptation, validation, reference
relinking, and execution path. Current output must not yet be treated as a durable replay artifact.

### 10.5 Competing incomplete APIs

There are currently multiple divergent encoding surfaces:

- `ResolverService.encodeDataflow(...)` is an older incomplete encoder intended for this purpose
  but not aligned with the current observation-language grammar;
- `ResolverClient.encodeDataflow(...)` returns `null`;
- `ResolverService.retrieveAsset(...)` returns `null`;
- `DataflowEncoder` is the encoder actually used by the runtime for metadata;
- Jackson JSON is the format actually used for service execution transport.

These should converge on one canonical observation-language codec backed by the grammar in
`klab-languages`. A safe decoder must reject unsupported versions or required constructs, validate
requirements and references before execution, preserve observation/reference identity, and never
rely on Java object identity surviving a round-trip. JSON may remain an internal service transport,
but it must not become a second, semantically divergent persistence contract.

## 11. Reentrancy and concurrency risks

The public API promises asynchronous work, and independent calls can run concurrently. Current
mutable state is not designed around that fact.

### 11.1 Shared context data is not thread-safe

The root and child resolution graphs use:

- `HashMap` for observations and service prototypes;
- `ArrayList` for local resources;
- a mutable `ResourceSet`;
- a plain decrementing `long` for synthetic IDs;
- mutable JGraphT graphs.

Child resolutions share several of these objects. Concurrent resolution or simultaneous resource
submission can race, corrupt collections, reuse synthetic IDs, or lose dependency updates.

### 11.2 Blocking inside asynchronous work

The outer resolver future runs on the common asynchronous pool, then blocks on runtime query
`.join()`. Under load, reciprocal resolver/runtime calls can exhaust common-pool capacity or create
hard-to-diagnose latency amplification.

### 11.3 No explicit resolution transaction

The runtime has graph transactions, but the resolver's context cache does not have a begin/commit/
rollback boundary. Child graphs mutate shared maps and dependencies while exploring strategies,
including strategies that are later rejected. A failed resolution can therefore leave incidental
state behind.

### 11.4 Recommended state model

A reentrant design should distinguish:

- **immutable request snapshot:** observation, effective constraints, context/observer IDs,
  requested geometry, service catalog/version;
- **per-attempt workspace:** recursion stack, query results, candidate graphs, notifications,
  requirements, synthetic reference IDs;
- **committed context catalog:** immutable or copy-on-write entries from successful resolutions,
  keyed by semantic identity plus geometry, constraints, worldview, and service/resource versions;
- **runtime references:** stable observation IDs/URNs, never live object identity;
- **commit protocol:** atomically publish a successful catalog delta or discard the entire attempt.

A future cache key must include every input capable of changing model eligibility or ranking.
Observable equality alone is insufficient.

## 12. Known weaknesses and vulnerable spots

| Priority | Area | Current weakness | Consequence |
| --- | --- | --- | --- |
| Critical | Strategy compilation | APPLY operations are validated but not emitted | A “successful” plan may omit intended computation |
| Critical | Inter-resolution state | Cache lookup/accept are stubs and successful graphs are not committed | No semantic reuse; future partial cache changes could be inconsistent |
| Critical | Reentrancy | Shared graph maps/lists/dependencies/IDs are unsynchronized | Races and cross-request state leakage |
| Critical | Reconstruction export | `DataflowGraph` extraction/adaptation is empty | No whole-context dataflow can be assembled from incremental resolutions |
| High | Encoding | Observation-language output is not grammar-complete or round-trippable | Persisted source cannot yet rebuild and replay a resolution |
| High | External execution | `runDataflow(...)` compiles partially but never executes and returns null | Persisted or external plans cannot run against a knowledge graph |
| High | Submitted inputs | Explicitly submitted objects have no encoded `define` values | Whole-graph replay loses root/input observations and their data |
| High | Validity | No executable validity envelope is enforced | A plan may run with incompatible graph state, geometry, semantics, or resources |
| High | Failure reporting | Many empty-graph exits carry no notification | Runtime reports only generic “empty dataflow” |
| High | Graph representation | No parallel edges | Repeated bindings to the same node can lose local-name/coverage information |
| High | Cycle handling | Per-call resolution cache is never consulted | Recursive semantic/model dependencies can recurse indefinitely |
| High | Model fidelity | Ingested models receive universal coverage | Ranking/coverage can accept geographically or temporally invalid models |
| High | Constraint enforcement | Many constraint types are not enforced | Caller intent may be serialized but ignored |
| High | Ranking comparator | Operand-dependent criterion order | Sorting may be inconsistent for model-specific ranking policies |
| Medium | Async execution | Common-pool task blocks on `.join()` | Pool starvation and latency under load |
| Medium | Notifications | ResourceSet notifications are discarded | Missing diagnostics for model/resource failures |
| Medium | Contextualizables | Unsupported form compiles to null | Delayed null failure rather than resolver diagnostic |
| Medium | Geometry | Dependent-without-context logs an error but continues | Work may continue with an invalid semantic context |
| Medium | Thresholds | Duplicate hard-coded `0.15`; service copy unused | Scope configuration cannot tune contribution policy |
| Medium | Scope lifecycle | Resolver graph presence is assumed | Direct/misordered calls fail with null dereference |
| Low | Compiler catalog | Unused local `Map<Observable,String>` shadows the ID catalog concept | Confusing maintenance surface |
| Low | Observation-language encoders | Service/client encoders diverge or return null | Public encoding behavior depends on implementation |

The first implementation phase should add diagnostics and tests before filling cache or APPLY
behavior, because both affect the semantic contract of generated plans.

## 13. Testing strategy

### 13.1 Layer 1: deterministic unit contracts

Test `ResolutionGraph` without services:

- model coverage intersects while alternatives union;
- complete/empty/relevant thresholds;
- reference lookup for positive IDs and multiple ID-0 query views;
- synthetic IDs are unique within one attempt;
- child merge preserves local name and coverage;
- repeated source/target pairs have a defined policy;
- notifications and requirements follow accepted graphs only;
- failed candidate graphs leave no committed state.

Test `DataflowCompiler` with small hand-built graphs:

- actual root nodes are compiled exactly once;
- existing references are attached to each contributing strategy;
- model dependencies retain their stated local names;
- transformation targets bind the intended inputs;
- every contextualizable variant becomes the correct runtime functor;
- unsupported contextualizables fail with a specific notification;
- APPLY operations appear in the final actuator;
- sharding annotations are validated and propagated;
- requirements, coverage, proportional coverage, and notifications survive compilation.

Test `PrioritizerImpl`:

- comparator antisymmetry and transitivity over models with different custom criteria;
- deterministic tie handling;
- scenario/namespace/project precedence;
- every enabled criterion has a non-placeholder score;
- constraints blacklist, whitelist, and force models as specified.

### 13.2 Layer 2: resolver orchestration with service fakes

Use controlled fake `Reasoner`, `ResourcesService`, and `RuntimeService` implementations:

- no geometry;
- dependent without context;
- complete direct contextual quality reference;
- absent contextual quality proceeding to semantic resolution;
- collective ID-0 query view with multiple contributors;
- rejection of detached quality and non-enumerable ID-0 queries;
- temporal union across collective events and functional relationships;
- absence of temporal cohort bounds for continuant substantials;
- one complete strategy;
- several incomplete model contributions whose union completes;
- optional versus mandatory dependencies;
- unsupported service requirements;
- recursive/cyclic model dependencies;
- predefined contextualization and direct resolver invocation;
- exception and cancellation propagation.

Assertions should cover both graph/dataflow shape and notifications, not only `isEmpty()`.

### 13.3 Layer 3: codec compatibility

Create a versioned golden corpus of dataflows containing:

- every actuator type;
- nested children and repeated references;
- every `ServiceCall` parameter value supported by Jackson;
- coverage and resolved geometry;
- requirements with all resource classes and services;
- annotations, identifiers, expressions, lookup tables, and classifications;
- info/warning/error notifications;
- unknown optional and required fields.

For JSON transport, assert semantic equality after encode/decode and compatibility with at least
the previous released schema.

For observation-language persistence, use grammar-valid golden sources covering both the
`strategies` and `dataflow` document forms. Require:

```text
compile Dataflow
    -> encode observation-language source
    -> parse
    -> adapt and validate
    -> rebuild Dataflow
    -> compile for runtime execution
```

The rebuilt dataflow must preserve actuator/reference identity, strategy URNs, local bindings,
execution order, requirements, metadata, and coverage. Re-encoding the rebuilt form should be
semantically idempotent. Persisting it as a `Resource`, retrieving it, and annotating/referencing it
from k.IM should be covered by integration tests.

Maintain separate golden cases for:

- one incremental resolution fragment whose references are deliberately external;
- one whole-context reconstruction export with every internal reference closed;
- submitted root and non-root objects encoded through `define`, including values, semantics,
  geometry, and metadata;
- a reconstruction artifact with external prerequisites and a validity envelope;
- rejection caused by an unresolved reference or invalid worldview/resource/coverage constraint.

### 13.4 Layer 4: runtime integration

Run `RuntimeService.submit(...)` against an in-memory/test digital twin:

- resolution and submission transactions commit in order;
- failure rolls back observations, executors, storage, provenance, and resolver catalog deltas;
- query ID-0 observations are never persisted;
- positive references retain the correct knowledge-graph links;
- child submissions complete before parent transaction commit;
- contextualization uses the intended geometry and storage;
- activity metadata records a decodable dataflow or is explicitly diagnostic-only.
- extracting a root-context dataflow, clearing the target digital twin, and replaying it recreates
  the same selected observations, links, metadata, and computable values;
- a reconstruction export does not call semantic resolution during replay;
- an external dataflow binds declared prerequisites in an existing graph and rejects missing or
  incompatible bindings without partially mutating the graph;
- explicitly submitted values survive export, resource persistence, reload, and replay.

Existing `RuntimeServiceQueryTest` is the starting point for query identity, coverage, and
contributor geometry. `ResolutionCompilerQueryTest` protects direct quality reuse and
`CohortGeometryTest` protects the occurrent/continuant temporal-boundary distinction.

### 13.5 Layer 5: concurrency and reentrancy

Use barriers rather than sleeps:

- resolve two unrelated observations in one context concurrently;
- resolve the same observable/geometry concurrently and define deduplication behavior;
- resolve overlapping geometries concurrently;
- submit a local resource while resolution reads the scenario catalog;
- cancel one waiter while another shares work;
- inject failure immediately before catalog commit;
- reconnect a remote resolver during a request;
- stress synthetic reference IDs and requirement merges.

Verify deterministic results, no collection exceptions, no cross-request edges, and an atomic
committed catalog.

### 13.6 Property and mutation testing

Coverage and graph composition are suitable for generative tests:

- union is monotonic;
- intersection is non-increasing;
- coverage remains in `[0, 1]`;
- accepted contributions never reduce non-model coverage;
- reordering independent candidates does not change the final semantic coverage;
- encode/decode is idempotent modulo transient IDs;
- a completed dataflow has no dangling reference ID.

Mutation tests should target branch conditions around completeness/relevance, optional
dependencies, query IDs, and graph merge direction.

## 14. Tests added with this trace

- `klab.services.resolver/.../DataflowCompilerTest`
  - proves the actual graph root is compiled rather than the original request;
  - proves projected geometry, proportional coverage, and requirements reach `DataflowImpl`.
- `klab.services.resolver/.../DataflowCoverageSerializationTest`
  - reproduces the remote-boundary failure caused by transporting `CoverageImpl`;
  - proves the plain geometry projection survives a polymorphic JSON round-trip and is not a
    `Coverage` implementation.
- `klab.core.common/.../DataflowSerializationTest`
  - proves dataflow name, requirements, and proportional resolver coverage survive polymorphic
    Jackson serialization through the `Dataflow` interface.

Focused verification commands:

```powershell
.\mvnw.cmd -q -pl klab.services.resolver -am "-Dtest=DataflowCompilerTest,DataflowCoverageSerializationTest" "-Dsurefire.failIfNoSpecifiedTests=false" test
.\mvnw.cmd -q -pl klab.core.common -am "-Dtest=DataflowSerializationTest" "-Dsurefire.failIfNoSpecifiedTests=false" test
```

## 15. Suggested improvement sequence

1. Define invariant-rich test fixtures for graphs, coverage, and actuator trees.
2. Make all failure exits produce structured resolver notifications.
3. Complete strategy APPLY and transformation/local-name compilation.
4. Add explicit recursion/cycle detection.
5. Define a per-attempt resolution workspace and atomic context-catalog commit.
6. Implement cache keys and invalidation before implementing `getResolving(...)`.
7. Make the resolver executor and runtime-query composition explicit and non-blocking.
8. Implement provenance-to-`DataflowGraph` extraction, incremental-fragment assembly, reference
   closure, submitted-value definitions, and validity-envelope generation.
9. Complete the observation-language codec defined by `Observation.xtext`, including strict
   source-to-dataflow validation, resource persistence, re-execution, and compatibility tests.
10. Complete transactional external dataflow execution against empty and existing knowledge
    graphs.
11. Enforce all advertised resolution constraints and make ranking comparator behavior global and
    deterministic.
12. Add concurrent integration tests before enabling shared-work deduplication.

## 16. Trace map

Start future investigations at these methods:

- `ResolverService.resolve`
- `ResolverService.declareContextScope`
- `ResolutionCompiler.resolve(Observation, ContextScope)`
- `ResolutionCompiler.query`
- `ResolutionCompiler.resolve(ObservationStrategy, ...)`
- `ResolutionCompiler.resolve(Model, ...)`
- `ResolutionCompiler.resolve(Observable, ...)`
- `ResolutionGraph.merge`, `addReference`, `getResolving`, and `accept`
- `DataflowCompiler.compile`, `compileObservation`, `compileStrategy`, and `compileModel`
- `PrioritizerImpl.compare` and `computeCriteria`
- `ResolverClient.resolve` and `ResolverController.resolveObservation`
- `RuntimeService.submit`, `compile`, and `createPredefinedDataflow`
- `RuntimeService.runDataflow`
- `CompiledDataflow.compile`, `requireObservations`, `store`, and executor ordering
- `ContextScope.getDataflow`
- `DigitalTwin.getDataflowGraph` and `DigitalTwinImpl.getDataflowGraph`
- `DataflowGraph.adapt`
- `ClientDigitalTwin.getDataflowGraph`
- `DataflowEncoder.encode`
- `JacksonConfiguration.configureObjectMapperForKlabTypes`
- `../klab-languages/org.integratedmodelling.languages.observation/src/org/integratedmodelling/languages/Observation.xtext`
- observation-strategy parsing/adaptation in `WorkspaceManager` and `LanguageAdapter`

When changing one layer, trace the change through all subsequent layers. In particular, a new graph
edge or actuator field is incomplete until its JSON service representation,
observation-language syntax and adaptation, runtime compiler, `Resource` persistence, k.IM reuse,
provenance behavior, and failure rollback are all defined and tested.
