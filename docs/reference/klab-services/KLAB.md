# k.LAB: executable semantics for a knowledge commons

Ferdinando Villa, BC3

*Technical note, revised 2026-08-26*

> This document is a stand-alone introduction to the purpose and architecture of k.LAB. It explains the ideas behind the platform and their expression in the current service stack; it is not a user manual or an API reference. The documents linked throughout provide implementation-level detail.

## Introduction

k.LAB is an open-source platform for turning a request for knowledge into a contextualized, traceable observation. It is designed for integrated modelling: the practice of connecting scientific data, models, algorithms and services while preserving what each artifact means, where it is valid, how it was used and who is responsible for it.

The central interaction is deliberately different from asking for a file or calling a known model endpoint:

```text
observe <concept> in <context>
```

The concept placeholder is expressed in practice through an [observable
expression](OBSERVABLES.md): k.LAB's compositional query language for *what*
should be observed. The context states where, when, at what scale, under which
scenario and from whose perspective. k.LAB discovers candidate knowledge,
reasons about semantic compatibility, assembles a computational plan called a
**dataflow**, executes it and records the resulting **observation** in a digital
twin. The observation remains linked to its semantics, computation, provenance
and context.

This changes the unit of interoperability. Files, APIs and database records remain necessary, but they are not the final contract. The contract is the meaning of an observation in context.

### From the Semantic Web to an executable semantic commons

The conventional Semantic Web made a foundational contribution: resources can have stable identifiers, formal machine-readable descriptions and links that cross organizational boundaries. In its common implementation, however, the center of gravity remains the publication and query of data, metadata or graph statements. Most scientific and policy questions need more than retrieval. They require situated computation across data, models, transformations, scales, assumptions and access regimes.

k.LAB extends the Semantic Web idea from *describing resources* to *producing observations*. Semantics is executable: it constrains which resources can answer a request, which mediations are valid, which dependencies must be resolved and how the result should be interpreted. A semantic query may therefore be answered by a dataset, a model, a chain of models, an already existing observation, or a composition not explicitly anticipated by any one provider.

This is the technical basis for a **semantic knowledge commons**: a shared, distributed and governed space in which scientific artifacts can be found and combined by meaning. It is a commons rather than merely a catalogue because its value depends on continuing stewardship, shared semantic rules, contribution processes, attribution, review and safeguards against capture. Open access alone does not create a commons, and a centralized platform controlled by one provider does not become one merely by publishing metadata.

The distinction can be summarized as follows:

| Concern | Conventional data or Semantic Web | Semantic knowledge commons |
| --- | --- | --- |
| Primary unit | Dataset, document, endpoint or graph statement | Observation in a stated context |
| Discovery | Identifier, metadata, keyword or graph pattern | Observable meaning, context, scale and constraints |
| Integration | Predefined links and application-specific pipelines | Reasoned mediation and on-demand dataflow assembly |
| Output | Retrieved object or query result | Semantically typed observation with provenance and an executable plan |
| Evolution | Republish or update linked resources | Re-resolve as knowledge, context and availability change |
| Governance | Usually repository- or provider-specific | Shared semantic stewardship plus provider sovereignty |

The commons is compatible with the FAIR principles, but pushes their operational meaning further. Findability becomes discovery by meaning; accessibility includes machine-actionable rights and conditions; interoperability is enforced through formal observational semantics; and reuse carries provenance, scale, uncertainty and applicability. k.LAB also adds **reactivity**: observations may persist, receive events and participate in living digital twins rather than ending as static outputs.

### Why a commons is needed

Science produces an abundance of observations, datasets, models and services, yet decision-grade knowledge remains scarce. Integration across disciplines and institutions is still largely bespoke. Terms differ, implicit assumptions conflict, scale and context are lost, and provenance is often separated from the output it should qualify. These failures are semantic and institutional as much as technical.

A functioning commons addresses both sides:

- providers retain custody, licensing choices, attribution and operational control over their resources;
- users ask for knowledge in terms of meaning rather than infrastructure location;
- model and data contributions become reusable outside the workflow that created them;
- competing explanations can coexist and be selected transparently for a context;
- provenance makes results reviewable, reproducible and contestable;
- shared maintenance and validation allow the value of contributions to compound.

This model does not require every asset to be free or public. Protected resources can participate when their access conditions are explicit and enforced. Nor does it remove the role of commercial services. It shifts value away from enclosing meaning and interfaces, leaving room for paid compute, latency, hosting, validation, support, training and specialized expertise.

