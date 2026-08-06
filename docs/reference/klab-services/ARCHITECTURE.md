# k.LAB Architecture

k.LAB is a service stack for turning semantic observation requests into a live
digital twin. The interesting part is not that there are four services. It is
that each service owns a different kind of truth, and scopes carry the user's
workflow through all of them without losing identity, context, permissions, or
state.

At a high level:

```text
Resources  -> what knowledge, models, data, components, and adapters exist
Reasoner   -> what those things mean semantically, and how they can observe
Resolver   -> what plan can satisfy an observation in this context
Runtime    -> what actually exists in the digital twin, and what gets executed
```

The Engine sits above this stack. It authenticates the user, starts or discovers
services, builds the client-side service catalog, creates the first user scope,
and advertises that user scope to the services. The four services are the
operational core. They are the services that must be available for ordinary
observation work.

This document describes how those services fit together, how scopes make the
system behave as one workflow across several processes, and how an observation
moves from a semantic request to committed digital twin state.

## Mental Model

k.LAB separates four questions that are easy to blur together:

- What assets are available?
- What do the requested observables mean?
- What should be done to observe them?
- What state and computation actually happen?

Each service answers one of these questions.

The Resources service is the catalogue and source of assets. It knows
workspaces, projects, namespaces, ontologies, observation strategies, resources,
components, adapters, import/export schemata, metadata, and rights.

The Reasoner service is the semantic brain. It loads the worldview, builds the
OWL-backed semantic model, resolves concept and observable expressions, checks
semantic relationships, and turns observation strategy documents into
context-aware observation strategies.

The Resolver service is the planner. Given an unresolved observation in a
context scope, it builds a resolution graph, asks the Reasoner for strategies,
asks Resources for candidate models and assets, asks Runtime whether the
required contextualizers can actually run, and compiles the result into a
dataflow.

The Runtime service is the host of the digital twin. It owns session and context
lifetime, the knowledge graph, storage, transactions, provenance, dataflow
compilation, scheduling, contextualization, and cleanup.

Scopes are the thread that keeps this distributed arrangement coherent. A scope
is the live envelope for identity, services, lifecycle, messages, and digital
twin position. Service code should normally discover collaborators through the
scope it receives, not by constructing service clients directly.

## The Service Stack

The four main services all derive from the same `KlabService` contract through
the shared service base. That common layer gives them a service identity, URL,
status, capabilities, settings, component registry, service secret, import and
export handling, shared typed `info`/`query` inspection, and a `ScopeManager` for service-side peer
scopes.

In this codebase the four concrete service classes are:

- `ResourcesProvider`
- `ReasonerService`
- `ResolverService`
- `RuntimeService`

From there, each service specializes the stack:

```text
Engine
  authenticates users, starts/discovers services, advertises user scopes

Resources
  manages assets, workspaces, worldview sources, components, adapters, rights

Reasoner
  loads worldview semantics, answers semantic questions, computes strategies

Resolver
  creates resolution graphs and dataflows for unresolved observations

Runtime
  owns sessions, contexts, digital twins, transactions, execution, storage
```

The order above is not a call chain for every operation. It is a dependency
shape. Runtime verbs Resolver to resolve an observation. Resolver verbs
Reasoner, Resources, and Runtime. Reasoner loads its worldview from Resources.
Resources can use Reasoner-backed semantic indexing when it is available.
Runtime uses Resources to make sure components, resources, and adapters needed
by a dataflow are visible and usable.

This creates a small, deliberate cycle:

```text
Runtime -> Resolver -> Reasoner -> Resources
        -> Resolver -> Resources
        -> Resolver -> Runtime
        -> Runtime  -> Resources
```

That cycle works because verbs are scoped, service availability is advertised
through scopes, and the Runtime remains the only owner of the digital twin.

### Service Availability

Services distinguish being reachable from being usable.

A service is available when it has initialized enough to accept verbs. A service
is operational when its advertised API can be trusted under its current
configuration and dependencies.

That distinction matters most during startup. Runtime needs its knowledge graph.
Reasoner needs a worldview before semantic answers are meaningful. Resources
can start before semantic search is ready, then become semantically capable when
an operational Reasoner is visible. Resolver can initialize its own libraries
early, but meaningful resolution still depends on the scoped Reasoner,
Resources, and Runtime.

Capabilities are the service's scoped promise. They advertise not only service
type, URL, and ID, but also things such as worldview status, permissions,
components, import/export schemata, storage defaults, and semantic readiness.

### Shared Inspection

