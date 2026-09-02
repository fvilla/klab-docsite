# Resources service contract

This document defines the resource-management contract exposed by `ResourcesService`. Its public
asset API consists of `resolve`, `retrieve`, `delete`, `list`, and `submit`, plus the shared
`KlabService.info` and `KlabService.query` inspection operations. Asset-specific methods are
implementation helpers, not service API.

The other methods still declared by `ResourcesService` are operational facilities (for example,
resource contextualization, repository management, behavior parsing, and project locking). They
do not create an alternative asset CRUD surface.

## Terminology: asset versus `Resource`

In this document, **asset** is the generic word for any object implementing `KlabAsset`: projects,
namespaces, models, workflows, components, and the other managed knowledge objects are all assets.
`Resource` with an initial capital denotes only the concrete
`org.integratedmodelling.klab.api.knowledge.Resource` contract. A `Resource` describes an
adapter-backed dataset or computation, including its URN, version, geometry, parameters, metadata,
files, validation notifications, and history. “Resources service” is the proper name of the
service, not a claim that every asset it manages is a `Resource`.

The publication lifecycle in this document applies to that concrete `Resource` contract. It must
not be generalized to arbitrary assets without defining their own submission and review rules.

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
- `limit` or `maxResults`: cap a `ResourceInfo` catalog query to 1–100 results;
- `includePublishedLocal`: include retained local sources that have already been published; the
  default is `false` on a local Resources service;
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
- `CREATE_OR_UPDATE`: create an absent asset or save a newer version of an existing one;
- `PUBLISH`: submit a concrete `Resource` to a remote authoritative service for tier-1 review.

The current provider can ingest `Resource`, create `Workspace`, create `Project`, and replace/update
file-backed k.IM documents carrying both `projectName` and `sourceCode`. A new project asset must use
the `workspace/project` URN. `Resource` updates preserve the previous current representation in the
embedded history and require the submitted version to be newer. k.Actors document mutation,
project/workspace update, and merge semantics remain pending and return explicit notifications.

## Complete lifecycle of a concrete `Resource`

### 1. Local creation and tier 0

A new `Resource` is first created on a local Resources service. Its adapter contract, required
parameters, geometry, identity, version, metadata, and local-file integrity are validated before a
normal save is enabled. Creation establishes a `ResourceInfo` catalog record with owner-scoped
rights, `Stage.STAGING`, and review status 0 (tier 0).

The editor distinguishes two subsequent mutations:

- **Update temporary data** uses `REPLACE`. It keeps the same version and is accepted only by a
  local service or for a tier-0 record. It is intended for incomplete staging metadata and still
  requires a valid resource overview.
- **Save new version** uses `UPDATE`. Full validation must pass, the version must be newer than the
  current version, and the former current representation is appended to `Resource.history`.
  Historical versions do not appear as separate browser results.

Permissions do not live in the serialized `Resource`. `ResourceInfo.rights` is independently
persisted in `ResourcesKBox`, and the editor updates it through its dedicated permissions action.
Saving resource content does not implicitly save permission edits.

### 2. Publication eligibility in the editor

Publication is a separate tab, not a variant of local Save or Update. It is available only when all
of these conditions hold:

- the source service is local and the local `Resource` is no longer an unsaved draft;
- client-side validation has no errors;
- at least one available non-local Resources service grants `CRUDOperation.CREATE` to the current
  `UserScope`;
- the user explicitly selects and confirms the target, acknowledging that local editing becomes
  restricted.

Target discovery and submission run off the JavaFX application thread. The publication action is a
`WaitButton`, so a long adapter validation or remote ingest exposes waiting/success/failure state
without blocking the UI.

The caller is an editor when `WorkflowParticipant.from(UserScope)` contains `WorkflowRole.EDITOR`
(workflow administrators also qualify). Otherwise the publication tab requires an intended editor
identity and sends it as `klab.publication.intendedEditor` metadata. The remote endpoint rejects a
non-editor submission without that metadata even if a non-IDE client bypasses the UI.

### 3. Remote submit and review entry

The client submits the complete `Resource` to
`PUT /api/v1/submit/RESOURCE/PUBLISH/{urn}`. `PUBLISH` is invalid for any other knowledge class. The
target enforces CREATE permission and rejects the request when:

- the target is local;
- any version of the URN already exists;
- incoming validation notifications contain an error;
- mandatory adapter parameters are missing;
- the target adapter's local-import validator rejects the resource; or
- a non-editor submission has no intended editor metadata.

The adapter validator or metadata analysis may replace the catalog and namespace components. Once
that processing succeeds, the service replaces the first URN component with its own sanitized
service name and returns that final authoritative URN. A duplicate check is repeated against the
final URN, so analysis cannot accidentally overwrite an existing resource.

Successful ingest creates exactly one current resource keyed by that final URN. Its remote `ResourceInfo` is
set to `Stage.REVIEWING` and review status 1 (tier 1, “under review”). The configured
`publicationReviewWorkflow` defaults to `asset-review`. For an editor submission, the service tries
to start that workflow automatically in its `editing` state. A missing or unusable workflow does
not roll back the accepted resource; it is reported as a warning so review can be started manually.
Setting the configuration value to blank disables automatic workflow creation.

### 4. Recording authority on the local source

Only after remote acceptance does the client call the source service's `markPublished` API. The
source must itself be local, and only the resource owner or a service administrator may change the
record. The endpoint is `PUT /resourceInfo/{urn}/publication/{serviceId}` and its request
body carries the final `authoritativeResourceUrn`. The local `ResourceInfo` then stores:

- `published = true`;
- `authoritativeServiceId` equal to the accepting remote service ID; and
- `authoritativeResourceUrn` equal to the final URN returned after remote validation and analysis;
- `publicationTimestamp` for the successful handoff.

This is a cross-service two-step operation, not a distributed transaction. If the remote accepts
the resource but the local catalog update fails, the editor reports that exact partial outcome;
the remote copy is authoritative and the local record must be reconciled rather than submitting a
duplicate blindly.

### 5. Discovery and local read-only behavior

Normal local `ResourceInfo` search omits records whose local source has `published = true`.
`includePublishedLocal=true` opts into those records through the generic query API; the resource
browser exposes the same option as **Show published local resources**. The filter applies only to a
local service, so it never hides the authoritative remote record.

When an opted-in published local source is opened, its resource fields, Save, Update, and Delete
actions are read-only by default. **Edit published local copy** is shown beside the local action
buttons. Checking it opens an explicit warning that local changes do not update the authoritative
server; only confirmation enables editing. Permissions retain their independent authorization and
update action.

### 6. Re-publication and deletion

The authoritative service ID is retained even when that service is unavailable. Re-publication is
allowed when the recorded authority is unavailable. If it is available, only a user with
`CRUDOperation.ADMINISTER` may choose a different target, and the editor warns that normal
operations belong on the authoritative service.

The recorded authoritative service is not offered again while it still returns the recorded
`authoritativeResourceUrn`. It becomes
eligible only after that remote resource has been deleted. Independently of UI discovery, every
remote `PUBLISH` request rejects an existing URN, including a different version, so concurrent or
stale clients cannot turn publication into an update.

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
- implement project/workspace update and `MERGE` submission;
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