### A worldview that is shared, not imposed

Semantic interoperability needs a common logical basis. k.LAB calls this basis a **worldview**: a coordinated set of ontologies, observation concepts and inference rules that acts as the grammar for expressing what can be observed. The worldview is not intended as a universal list of terms or a monolithic ontology. It provides a compact observational language in which concepts can be composed, checked and related to external vocabularies.

The current worldview grew through more than a decade of work in k.LAB and ARIES. It is useful scaffolding, not a finished authority. Broad legitimacy requires a community process in which the people who understand a domain can own its meanings while maintainers protect logical coherence across domains.

A practical governance model should resemble a mature open-source project:

- **stewards** are accountable for coherence, governance and releases;
- **domain editors** maintain defined namespaces and their scientific boundaries;
- **maintainers** operate validation, documentation and release tooling;
- **moderators** keep participation constructive and accessible;
- **contributors** propose definitions, examples, mappings, models and semantic tests;
- **observers** can follow the work without a commitment to contribute.

Concepts should move through an explicit lifecycle: draft, review candidate, stable, deprecated and eventually removed after a migration period. Proposals need definitions, scope boundaries, examples and counterexamples, operational motivation, traceable discussion and tests. Because the worldview drives computation, a concept must not only sound plausible; it must behave consistently and avoid breaking existing resolutions.

This process should be open to more than ontology specialists. Domain experts can identify distinctions and counterexamples; users can report ambiguous outputs; modelers can provide validity constraints; communities can map local, indigenous, regulatory or disciplinary knowledge systems; and engineers can maintain validation and migration tools. Existing ontologies and classifications remain valuable. k.LAB **authorities** connect their identifiers to the observational semantics needed at runtime without importing every external vocabulary into one reasoning graph.

Generative AI can assist with search, drafting, comparison, documentation and discussion summaries. It should not decide semantic truth. Formal validation, tests, provenance and accountable human governance remain the basis for adoption.

### Digital twins as living, composable knowledge

A decision-grade digital twin is more than a dashboard, data lake or static model. It represents a real or hypothesized system through time, incorporates observations from the world, supports prediction and counterfactual scenarios, and maintains a defensible relationship between evidence, computation and decisions.

For complex Earth and social systems, semantic mistakes are often more dangerous than format errors. Two services may exchange valid arrays while silently disagreeing about precipitation, exposure, population, price basis or spatial support. A technically successful workflow can therefore remain scientifically invalid.

k.LAB makes semantics part of both the external request and the internal state. A digital twin contains semantically typed observations in a knowledge graph, together with storage, provenance and the activities that created or changed them. Behaviors can make observations reactive to time, messages, state changes and other observations. The twin can be ephemeral, persistent for a session or maintained according to a longer-lived policy.

Large twins should be built compositionally. The useful unit is a bounded twin whose semantics, models, data, uncertainty and operational behavior can be owned and validated by a responsible community. Watershed, city, biodiversity, infrastructure, public-health or economic twins can then participate in larger systems without being collapsed into one model monolith. Composition remains trustworthy only when every component exposes:

- a semantic contract for its observations and validity boundaries;
- a semantic query interface rather than only fixed endpoint calls;
- discoverable resources and capabilities;
- provenance and, where available, uncertainty;
- explicit access, lifecycle and governance policies.

This is the perspective behind an **internet of observations**: independently operated digital twins and knowledge services that can discover, explain and reuse one another through shared semantics.

## Architecture

k.LAB separates three logical layers and instruments them through four main service types. The logical layers explain *what kind of interoperability is provided*; the services define *which process owns each responsibility*.

### Three logical layers

1. The **resource layer** makes heterogeneous data, models, algorithms, services, projects and software components addressable through uniform contracts and resolvable URNs. Resources retain their native representation and do not acquire one mandatory meaning at this layer.
2. The **semantic layer** uses the worldview ontology language (`.kwv`) to define shared concepts, the observable expression language to formulate semantic queries, and k.IM (`.kim`) to annotate resources and publish observation strategies.
3. The **reactivity layer** hosts observations in digital twins and uses k.Actors (`.kactor`) to let observations, users, sessions and twins react to events.

Keeping these layers distinct is essential. The same dataset can be interpreted through more than one worldview or used to observe more than one concept. A semantic model can change without moving the source data. A digital twin is itself a semantic artifact that can be re-resolved when better knowledge becomes available without redefining its role in a cooperating network.

