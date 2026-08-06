# k.LAB IDE Architecture

## 1. Purpose and scope

`klab-ide` is a JavaFX desktop client built around the k.LAB modeler and service-client libraries.
It is primarily an orchestration and presentation layer: authoritative workspaces, resources,
semantics, observations, and runtime state live in k.LAB services or in local behavior files.

This document describes the current implementation, including incomplete paths. “Implemented”
means that the code has an end-to-end action path; it does not imply production maturity.

## 2. Bootstrap and application shell

`KlabIDEApplication` owns the JavaFX lifecycle. It:

1. applies the selected AtlantaFX theme;
2. loads `ide.fxml`;
3. installs `custom.css`;
4. creates the 1480 x 1060 primary scene;
5. delegates shutdown to `KlabIDEController`.

`ide.fxml` defines a fixed shell:

- a left navigation and service rail;
- a central `StackPane` containing `NotebookViewer` initially;
- a bottom `inspectorArea`, normally 300 pixels high;
- a bottom status bar;
- a right-side notification area attached on demand.

`KlabIDEController` is the composition root. During deferred initialization it creates
`ModelerImpl`, obtains service and runtime view controllers, registers itself with them, constructs
the persistent top-level views, boots the modeler, authenticates the user, and initializes the
software stack.

The controller also implements the `Modeler` facade and delegates most modeler operations to the
contained `ModelerImpl`. Consequently, UI components frequently call the controller for both
navigation and domain operations.

## 3. Primary UI composition

### 3.1 Top-level views

The `KlabIDEController.View` enum maps navigation buttons to long-lived view instances:

| View | Component | Primary asset |
| --- | --- | --- |
| Notebook | `NotebookViewer` | notebook cards and command results |
| Workspaces | `WorkspaceView` | `NavigableWorkspace` |
| Resources | `ResourcesView` | `Resource` |
| Digital Twins | `DigitalTwinView` | `IDEContextScope` |
| Applications | `AgentView` | local `NavigableKActorsBehavior` |
| Worldview | `OntologyView` | not implemented |

`selectView()` swaps the selected node into `mainArea`; view instances survive navigation. This
preserves their open tabs and local state.

### 3.2 Browsable pages

`BrowsablePage<T,A>` is the common outer shell for Workspaces, Resources, Digital Twins,
Applications, and Worldview.

- The first, disabled tab contains a menu icon.
- Clicking the icon opens a left-side `ModalPane`.
- The modal browser lists or creates assets.
- Each selected asset opens as a top-level tab.
- `assetEditorSelected()` and `assetEditorClosed()` let each view manage focus and cleanup.

The browser is rebuilt on each show/update. It is not a permanent side pane.

### 3.3 Editor pages

`EditorPage<A,T>` is the common inner editor shell:

- inner asset tabs occupy the left 70% of a horizontal split;
- a browsing tree occupies the right 30%;
- editor-specific top controls may sit above the tree;
- a `DigitalTwinControlPanel` can be inserted below the tree;
- single and double click are distinguished with a 350 ms `Timeline`.

`edit(T)` guarantees one inner tab per asset according to map-key equality. `disposeEditor()` is
called only on actual tab closure. This distinction is essential for Monaco/LSP sessions because
JavaFX can temporarily detach tab content without logically closing the document.

Every editor registers as a `DigitalTwinReactor` with the main controller and unregisters from
`close()`.

### 3.4 Notebook

`NotebookViewer` hosts a `Notebook` of collapsible cards and a `REPLTextField`. Fixed cards are
created lazily from `AssetViewComponent.Type`; command submissions create `CommandResult` cards.
The command line is backed by `ModelerCommandLine`, using the focal context scope when present and
the authenticated user otherwise.

### 3.5 Inspector

`InspectorView` is a reusable, dockable `BorderPane` with:

- a list of `InspectorItem` values;
- backward/forward navigation;
- removable breadcrumb chips;
- lazy item resolution;
- cached display nodes;
- docked and detached sizing modes.

Values are rendered through `Theme.getDisplayObject(value, Detail.CARD)`. The current mappings
cover semantics, activities, observations, and cohorts; unknown values fall back to a label.

The inspector is invoked from workspace, observation, activity, and relationship views. Its
history is independent of editor selection history.

## 4. Domain and service model

### 4.1 User scope and services

After boot, `KlabIDEController.user` is the authenticated `UserScope`. It is the discovery point for
available service clients:

- `ResourcesService` hosts workspaces, projects, documents, and resources;
- `RuntimeService` hosts sessions, digital twins, observations, and agents;
- `Resolver` supplies resolution and scope-specific submitted resources;
- the reasoner supports semantic knowledge and validation;
- the language server provides Monaco diagnostics and language features.