`info` and `query` belong to `KlabService`, not to one specialized service. Their common HTTP
transport accepts a `KnowledgeClass`, a requested projection class, and a user scope. The shared
`BaseService` implementation exposes service capabilities/status and the installed component,
adapter, and service-implementation catalogues. It also provides a portable `DomainObject`
projection when a caller needs a representation independent of a concrete descriptor class.

Specialized services override these operations for objects they own. `ResourcesProvider`, for
example, handles resource assets, workspaces, projects, and language documents, then delegates
component, adapter, service and generic `DomainObject` projections to `BaseService`. Client-side
transport lives in `BaseServiceClient`, so reasoner, resolver, resources and runtime clients use the
same endpoints and serialization rules.

## Services In Scopes

Scopes are covered in detail in `SCOPES.md`; the short version for architecture
is this: a scope is a live handle to a user workflow. It contains the identity,
authorized service catalog, lifecycle status, messages, scope data, and, for
context scopes, a position inside a digital twin.

Services are not looked up globally during ordinary work. They are looked up
from the active scope:

```text
scope.getService(ResourcesService)
scope.getService(Reasoner)
scope.getService(Resolver)
scope.getService(RuntimeService)
```

That lookup matters. It means "the Resources service visible to this identity
and this workflow", not "any Resources service on the network".

At client side, the Engine and client scope manager create user, session, and
context scopes. At service side, each service keeps peer scopes in its own
`ScopeManager`. Those service-side scopes mirror the same logical workflow in
that service process.

The important scope levels are:

- `UserScope`: identity-level access to the service catalog.
- `SessionScope`: a user session pinned to one host runtime.
- `ContextScope`: a live digital twin, or a focused view inside one.

The host runtime ID travels with session and context verbs. That is what lets a
non-runtime service reconstruct a peer context scope and still know where the
actual digital twin lives.

### User Scope Advertisement

After authentication, the Engine notifies each service about the user scope and
the services available to that user. Each receiving service creates or updates a
service-side user scope and populates it with service clients. If the advertised
service is the service itself, the local service instance is used directly.

This is why a resolver, reasoner, resources provider, or runtime can ask its
scope for collaborators without knowing whether they are local services, remote
services, or clients to a service started by the Engine.

### Context Peers

Only one runtime hosts a digital twin. Other services may still receive
context-scoped verbs. When that happens, they reconstruct a peer context scope:

```text
incoming identity + scope token + host runtime ID
  -> service-side user scope
  -> service-side session scope
  -> service-side context peer
  -> client digital twin handle pointing back to the host runtime
```

For a non-runtime service, the context peer is not the state owner. It is a
scoped lens with the right identity, service catalog, focus observation,
transaction ID, and remote digital twin handle.

For the host runtime, declaring the context scope creates the actual digital
twin, backed by the runtime's knowledge graph and storage.

## Observation Lifecycle

An observation begins as semantic intent and ends, if successful, as committed
digital twin state with provenance, storage, and messages.

The usual path looks like this:

```text
client context scope
  -> build or receive an Observation
  -> Runtime registers the unresolved observation
  -> Runtime opens submission and resolution transactions
  -> Resolver builds a resolution graph
  -> Reasoner supplies observation strategies
  -> Resources supplies models, resources, adapters, and components
  -> Runtime checks executable contextualizers
  -> Resolver compiles a Dataflow
  -> Runtime compiles and stores execution sequences
  -> Runtime commits resolution
  -> Runtime scheduler contextualizes the observation
  -> Runtime commits contextualization outcomes
  -> scopes publish messages and the knowledge graph becomes queryable
```

The important detail is that the Runtime owns the lifecycle, even though it does
not invent the plan by itself. Runtime asks Resolver for the dataflow, but the
submission transaction, observation identity, knowledge graph links, execution
storage, scheduling, commits, and failure cleanup stay in the runtime.

### Registration

Before resolution, the Runtime validates the requested observation against the
context scope.

If the observation already exists in the knowledge graph, or in the active
transaction, registration can return the existing resolved observation. If the
observation is new, Runtime assigns a negative ID that is unique within the
context. Negative IDs mean "known to the workflow, not yet committed as digital
twin state".

Substantial observations are checked against cohorts and identity. Dependent
observations are checked relative to the current context observation. Qualities
must have a context observation. Missing geometry can be inferred for common
dependent cases from the context observation or observer.

### Submission And Resolution

Submission creates provenance activities and a transaction. Runtime links the
unresolved observation into the transaction graph, creates or finds any needed
cohort, records context and observer relationships, and then asks Resolver to
resolve the observation.