### Languages of the semantic commons

The semantic commons is instrumented through three languages, all sharing one common
_observable_ syntax to express meaning. Assets written in these languages are assembled into versioned projects, hosted and indexed by Resources services. The latter make them available as semantic assets to their intended communities, forming the k.LAB semantic web.

| Language | Layer and purpose |
| --- | --- |
| [Observable expressions](OBSERVABLES.md) | Shared semantic query and asset-description syntax. inherited by all three languages |
| [Worldview ontology language](ONTOLOGY_LANGUAGE.md) (`.kwv`) | Defines the concepts and relationships that delimit the boundaries of interoperability; distributed, synchronized and maintained by a worldview community |
| [k.IM](KIM.md) (`.kim`) | Publishes context-explicit models, including resource annotations, algorithms with dependencies, and semantic bridges to external services and models |
| [k.Actors](AGENTS.md) (`.kactor`) | Gives observations, digital twins, users, and sessions reactive behavior, enabling agent-based models, interactive applications and monitoring systems |

Observable expressions are used directly to specialized concepts in `.kwv` definitions and in `.kim`
models to annotate resources and outputs, and to specify dependencies. In value positions, such as in function parameters or metadata, they are written as `{{ ... }}` semantic literals;
k.Actors uses only this literal form. Together the languages separate shared
meaning, ways of producing observations, and behavior after observations enter
a digital twin.

The resulting division is deliberate: `.kwv` establishes communal meaning, `.kim` connects that meaning to context-, observer- and scale-scoped ways of observing, and `.kactor` governs behavior after observations become live state.

### Four operational services

The pre-1.0 architecture grouped responsibilities into nodes and engines. The current implementation replaces that topology with explicit, independently deployable services:

| Service | Owns | Principal responsibility |
| --- | --- | --- |
| **Resources** | Assets and their availability | Workspaces, projects, worldview, k.IM and k.Actors documents, resources, components, adapters, rights, versions and transport |
| **Reasoner** | Semantic truth | The worldview, OWL-backed inference, concept and observable interpretation, semantic relationships and observation strategies |
| **Resolver** | Plans | Context-sensitive resolution graphs, candidate ranking, coverage and compilation of a dataflow |
| **Runtime** | Live state and execution | Sessions, contexts, digital twins, knowledge graphs, transactions, storage, provenance, scheduling and contextualization |

The distinction can be remembered as:

```text
Resources -> what usable knowledge exists
Reasoner  -> what the request and available knowledge mean
Resolver  -> what plan can satisfy the request in this context
Runtime   -> what exists in the twin and what actually runs
```

The **Engine** sits above the four-service stack as a user-side orchestrator. It authenticates the user, starts or discovers services, constructs the service catalogue and creates the initial user scope. It is not the owner of the distributed knowledge or of a remote runtime's twin.

Database, language-server and messaging-broker processes support the stack. Authentication and community coordination are provided by network infrastructure outside the four core service APIs. A dedicated **Discovery** service type is already part of the service model, but global capability discovery and network-wide refactoring are roadmap work; they must not be confused with the configured or certificate-mediated service selection available today.

### Scopes make several services one workflow

A distributed workflow must preserve identity and context across process boundaries. k.LAB does this with **scopes**:

- a `UserScope` carries identity and the authorized service catalogue;
- a `SessionScope` binds a user workflow to one host runtime;
- a `ContextScope` identifies a digital twin or a focused position within it;
- service-side peer scopes reconstruct the same logical workflow inside each participating service.

Services are normally obtained from the active scope, not from a global singleton. This makes a request mean “use the Resources service authorized for this user and workflow,” and permits local and remote services to participate through the same contract. Only the host Runtime owns the digital twin; peer contexts in Resources, Reasoner and Resolver are scoped lenses pointing back to that runtime.

Scopes carry lifecycle, service identity, permissions, messages, focus observations and transaction information. They are therefore not optional request metadata. They are the continuity mechanism that keeps a multi-service resolution coherent.

### From a request to an observation

The normal lifecycle is:

```text
semantic request in a ContextScope
  -> Runtime registers an unresolved observation and opens transactions
  -> Resolver builds a resolution graph
  -> Reasoner supplies context-appropriate observation strategies
  -> Resources supplies candidate models, resources and dependencies
  -> Runtime confirms that required contextualizers can execute
  -> Resolver compiles the successful graph into a dataflow
  -> Runtime compiles, schedules and executes the dataflow
  -> Runtime commits observations, storage and provenance to the digital twin
```