Views list services from the user scope and generally sort local services before remote ones.
Creation controls are filtered by service capabilities and permissions in some, but not all,
paths.

### 4.2 Modeler and view controllers

`ModelerImpl` mediates higher-level operations and dispatches service/runtime changes through
view-controller interfaces. `KlabIDEController` registers as both `ServicesView` and `RuntimeView`.
`WorkspaceView` separately registers as a `ResourcesNavigator`.

The application receives digital-twin changes from two sources:

1. modeler/view-controller callbacks handled by `KlabIDEController`;
2. direct digital-twin event consumption handled by `IDEContextScope`.

Both sources now converge on the same `IDEContextScope` serial queue. The controller resolves the
scope peer and never dispatches directly to viewers.

### 4.3 IDEContextScope

`IDEContextScope` wraps a `ClientContextScope` and implements the full `ContextScope` contract by
delegation. It adds UI state:

- registered `DigitalTwinViewer`s;
- an activity graph indexed by transient activity ID;
- schedule state;
- focal graph root and asset;
- successful commit/observation pairs;
- graph-depth preference.

The constructor subscribes to the client's digital-twin event stream and serializes processing on
a single-thread executor. Submission start, abort, and finish; context and observer changes;
activity start and finish; schedule changes; graph changes; and remote closure all pass through
this queue. Successful submission records the commit and focal observation before notification.
Out-of-order activity completion is accepted and parent/child edges are repaired when either side
arrives. Duplicate completion arriving through both input routes is coalesced briefly.

`DigitalTwinEventRouter` owns a thread-safe, idempotent viewer registry. It uses a stable snapshot
for each delivery and isolates a failing viewer from the remaining recipients.

`within()`, `withObserver()`, and `between()` retain the wrapper identity. Context and observer
changes notify viewers. `getContextPath()` walks parent context scopes while suppressing duplicate
observations.

The controller stores one wrapper per context ID in `contextMap`. `requireDigitalTwinPeer()` adapts
raw client scopes, registers optional viewers, and ensures identity stability at the UI layer.

### 4.4 Focal digital twin

`KlabIDEController.focalScope` is global application state. `setFocalScope()`:

- deselects the previous scope;
- broadcasts the new scope to all registered `DigitalTwinReactor`s;
- refreshes the status-bar selector;
- brings the selected digital twin into the `DigitalTwinView`.

The current top-level editor is tracked separately so the status-bar panel toggle affects the
selected `EditorPage`.

### 4.5 Asset, scope, and service interaction matrix

| Component | Asset identity | Scope behavior | Services used | Change input |
| --- | --- | --- | --- | --- |
| `WorkspaceView` | workspace URN and hosting service | user-level; independent of focal context | Resources | `ResourcesNavigator.workspaceModified()` |
| `WorkspaceEditor` | navigable workspace, project, document, statement | reacts to focal context through its optional control panel | Resources, language server, Runtime for dropped observations | workspace `ResourceSet` changes and LSP diagnostics |
| `ResourcesView` | resource URN and service ID | includes resolver-submitted resources from the focal context | Resources, Resolver | search completion; no persistent resource-change subscription |
| `ResourceEditor` | selected `Resource` | delegates scope relevance to its control panel | currently none after construction | none |
| `AgentView` | normalized local file path | coordinates debug target across behavior editors | Resources for parsing | local file selection and editor callbacks |
| `BehaviorEditor` | file path plus optional parsed behavior | stores the focal `IDEContextScope`; exposes context agents in its tree | Resources, local Runtime, language server | saves, diagnostics, agent polling/callbacks |
| `DigitalTwinView` | context ID | selecting a tab sets the global focal scope | Runtime | service context enumeration and controller focus changes |
| `DigitalTwinEditor` | one `IDEContextScope` | permanently dedicated to that scope | Runtime through scope, client knowledge graph | dedicated scope viewer notifications |
| `KnowledgeGraphView` | runtime root/focus asset IDs | dedicated viewer registered with the scope | client knowledge graph | submission/graph/schedule callbacks |
| `ObservationCard` | observation URN/ID | receives the editor's explicit scope | Runtime export through `ValueCard` | timeline and point-query actions |
| `InspectorView` | object equality plus cached node | renderer commonly uses the global focal scope | renderer-dependent | explicit inspect calls |
| `NotebookViewer` | card key or generated result key | command target is focal scope, otherwise user scope | modeler command line and card-specific services | commands and shell button actions |

## 5. Asset presentation