Resolver works inside the context scope it receives. It uses that scope to get
the Reasoner, Resources, and Runtime services. The scope also carries resolution
constraints such as geometry, provenance runtimeAgent, namespace, project, scenario,
observer, and context observation.

Reasoner returns candidate observation strategies that match the observable and
context. Resources returns candidate models and the assets needed to use them.
Runtime confirms whether each contextualizer can actually be executed, either
because it is built in, supplied by a loaded component, or obtainable through
Resources.

The output of planning is a dataflow. The dataflow is not execution yet. It is
an executable description of observations, dependencies, references, service
verbs, resource resolutions, sharding hints, and coverage.

### Compilation And Execution

Runtime compiles the dataflow into execution sequences and stores them in the
current digital twin transaction. A successful resolution transaction commits
the graph and provenance created during planning.

After that, Runtime submits the observation to the digital twin scheduler. The
scheduler runs contextualizers against the compiled execution sequence. Runtime
services, component functions, resource adapters, expressions, lookup tables,
constants, and resource URNs all meet here as executable work.

When contextualization succeeds, Runtime records created or modified
observations, storage, provenance, and any child submissions required by the
result. For example, an instantiator may create child observations that need to
be submitted and resolved in turn.

When contextualization fails, Runtime marks the activity failed and relies on
the transaction and storage cleanup paths to avoid committing partial digital
twin state.

### Persistence And Cleanup

Context lifetime is governed by the digital twin configuration. A context may
be one-off, persistent until service shutdown, idle-timeout based,
reinitialized after inactivity, or persistent until an explicit action.

The Runtime maintenance task scans context information from the knowledge graph.
If a non-persistent context has no live scope, or it has been idle beyond its
configured policy, Runtime closes or deletes it. If a context is configured for
reinitialization, Runtime resets it instead of deleting it.

Closing a context scope disposes the digital twin handle, closes scope data that
needs closing, closes messaging, and releases the service-side peer scope.

## Resources Service

Resources is the memory and catalogue of k.LAB. It knows what can be used.

It manages:

- workspaces and projects;
- parsed k.IM namespaces, ontologies, models, and symbol definitions;
- k.Actors behaviors, applications, scripts, and tests;
- worldview ontologies and observation strategy documents;
- published resources and their metadata;
- resource rights, ownership, review status, and availability;
- components and their contributed libraries, functions, adapters, importers,
  and exporters;
- resource adapter lookup, validation, import, contextualization, and encoding.

Resources is also a language-facing service. It holds parsers and can turn
concept and observable definitions into serialized k.LAB objects. Its standalone
`parseAsset(URL, Class, UserScope)` operation parses k.Actors behaviors, k.IM ontologies and
namespaces, and observation-strategy documents without registering them in a workspace.
That makes it the bridge between files, projects, component archives, and the
runtime objects used by the rest of the stack.

### Resources And The Worldview

When a Resources service is a worldview provider, it can supply the worldview
used by the Reasoner. That worldview is made of ontologies plus observation
strategy documents. Reasoner loads those assets, builds the semantic model, and
keeps the observation strategy catalogue used by resolution.

Resources and Reasoner then continue to reinforce each other. Once an
operational Reasoner is available, Resources can index semantic assets so model
lookup becomes semantic rather than only lexical or structural.

### Resources And Resolution

Resolver depends on Resources for candidate models and their dependencies.
Resources returns enough information for another service to operationalize an
asset: not just "this model exists", but the namespaces, components, resources,
and service locations needed to use it.

Resolver then ingests those assets into its local knowledge repository, turns
k.IM model statements into runtime model objects, and uses them in the
resolution graph.

Runtime also depends on Resources before executing a dataflow. A dataflow may
reference a resource URN, a service call implemented by a component, or an
adapter required to encode data. Runtime asks the scoped Resources service to
make those requirements visible and then loads embeddable components when its
settings allow that.

### Resources And Scopes

Resources is heavily scope-sensitive:

- user scopes determine permissions for creating, updating, deleting, reading,
  importing, exporting, locking, or publishing assets;
- context scopes are used when semantic model lookup depends on the current
  observation context;
- service-side peer scopes let Resources serve resolver and runtime requests
  with the same identity and service graph as the original user workflow.

A Resources service should never be treated as a passive file store. It is an
identity-aware catalogue with live component and adapter knowledge.

## Reasoner Service

Reasoner is the semantic center of k.LAB. It knows what concepts and
observables mean, how they relate, and which observation strategies can apply
in a context.