The service boundary is intentional. Reasoner determines what is semantically admissible, but does not choose or execute resources. Resolver plans, but does not own state. Runtime controls registration, transactionality, execution and cleanup. Resources controls the assets and rights needed by the other services.

If no valid strategy covers the request, resolution fails with notifications rather than fabricating a result. If execution fails, Runtime uses transaction and storage cleanup paths to avoid treating partial state as a completed observation. Successful outputs remain queryable in the twin together with their provenance.

## The resource layer

The Resources service manages all assets that may participate in k.LAB, including:

- workspaces, projects, ontologies, namespaces and semantic models;
- observation strategy documents;
- k.Actors behaviors, applications, scripts and tests;
- datasets, external services and computations exposed as resources;
- components that contribute adapters, functions, importers and exporters;
- metadata, ownership, versions, review state and access rights.

A resource is identified by a URN and accessed through an adapter. An adapter defines how to validate, import, contextualize, encode or export a particular resource type. The underlying asset may be copied into managed storage, left at its authoritative source, generated by an algorithm or obtained from an external service. Uniform resource contracts make those differences manageable without pretending they are semantically equivalent.

Resources and semantics remain orthogonal. A file or service can be annotated by several models and interpreted differently under distinct use cases. Conversely, a semantic observable can be resolved through different resources as availability, permissions, context or ranking changes.

Resources operations are identity-aware. Resolution returns the asset and dependencies needed to operationalize it; retrieval returns the managed asset itself; submission, publication, update and deletion obey scope-specific privileges. A model that depends on an inaccessible resource is not a viable strategy for that user, even if it is visible to another participant.

Institutional deployment follows naturally from this design. A data agency can operate a Resources service near authoritative databases; a research institute can publish reviewed model projects and components; a community organization can curate local observations under suitable access policies. Participation does not require surrendering custody to a central repository.

## The semantic layer

### Observables and observations

An **observable** is a logical description of what may be observed. An **observation** is its contextualized realization in a digital twin. This distinction separates meaning from any one implementation.

For example, a request for the probability of flood exposure in a watershed during a period does not identify a raster, model or service. It identifies an observational intent. The available context, worldview and resolution constraints determine which resources can contribute, whether their scales and meanings are compatible and what mediation is required.

The [worldview ontology language](ONTOLOGY_LANGUAGE.md) defines concepts and
their formal relationships. The shared [observable expression
language](OBSERVABLES.md) composes those concepts into queries through
subjects, qualities, processes, events, relationships, predicates and semantic
operators. [k.IM](KIM.md) then uses the same expressions to state model outputs
and dependencies and to annotate datasets, algorithms and services. The
logical model is compatible with OWL 2, while the languages are designed for
scientific modelling rather than direct manipulation of triples. See also
[Semantic Modeling](SEMANTIC_MODELING.md) and [ODO-IM](ODO_IM.md).

### Reasoning, strategies and mediation

The Reasoner loads the worldview from an authorized Resources service and maintains the inferred semantic model. It resolves concept and observable expressions, checks relationships and produces observation strategies that may apply to a request.

An observation strategy explains, at a semantic level, how a kind of observable can be approached. The Resolver contextualizes these strategies against geometry, scale, scenario, observer, current twin state and other constraints. It then combines them with models and resources, tracks coverage and builds a resolution graph.

Semantic mediation is more than unit conversion or field renaming. It may involve recontextualization, aggregation or disaggregation, classification, inference of related observables, introduction of required dependencies or adaptation between spatial and temporal representations. Every mediation must remain visible in the dataflow and provenance.

Resolution is designed to admit plural knowledge. Several models may legitimately observe the same concept under different assumptions, scales or communities of practice. Ranking and constraints choose among compatible candidates for a request; scenarios and explicit choices can preserve alternative hypotheses. Future discovery can improve the candidate pool and ranking signals, but semantic validity cannot be delegated to popularity or opaque machine learning.

### Provenance and trust

An observation is inseparable from the activity that produced it. Runtime transactions record plans, agents, inputs, outputs and derivations in the digital twin's knowledge graph. This supports reproducibility, attribution and review, but also a more important property: contestability. A decision maker should be able to see which knowledge was selected, which alternatives were excluded, which mediations occurred and where uncertainty or failure entered the workflow.