`Theme` centralizes labels, icons, semantic colors, and detail renderers. It classifies both
authoring assets and runtime assets. Repository state prefixes are added to navigable asset labels;
semantic types determine observation colors.

The detailed card layer includes:

- `ObservableCard`;
- `ActivityCard`;
- `ObservationCard`;
- `CohortCard`;
- `GeometryCard`;
- `MetadataCard`;
- `RelationshipCard`;
- `HistogramCard`;
- `ValueCard`.

`ObservationCard` composes geometry/relationships, central observation content, and metadata.
Spatially distributed two-dimensional qualities use `ValueCard`; other geometries and observation
types use explicit stubs.

`ValueCard` separates `MapImageProvider` and `PointValueProvider`. Runtime defaults execute
`exportAsset` asynchronously:

- `image/png` receives viewport and temporal parameters;
- `text/plain` receives timestamp plus normalized and, when derivable, geographic coordinates.

Generation counters prevent stale map or point responses from replacing a newer temporal state.
`GeometryCard` merges event and histogram timestamps, includes a pre-span initialization state, and
notifies `ValueCard` when the user selects a timeline position.

## 6. View and editor behavior

### 6.1 WorkspaceView and WorkspaceEditor

`WorkspaceView` discovers workspaces from all visible Resources services and creates workspaces on a
selected service. Opening a workspace retrieves it, wraps it in `NavigableWorkspace`, and creates a
`WorkspaceEditor`.

The editor:

- attempts to lock each project;
- renders the complete navigable asset tree;
- supplies project/document context menus;
- creates projects and documents through controller/modeler operations;
- exposes repository operations;
- opens `NavigableKlabDocument` source in `MonacoEditorView`;
- binds `LspDocumentSession` when the language server is available;
- maps source offsets to tree statements and tree selection back to source;
- saves documents through the hosting Resources service;
- merges `ResourceSet` changes into the tree;
- submits dragged assets to the focal/default context.

Document identity uses an in-memory URI derived from the document URN and language extension.
Closing an inner editor closes its LSP session; closing the workspace closes all sessions through
`EditorPage.close()`.

### 6.2 ResourcesView and ResourceEditor

`ResourcesView` combines:

- resources already submitted to the focal resolver scope;
- asynchronous text search across all Resources services.

It resolves a selected `ResourceInfo` back to the hosting Resources service or, for scope-specific
resources, the Resolver. `ResourceEditor` displays resource data, geometry, attributes, metadata,
provenance, adapter parameters, and operation controls.

Most `ResourceEditor` controls are currently static examples and do not bind to or persist the
actual `Resource`.

### 6.3 AgentView and BehaviorEditor

`AgentView` manages local `.kactor` / `.kactors` files, a 12-entry recent-file list in Java
preferences, open editors keyed by normalized path, and a shared current debug target.

`BehaviorEditor` deliberately separates raw source identity from parsed behavior state:

- the filename is always the editor asset;
- a parsed `NavigableKActorsBehavior` is optional derived state;
- invalid source stays editable;
- successful save replaces the parsed asset in place;
- failed parsing clears compilation state rather than retaining stale executable behavior.

The source editor uses a file URI and k.Actors language ID. If available, `LspDocumentSession`
provides live diagnostics. Save writes the local file, reparses through the Resources service, and
optionally recompiles.

Compilation and execution require a local Runtime service. The editor can request generated Java,
create/run/debug agents, manage console tabs, poll agent liveness, coordinate a debugger, and stop
agents. The publication dialog enumerates local workspaces/projects but the final publication
method is empty.

### 6.4 DigitalTwinView and DigitalTwinEditor

`DigitalTwinView` enumerates `ContextInfo` from all visible Runtime services. It creates contexts
through a service-specific user session and wraps them in `IDEContextScope`.

Selecting a digital-twin top-level tab makes its scope focal. `DigitalTwinEditor` owns:

- a `ClientKnowledgeGraph`;
- a `KnowledgeGraphView` as the root asset editor;
- a `KnowledgeGraphTree` as the browsing tree;
- `ObservationCard` tabs for observations;
- a scope-bound `DigitalTwinControlPanel`.

`KnowledgeGraphView` maintains graph root/focus history, layout controls, graph-depth selection,
filtering, and deferred/coalesced redraw. `KnowledgeGraphTree` rebuilds from `TreeModel` and
coalesces refresh requests.

### 6.5 DigitalTwinControlPanel

Each `EditorPage` constructs a control panel, but only the selected editor's panel is shown through
the status bar. The panel registers with its scope as a dedicated viewer.

Its status machine is:

- `IDLE`: show the selected activity/observation/observer/scenario view;
- `RECEIVING`: show the drag-and-drop target;
- `COMPUTING`: show progress and activities;
- `ERROR` and `INFO`: declared but not specifically rendered.

Observation and activity trees integrate with the inspector. Individual subject observations can
become context through `IDEContextScope.within()`.

## 7. Lifecycle and threading

JavaFX mutations are generally wrapped in `Platform.runLater`, but this is not systematic.

Important lifecycle rules:

- top-level views persist for the application lifetime;
- top-level browser tabs own `EditorPage`s;
- inner editor tabs own Monaco/LSP sessions and auxiliary consoles;
- `EditorPage.close()` disposes inner editors, closes its digital-twin panel, and unregisters the
  reactor;
- each dedicated digital-twin editor registers once with `IDEContextScope` and forwards relevant
  changes to its tree and graph; control panels register independently because they may be hosted
  by unrelated editors;
- temporary JavaFX scene detachment is not editor disposal.

Asynchronous work currently uses several mechanisms:

- JavaFX `Task` plus ad-hoc threads for resource search;
- `CompletableFuture` for observation submission and map exports;
- `Timeline` for click discrimination and agent polling;
- the per-scope single-thread executor for digital-twin messages and modeler callbacks.

Closing a scope rejects late events, drains viewer registrations, shuts down its executor, and
unregisters the digital twin. Other asynchronous features still lack a shared application executor
or uniform cancellation policy.

## 8. Notifications and status

The main controller receives `Notification`s, caches a bounded history, updates unread counts, and
can attach a right-side notification panel. Fatal or direct alerts use JavaFX dialogs.

Editor-specific diagnostics are handled separately:

- workspace source diagnostics come from LSP and resource changes;
- behavior diagnostics merge parser, compiler, and editor markers;
- observation/activity cards expose their own notification state.

These channels do not yet converge into one consistent diagnostic model.

## 9. Explicitly marked gaps

The source explicitly marks the following incomplete features:

| Area | Gap |
| --- | --- |
| Worldview | `OntologyView` has an empty browser and even reports the wrong view name. |
| Resource editor | Controls contain example values; operations and persistence are not wired. |
| Behavior publishing | Project selection is implemented; `publishBehavior()` is empty. |
| Behavior compilation | Compilation runs synchronously despite a FIXME requesting a serialized executor. |
| Concept search | The digital-twin concept button opens a placeholder. |
| DT idle/error UI | Submission abort now stops progress and enters the error state, but no explanatory error content is rendered. |
| Scenarios/observers | A resolved current observer is displayed; observer discovery and scenario population remain incomplete. |
| Workspace settings | Workspace and project settings actions are empty. |
| Repository workflow | Branch selection, confirmations, detach/untrack, and operation parameters are unfinished. |
| Workspace updates | `findOrAddFolder()` returns `null`; new nested assets may not be inserted. |
| Workspace diagnostics | Resource-change diagnostics are collected but not delivered to editors or ancestor icons. |
| Workspace dirty state | Dirty tabs are not visibly marked. |
| New-document activation | Automatically opening newly created documents is disabled because it previously hung the UI. |
| DT access control | The creation dialog displays access rights, but its editor dialog is a placeholder. |
| DT persistence UX | Idle-time/one-off close warnings and countdown behavior are absent. |
| Quality filesystem export | `DigitalTwinEditor.exportToFilesystem()` only logs the request. |
| Export UI | `ExportCard` is only a stub. |
| Service dashboard | `ServiceDashboard.createContent()` returns `null`. |
| Distribution management | Action arming, descriptions, switching, and some progress transitions are TODO. |
| Command rendering | Collections, semantic results, and resources often fall back to generic rendering. |
| Settings/property editing | Validation and some settings actions are incomplete. |

## 10. Weaknesses inferred from the implementation

These are not all labeled TODOs, but follow from the current control flow.

### 10.1 Event replay and richer state models

Live event routing is now centralized in `IDEContextScope`, and late graph-view creation replays the
stored schedule and focal graph state. Not all event-derived state has a durable client model:
scenario selection, the catalog of potential observers, detailed submission errors, and restored
activity history are still incomplete.

**Recommended direction:** define durable per-scope state for each of those domains so a viewer
opened after an event can reconstruct the same UI as one that was already attached.

### 10.2 Mutable delegate semantics

`IDEContextScope.within()`, `withObserver()`, and `between()` preserve wrapper identity, so chained
callers no longer bypass IDE event propagation. They still replace the internal delegate. Code
holding an earlier derived raw scope may therefore observe a different contextual path from code
using the wrapper.

