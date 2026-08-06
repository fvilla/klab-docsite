# Resources service contract

This document defines the resource-management contract exposed by `ResourcesService`. Its public
asset API consists of `resolve`, `retrieve`, `delete`, `list`, and `submit`, plus the shared
`KlabService.info` and `KlabService.query` inspection operations. Asset-specific methods are
implementation helpers, not service API.

The other methods still declared by `ResourcesService` are operational facilities (for example,
resource contextualization, repository management, behavior parsing, and project locking). They
do not create an alternative asset CRUD surface.

## Core concepts

Every managed object is a `KlabAsset`, identified by a URN and classified by
`KlabAsset.KnowledgeClass`. The class is part of the request: identical text can name different
kinds of asset, and implementations must not guess when the caller can state the class.

Workspace-managed documents normally use their language URN. A project is addressed by its project
name for retrieval and deletion. Submission of a new project uses `workspace/project`, because the
target workspace is otherwise ambiguous. A workspace is addressed by its workspace name.

Except for public discovery, calls carry a `UserScope`. The scope is the authority for visibility,
ownership, and mutation. Passing `null` is valid only for public assets, notably worldview discovery
during service startup. Full privilege enforcement is not implemented in every provider branch yet;
those branches are explicitly listed under "Work remaining".

`ResourceSet` is the resolution and change-set envelope. A resolution result contains descriptors
for the requested asset and the dependency closure needed to use it, plus service locations and
notifications. A mutation returns one `ResourceSet` for each affected workspace. An empty result is
represented by `ResourceSet.isEmpty()` and may carry explanatory notifications; callers must not
interpret an empty Java collection and an error-bearing empty `ResourceSet` as equivalent.

## The resource operations

| Method | HTTP endpoint | Contract |
| --- | --- | --- |
| `resolve(urn, knowledgeClass, scope)` | `GET /api/v1/resolve/{knowledgeClass}/{urn}` | Locate an asset and return a self-contained `ResourceSet`, including required dependencies. This is discovery, not object transfer. |
| `retrieve(urn, assetClass, scope)` | `GET /api/v1/retrieve/{knowledgeClass}/{urn}` | Return the full serialized asset of the requested Java class, or `null` when it is not found or visible. Call `resolve` first when dependency loading matters. |
| `delete(urn, knowledgeClass, scope)` | `DELETE /api/v1/delete/{knowledgeClass}/{urn}` | Remove the asset and return change sets for all affected workspaces. Deletion is idempotent only where the underlying storage operation is idempotent. |
| `list(assetClass, scope)` | `GET /api/v1/list/{knowledgeClass}` | Return all visible assets of exactly the requested class. No filtering or descriptor conversion is implied. |
| `info(urn, knowledgeClass, infoClass, scope)` | `GET /api/v1/info/{knowledgeClass}/{urn}?infoClass=...` | Shared `KlabService` operation returning a projection or descriptor. Resources owns projections for its managed asset types and delegates common service/component projections to `BaseService`. |
| `submit(asset, mode, scope)` | `PUT /api/v1/submit/{knowledgeClass}/{submissionMode}/{urn}` | Add or change a typed asset and return workspace change sets. The body is the asset; the path class and URN must agree with it. |
| `query(parameters, knowledgeClass, infoClass, scope)` | `POST /api/v1/query/{knowledgeClass}?infoClass=...` | Shared `KlabService` operation selecting objects and returning one requested projection per match. For resource-managed types, an empty map is equivalent to listing the class followed by projection. |

HTTP knowledge-class and submission-mode values are enum names. `infoClass` is the canonical Java
class name and is required by `info` and `query`. Invalid classes, incompatible projections, and
unsupported query keys are request errors; they must not silently broaden a query.

### Resolve versus retrieve

`resolve` answers "what must be available to use this asset?" Its result contains lightweight
descriptors and dependencies and can be merged across services. `retrieve` answers "give me the
asset definition" and returns one concrete object from one service. A typical remote flow resolves,
loads the returned dependency set, and then retrieves concrete assets from the services named in
the result.

The provider currently resolves resources, namespaces, ontologies, behaviors, models, projects,
workspaces, worldviews, components, and service implementations. Special informational resolution
identifiers are:

- `export-schema:<media-type>` and `import-schema:<media-type>` with `INFORMATION`;
- an adapter identifier, optionally versioned, with `COMPONENT`;
- `<service-call-urn>@<version>` with `SERVICE_IMPLEMENTATION`.

Model resolution through `query` uses the typed convention
`{"observable": <Observable>}`, `KnowledgeClass.MODEL`, and `ResourceSet.class`. This preserves the
old semantic model-candidate operation while keeping it under the generic query API.

### Retrieve and list

`WorkspaceManager` is the source of full workspace-managed assets. It retrieves and lists
workspaces, projects, namespaces, ontologies, observation-strategy documents, behaviors, models,
and symbol definitions. The provider additionally retrieves resources, concepts, observables, and
the served worldview.

`list` has no search semantics. Clients that need matching, sorting, or a different representation
must use `query`. In a multi-service scope, `ResourcesMerger` snapshots all resource services,
excludes itself, queries them concurrently, tolerates an individual failure, and returns distinct
results in service order. `retrieve`, writes, and operational calls go to the primary service
because their results cannot be combined safely.

### Info

`info` and `query` belong to `KlabService`, so every service exposes the same transport and typed
projection contract. `BaseService` supplies common inspection of installed components, adapters,
service implementations, service capabilities/status, and portable `DomainObject` descriptors.
`ResourcesProvider` retains exclusive knowledge of resource-managed asset classes and delegates a
request to `BaseService` when the requested projection belongs to that common contract.