Digitally signed or institutionally endorsed outputs can build on this record, but endorsement is a governance decision, not an automatic consequence of computation. Provenance makes that decision auditable; it does not replace scientific review.

## The reactivity layer and digital twins

The Runtime service hosts digital twins. A twin is represented by a context scope backed by a knowledge graph, storage, a scheduler and lifecycle policy. It may contain observations of entities, qualities, processes, events and relationships, along with the provenance and activities that connect them.

[k.Actors](AGENTS.md) defines executable behaviors for observations and other
runtime agents. Behaviors can initialize state, respond to messages, emit
events, schedule work and call semantic observation services using
`{{ ... }}` observable literals. They can instrument observations, users and
sessions; implement agent-based models; automate workflows; expose interactive
applications; and provide test cases that exercise the system lifecycle.

Reactivity changes the temporal character of scientific integration. A contextualization no longer has to be a one-off pipeline. An observation can remain alive, receive new evidence, react to a threshold, interact with another agent or be re-observed under a scenario. Persistent and network-addressable twins can therefore act as decision systems rather than static reports.

This capability should be used with bounded responsibility. A large “twin of everything” is neither verifiable nor governable. A practical network will contain many twins with explicit thematic, geographic, institutional and temporal boundaries. Larger views emerge through semantic composition and scoped access, not by merging every internal state into one database.

## A realistic federated k.LAB network

The expected k.LAB network is not one global installation and not a peer-to-peer free-for-all. It is a federation of authenticated services operated by institutions with different mandates, capacities and access policies.

A plausible deployment includes:

- universities and research centers hosting Resources services for models, projects and research data, plus Runtime services for experiments and teaching;
- statistical, environmental and mapping agencies hosting Resources services close to authoritative data and elastic Runtime pools for official analyses;
- international organizations operating shared worldview, Reasoner and Resolver capacity, public applications and durable twins for cross-border programs;
- local governments, NGOs and community organizations contributing contextual knowledge and operating smaller twins with controlled visibility;
- commercial providers offering protected resources, specialized compute, validated components or managed Runtime capacity without controlling the common semantic interface.

An institution may run several instances of the same service. A national provider may shard resources by domain or policy; a compute center may operate a pool of Runtime services with different hardware and persistence profiles; several Reasoners may serve distinct but compatible worldviews; Resolver instances may be placed near users or runtimes. Replication and specialization avoid a single technical, geopolitical or commercial point of failure.

The topology can be pictured as:

```text
                         authentication and community governance
                                        |
                           discovery and capability indexes
                              (partly future work)
                                        |
          +-----------------------------+-----------------------------+
          |                             |                             |
  Institution A                 Institution B                 Institution C
  resource services             resource services             protected resources
  reasoner/resolver             runtime pool                  specialist components
  persistent twins              public applications           bounded digital twins
          |                             |                             |
          +------------- scoped, authorized service calls ------------+
                                        |
                       observations + dataflows + provenance
```

Today, Engines build service catalogues from configured and authenticated services, and services advertise status and capabilities. Scopes propagate the authorized catalogue through the workflow. The next discovery layer must generalize this into searchable, continuously updated indexes of services, worldviews, resources, semantic capabilities, runtime properties, trust and availability.

Enhanced discovery should answer more than “where is a service?” It should support questions such as:

- which Resources services can contribute knowledge about this observable under this worldview;
- which Runtime can execute the required components at the requested scale and persistence level;
- which providers and assets satisfy the user's rights, trust and jurisdiction constraints;
- which compatible service remains available when one provider is offline;
- which newer resource or model should trigger reconsideration of an existing plan;
- which twin can supply an already maintained observation instead of recomputing it.

This requires capability metadata, health and operational state, identity-aware filtering, semantic indexing, version negotiation, caching and explicit failure behavior. Global discovery must not silently erase user choice or provider policy. It should return explainable candidates to scoped resolution, not establish an unaccountable central ranking authority.

In this topology, data sovereignty and interoperability reinforce one another. Assets can remain under authoritative custody, runtimes can be placed where data or compute policy requires, and a user can still obtain a coherent result because semantics, plans and provenance cross service boundaries under a shared contract.

## Access, extension and integration

Users may reach k.LAB through modelling tools, applications, command-line clients or service APIs. The Engine establishes the authenticated scope and service catalogue; applications then submit observation requests without needing to hard-code the location of every model and dataset.

Providers contribute at several levels:

- publish or connect a resource through an existing adapter;
- define or review concepts in a `.kwv` worldview ontology;
- annotate a resource and publish observation strategies in `.kim`;
- use observable expressions to make assets discoverable by meaning;
- write a `.kactor` behavior, application, script or test;
- contribute a component containing adapters, runtime functions, authorities, importers or exporters;
- operate one or more services for a community or institution.

Existing models can be integrated incrementally. A model may first consume k.LAB observations through an API; it may be exposed as a coarse resource with semantically defined inputs and outputs; or its internal workflow may be decomposed into reusable semantic model components. Deeper integration takes more work but allows the network to replace inputs, reuse intermediate observations, expose feedbacks and adapt the computation to new contexts.

The preferred extension boundary is explicit and inspectable. Components should declare the services, adapters and functions they contribute. Remote computations should expose portable contracts. Semantic annotations should state applicability rather than relying on undocumented conventions in the wrapped model.

## This repository

`klab-services` is the Java 21 reference implementation of the current service architecture. The main modules are:

- `klab.core.api`: portable contracts and data structures shared by clients and services;
- `klab.core.common`: common implementations used across the stack;
- `klab.core.services`: service bases, clients, scopes and shared infrastructure;
- `klab.services.resources` and `klab.services.resources.server`: resource management and its server;
- `klab.services.reasoner` and `klab.services.reasoner.server`: semantic reasoning and its server;
- `klab.services.resolver` and `klab.services.resolver.server`: observation planning and its server;
- `klab.services.runtime` and `klab.services.runtime.server`: digital-twin state and execution;
- `klab.modeler`: modeler-side orchestration and client functionality;
- `klab.cli`: command-line access;
- `klab.distribution`: distribution and service-stack management;
- `support`: graph database, language server and messaging support.

The repository is under active development. The four core service contracts and their local/server implementations exist, along with scope propagation, resolution, runtime knowledge graphs, components, messaging and language support. Some features remain incomplete or transitional, including global discovery, portions of external dataflow transport and execution, and migration away from pre-1.0 node terminology. Documentation should therefore distinguish implemented contracts from planned network behavior.

For implementation details, start with:

- [Architecture](ARCHITECTURE.md) for service ownership and the observation lifecycle;
- [Observable expressions](OBSERVABLES.md), [worldview ontologies](ONTOLOGY_LANGUAGE.md), [k.IM](KIM.md) and [k.Actors](AGENTS.md) for the user-facing languages;
- [Scopes](SCOPES.md) for identity, service propagation and context lifetime;
- [Resources](RESOURCES.md) for asset operations and service contracts;
- [Resolution](RESOLUTION.md) for resolution graphs, dataflow compilation and known limitations;
- [Storage](STORAGE.md) and [Provenance](PROVENANCE.md) for runtime state;
- [Agent compiler](AGENT_COMPILER.md) for k.Actors execution;
- [Components](COMPONENTS.md) for extension and distribution.

## Outlook

k.LAB's long-term proposition is not that one platform should contain all knowledge. It is that independent institutions can operate a shared semantic space while retaining custody, responsibility and the freedom to specialize. Resources become more valuable when they can participate in unanticipated observations; models become more valuable when their assumptions and domains of validity are explicit; digital twins become more trustworthy when they are bounded, composable and provenance-rich.

Technology is only part of that outcome. The service stack can enforce identities, contracts, transactions and semantic checks. It cannot by itself create fair governance, sustained curation, scientific legitimacy or equitable participation. Those require institutions and a community-owned worldview whose processes are as open and testable as the software.

The near-term engineering path is correspondingly concrete: complete and harden the four-service stack; make capabilities and operational state reliable; broaden resource, component and runtime deployment across institutions; implement semantic and policy-aware discovery; and use real cross-institution resolutions and composable twins to test both the technology and its governance. Success is a network in which users can ask for an observation, understand how it was produced, contest its assumptions and reuse its parts - without first knowing where every dataset, model and computer lives.

## References and related reading

- [FAIR Guiding Principles](https://www.go-fair.org/fair-principles/)
- [W3C Semantic Web standards](https://www.w3.org/2001/sw/wiki/Main_Page)
- [The Knowledge Commons Framework](https://doi.org/10.1017/9781316544587.002)
- [European Open Science Cloud](https://eosc.eu/eosc-about)
- [Destination Earth](https://digital-strategy.ec.europa.eu/en/policies/destination-earth)
- [Destination Earth platform](https://destination-earth.eu/)
- [k.LAB and ARIES](https://integratedmodelling.org/)