**Recommended direction:** explicitly model context derivation within the wrapper instead of
silently replacing its delegate.

### 10.3 Event-consumer detachment

Scope closure now rejects new events, drains viewers, and shuts down the serial executor. The
client digital twin exposes event-consumer addition but no matching removal operation, so the IDE
must rely on closing the underlying client scope to release that listener.

**Recommended direction:** add an explicit removable subscription contract to the client digital
twin and retain its handle in `IDEContextScope`.

### 10.4 Inconsistent JavaFX thread confinement

Scope viewer notifications run on the scope executor. Graph, tree, panel, tab, and closure updates
now marshal to the JavaFX thread where necessary, while activity snapshots are prepared on the
serialized event thread. This remains a convention rather than an enforced type-level boundary.

**Recommended direction:** snapshot domain state off-thread and enforce one JavaFX dispatch boundary
before invoking UI viewers.

### 10.5 Global controller coupling

Most components access `KlabIDEController.instance()` for user, services, scope, navigation,
notifications, and operations. This hides dependencies, complicates unit testing, and makes it easy
for a card to use the global focal scope instead of the scope associated with its asset.

**Recommended direction:** inject a small workbench context and explicit scope/service providers
into views and cards.

### 10.6 Asset identity and tab focus

Some browser views call `requestFocus()` on an already-open editor instead of selecting its tab.
Inner editor maps use asset equality, which may change when service refreshes replace navigable
objects. Workspace updates replace nodes but do not consistently re-key open editors.

**Recommended direction:** key tabs by stable URN/context ID and centralize open/select/replace
logic.

### 10.7 Resource search concurrency

The Resources browser starts a new raw thread on every text change. It cancels the previous
`Task`, but the service call may not honor interruption; the comment describes debounce behavior
that is not implemented.

**Recommended direction:** use a scheduled debounce, a bounded executor, request generation IDs,
and deterministic ordering/deduplication across services.

### 10.8 Resource editor contract

`ResourceEditor` visually presents editable fields without binding them to the resource or offering
a reliable save/revert model. This can mislead users into thinking edits are durable.

**Recommended direction:** render read-only until a complete draft/validation/save contract exists,
then derive fields and operations from the resource adapter rather than hard-coded samples.

### 10.9 Error and confirmation behavior

`KlabIDEController.confirm()` always returns `false`, `log()` and `cleanWorkspace()` are empty, and
several service failures are either assumed impossible or reduced to generic notifications.

**Recommended direction:** implement controller contracts completely and adopt a consistent error
surface with retry/context information.

### 10.10 Naming and fallback quality

There are visible pre-alpha defects: `OntologyView.getName()` returns “Digital Twins”, the window
title contains a mis-decoded copyright character, service tooltips are placeholders, and
`Theme.getLabel()` / semantic-color fallback paths contain developer-only exception or label text.

**Recommended direction:** replace all developer fallbacks with stable “Unknown …” labels, add
exhaustive classification tests, and treat encoding/style checks as release gates.

### 10.11 Observation point-query contract

The map image contract is generic export and works through the runtime. Point lookup currently
assumes that the same asset supports a `text/plain` export with timestamp and coordinate
parameters. No dedicated typed result, no-data representation, units contract, or cancellation
endpoint exists.

**Recommended direction:** introduce a runtime point-query contract returning value, semantics,
unit, locator, timestamp, and no-data/error status. Keep the existing `PointValueProvider` as the UI
adapter.

### 10.12 Test coverage

The automated suite covers tree-model logic, observation timeline/map helpers, and the
digital-twin viewer registry's registration, removal, drain, and failure-isolation behavior. It
does not exercise application boot, controller navigation, workspace save/update, service failure
paths, full JavaFX rendering of routed events, LSP lifecycle in this checkout, or agent execution
UI.

**Recommended direction:** add headless JavaFX component tests, fake service contracts, event-route
tests for `IDEContextScope`, and a small boot/navigation smoke suite.

## 11. Suggested architectural priorities

1. Add durable replay models for scenarios, available observers, errors, and restored activities.
2. Complete stable tab identity and workspace update/diagnostic propagation.
3. Make Resource editing honestly read-only or implement a complete persisted editing contract.
4. Finish behavior publication and move compilation/search work to managed executors.
5. Complete Worldview, scenario, observer-discovery, and concept-search paths.
6. Replace placeholders and unsafe fallbacks, then establish UI smoke and service-failure tests.

These priorities preserve the existing successful structure—persistent top-level views,
`BrowsablePage`, `EditorPage`, explicit LSP sessions, and modular cards—while removing the main
sources of inconsistent behavior.