It manages:

- the loaded worldview and consistency state;
- OWL ontologies and inferred semantic relationships;
- concept and observable resolution;
- semantic compatibility, distance, inheritance, roles, traits, inherency,
  causality, co-occurrence, domains, and relationships;
- observation strategy matching;
- identification strategy selection;
- assisted semantic search and semantic builders.

Reasoner is intentionally not the owner of resources or digital twin state. It
does not decide what is stored in a context and it does not execute models. It
answers semantic questions for services that do those things.

### Loading Knowledge

At startup, Reasoner looks for a Resources service that can provide a worldview.
In local workflows it prefers a local Resources service. Once it retrieves a
worldview, it loads the ontologies into the OWL layer, registers them with the
reasoner, flushes inference, and registers observation strategies.

If semantic loading reports errors, Reasoner marks itself inconsistent. Its
status and capabilities expose that fact so callers can avoid trusting semantic
answers from an unhealthy worldview.

Worldview updates follow the same principle: ontology and strategy changes are
retrieved from the appropriate Resources service, caches are invalidated, the
OWL model is updated, and strategy namespaces are refreshed.

### Observation Strategies

Observation strategies are the main way Reasoner participates in observation
resolution.

For a requested observation and context scope, Reasoner filters strategy
definitions using semantic type, collective/non-collective constraints,
patterns, context variables, strategy functions, and the current context
observation. Matching strategies are contextualized: pattern variables are
substituted, operations are materialized, and contextualizable service verbs are
prepared for Resolver.

Resolver receives these strategies ordered by rank. It still needs to verify
coverage, available models, dependencies, resources, and executability. Reasoner
answers "what could make semantic sense here"; Resolver answers "what plan can
work here"; Runtime answers "what actually ran".

### Reasoner And Scopes

Some semantic operations are context-free, such as asking whether one concept
is a kind of another. Observation strategy computation is context-sensitive.
The context scope tells Reasoner the current context observation, observer,
geometry, transaction, and resolution constraints. That context is what makes a
strategy applicable or irrelevant.

The same Reasoner can therefore serve many users and contexts, but each
strategy request is evaluated in the scope that asked for it.

## Resolver Service

Resolver is the planner. Its central job is to turn an unresolved observation
into a dataflow that Runtime can compile and execute.

It manages:

- context-local resolution graphs;
- ingestion of model assets from Resources into runtime model objects;
- selection and merging of observation strategies;
- model and dependency resolution;
- coverage tracking;
- discovery of required resources, service implementations, adapters, and
  components;
- dataflow compilation;
- scope-local resources produced from contextualization data.

Resolver is deliberately not the owner of the digital twin. It may register
unresolved observations through the context scope so it can plan dependencies,
but Runtime remains responsible for transactions, commits, execution, and
knowledge graph state.

### Resolution Graphs

Each context peer in Resolver is instrumented with a resolution graph. The graph
stores observations, models, observation strategies, service information,
dependencies, notifications, and resources created locally for the context.

During resolution, Resolver first checks whether the graph already contains a
resolvable that can cover the requested observable and geometry. If not, it
creates a child graph for the observation and starts trying strategies.

Coverage matters. Strategies and models are accepted only when they contribute
enough useful coverage, and resolution stops when coverage is complete enough
for the target.

### Planning With The Other Services

Resolver's planning loop is a good summary of the whole architecture:

1. Ask Reasoner for observation strategies matching the unresolved observation.
2. For strategy operations that observe another observable, ask Resources for
   candidate models.
3. Ingest model dependencies and contextualizables locally.
4. Ask Runtime whether the contextualizers required by a strategy or model are
   available, loadable, and compatible.
5. Recursively resolve required observations.
6. Compile the accepted graph into a dataflow.

The Resolver does not assume a model can run merely because it exists. Runtime
must confirm that the contextualizers are supported and that required resources
or components can be made available.

### Scope-Local Submitted Resources

Resolver can also make contextualization results available as resources inside
the same context scope. If a context is persistent, those resources can be kept
in Resolver's resource store and made available again when the context is
reconnected. If a submission asks for publication to a Resources service,
Resolver can hand the resource to that service using the scoped service catalog.

This is how results computed inside a digital twin can become inputs for later
resolution without immediately becoming globally published resources.

## Runtime Service

Runtime is where the digital twin lives. It owns the stateful part of k.LAB.

It manages:

- session and context declaration;
- actual digital twin creation when it is the host runtime;
- the knowledge graph connection;
- context persistence, timeout, orphan cleanup, and shutdown cleanup;
- observation registration and submission;
- transactions, commits, provenance, and activities;
- cohorts and identity checks for substantial observations;
- dataflow compilation into execution sequences;
- scheduler submission and contextualization;
- storage and sharding defaults;
- knowledge graph queries and context reconnection.

The Runtime service is the only service that should be thought of as the owner
of a context. Other services may hold context peers. Runtime holds the digital
twin.

### Sessions And Contexts

A session is pinned to one runtime. A context belongs to a session and is hosted
by that same runtime.

When Runtime receives a context declaration and the context's host service ID is
its own service ID, it assigns a context ID when needed, registers the
service-side context scope, and creates a `DigitalTwinImpl` backed by the
runtime's knowledge graph.

When Runtime receives a context declaration for a context hosted elsewhere, it
uses the shared base behavior and creates a client digital twin handle instead.
That can happen in service-to-service peer reconstruction.

### Runtime As Lifecycle Owner

Runtime's submission path is the backbone of the observation lifecycle. It:

- registers or finds the observation;
- validates context, geometry, adapter visibility, and existing observations;
- creates submission and resolution activities;
- opens scoped digital twin transactions;
- links observations, cohorts, context, observer, and provenance;
- asks Resolver for a dataflow unless predefined contextualization data already
  supplies one;
- compiles and stores execution sequences;
- commits resolution;
- submits the observation to the scheduler for contextualization;
- commits or fails the final submission activity.

Because Runtime wraps resolution and contextualization in transactions, a failed
resolution does not leave the knowledge graph looking as if the observation had
been made. Runtime is the service that turns plans into durable twin state.

### Runtime And Components

Runtime contains built-in core functors for common k.LAB dataflow constructs:
URN resolution, expressions, lookup tables, constants, and adapter-backed
contextualization. Components can add more executable service implementations.

Before Resolver accepts a strategy or model, Runtime is asked to resolve its
contextualizables. Runtime first checks its own component registry. If a
service implementation, resource, adapter, or component is missing, Runtime
uses Resources through the current scope to find and load what it needs.

This keeps execution honest. The planner does not merely build a theoretically
valid dataflow; it builds one the scoped runtime says it can support.

### Runtime And Maintenance

Runtime periodically scans context information. Non-persistent orphan contexts
are removed. Idle contexts may be removed or reinitialized according to their
persistence policy. Contexts configured to close on service shutdown are closed
during runtime shutdown.

This is also where the distinction between scope lifetime and digital twin
lifetime matters. A context scope can disappear while persistent digital twin
state remains reconnectable.

## How The Services Interplay

The same observation can touch all four services:

```text
1. Client submits an observation in a ContextScope.
2. Runtime registers it and starts a transaction.
3. Runtime asks Resolver for a dataflow.
4. Resolver asks Reasoner which strategies match.
5. Resolver asks Resources which models and assets can support those strategies.
6. Resolver asks Runtime whether required contextualizers can run.
7. Runtime uses Resources to obtain missing components, resources, or adapters.
8. Resolver returns a dataflow.
9. Runtime compiles, schedules, executes, commits, and publishes messages.
```

The direction of ownership is just as important as the direction of verbs:

- Resources owns asset availability and rights.
- Reasoner owns semantic interpretation.
- Resolver owns the plan for a requested observation.
- Runtime owns digital twin state and execution.
- Scopes own the continuity of user identity and service visibility across all
  of the above.

## Practical Rules

- Use the scope's service catalog. A scoped service lookup is part of the
  security and topology model.
- Keep Runtime as the owner of digital twin state. Other services may hold peer
  contexts, but they should not pretend to own the twin.
- Let Reasoner answer semantic questions, not resource availability questions.
- Let Resources answer asset and component availability questions, not execution
  questions.
- Let Resolver plan, but make Runtime confirm that planned contextualizers can
  actually run.
- Treat ContextScope as mandatory for observation work. UserScope is enough for
  identity-level asset operations; observations need a context.
- Remember that service verbs can be local or remote without changing the
  architecture. The scope and service catalog hide that transport detail.
- Do not treat capabilities as mere documentation. They tell the caller which
  worldview, components, permissions, storage defaults, schemata, and semantic
  readiness are available under the requesting scope.

The invariant to keep in mind is simple: k.LAB observes through scopes. A
request without the right scope may have a token, a service URL, and a valid
payload, but it does not have the digital twin position, service graph,
identity, lifecycle, or messaging channel needed to become a real observation.