If `infoClass` is compatible with the asset itself, `info` is equivalent to `retrieve`. `String`
returns the matched URN, which lets query callers request identifiers without a separate
`listResourceUrns` endpoint. Current provider projections also include:

- `ResourceInfo` for catalog and authorization metadata;
- `ResourceTransport.Schema.LanguageDescriptor` for a language identifier with `INFORMATION`.

`AdapterDescriptor`, component descriptors, and service-implementation descriptors are supplied by
the common `BaseService` component-registry implementation and are therefore available from any
service that has loaded the corresponding component.

Additional `DomainObject` projections should describe a stable schema suitable for API discovery.
Unsupported projections fail explicitly. Model `Coverage` is reserved but not computed yet.

### Query

The parameter map belongs to the selected asset class. Current general parameters are:

- `urn`: a Java regular expression matched against the complete URN;
- `query`: an alias for the general textual/URN pattern;
- `observable`: the typed model-candidate query described above.

An empty map selects all visible assets of the class. If the requested `infoClass` is the asset
class, the result is equivalent to `list`. Otherwise each selected asset is transformed through
`info`. `ResourceInfo` queries use the resource catalog. Any unsupported key is rejected with a
`TO BE IMPLEMENTED` error rather than ignored.

### Submit

Submission modes are:

- `ADD`: create only; an existing asset is not overwritten;
- `REPLACE`: replace the current representation;
- `UPDATE`: update while retaining history when storage supports it;
- `MERGE`: merge submitted content into the existing asset.

The current provider can ingest `Resource`, create `Workspace`, create `Project`, and replace/update
file-backed k.IM documents carrying both `projectName` and `sourceCode`. A new project asset must use
the `workspace/project` URN. k.Actors document mutation, project/workspace update, version history,
and merge semantics remain pending and return explicit notifications.

### Delete

Deletion is selected by knowledge class and delegates to the existing storage-specific helpers.
Document, project, workspace, and resource removal return workspace change sets. The remote client
currently cannot deserialize the response body of its generic HTTP DELETE helper, so it returns an
empty Java list after a successful request; this transport limitation must be fixed before remote
callers can react to deletion change sets.

## Migration from specialized methods

| Old operation | Generic operation |
| --- | --- |
| `resolveModel`, `resolveResource`, adapter/service/schema resolvers | `resolve(urn, knowledgeClass, scope)` |
| `resolveModels(observable, scope)` | `query(Map.of("observable", observable), MODEL, ResourceSet.class, scope)` and merge returned sets |
| `retrieveNamespace`, `retrieveOntology`, `retrieveBehavior`, `retrieveProject`, `retrieveWorkspace`, `retrieveResource` | `retrieve(urn, AssetClass.class, scope)` |
| `retrieveWorldview` | `list(Worldview.class, scope)` or `retrieve(advertisedUrn, Worldview.class, scope)` |
| `listWorkspaces`, `listProjects` | `list(Workspace.class, scope)`, `list(Project.class, scope)` |
| `listResourceUrns` | `query(Map.of(), RESOURCE, String.class, scope)` |
| `resourceInfo`, `retrieveAdapterInfo`, `modelGeometry` | `info(urn, knowledgeClass, Projection.class, scope)` |
| `queryResources` | `query(parameters, knowledgeClass, ResourceInfo.class, scope)` |
| create/update/register methods | construct the typed asset and call `submit(asset, mode, scope)` |
| specialized delete methods | `delete(urn, knowledgeClass, scope)` |

Specialized methods that still encapsulate useful storage logic remain concrete helpers inside
`ResourcesProvider`; they are not overrides and are not callable through `ResourcesService`.
Client implementations contain only generic CRUD calls. Legacy controller routes and constants
remain temporarily for server compatibility and should be removed after external clients migrate.

## Non-CRUD service operations

The interface retains operations whose contract is not asset CRUD: resource contextualization and
data production, parsing standalone documents from an arbitrary URL, repository operations,
importing through transport schemas, publishing observations, and project locking. These operate on execution,
transport, or transaction state and should not be forced into CRUD solely to reduce method count.

`parseAsset(URL, Class<T>, UserScope)` accepts exactly four standalone document contracts:
`KActorsBehavior`, `KimOntology`, `KimNamespace`, and `KimObservationStrategyDocument`. It parses
without registering the result in a workspace. Remote clients upload the URL contents together with
the requested document class, so file URLs do not need to be accessible from the service host.

## Work remaining

The following gaps are deliberate and must remain visible until supporting contracts exist:

- enforce privileges consistently in every resolve, retrieve, query, submit, and delete branch;
- implement model coverage for `info(..., MODEL, Coverage.class, ...)`;
- implement resource composition and caching for multi-URN retrieval;
- implement import-schema resolution and geometry-aware schema selection in the generic identifier;
- implement project/workspace update, version history, and `MERGE` submission;
- support k.Actors document mutation in `WorkspaceManager`;
- make workspace deletion atomic and report complete change sets;
- return DELETE response bodies from `ResourcesClient`;
- enrich the minimal common `DomainObject` projection with stable type-specific schemas;
- replace public startup calls with an explicit public-scope contract instead of relying on a null
  scope;
- migrate and then remove legacy resource controller mappings and `ServicesAPI` constants.

The sibling `klab-ide` audit covered its resource-service call sites as well. Its standalone
k.Actors parsing in `AgentView` and `BehaviorEditor` now calls
`parseAsset(url, KActorsBehavior.class, scope)`. Its workspace and resource views use the generic
`retrieve`, `query`, `info`, and typed `submit` operations. Calls from `KlabIDEController` into the
modeler's own create/update methods are not `ResourcesService` calls and remain valid; the modeler
implements those workflows through the generic service API where supporting payloads exist.
