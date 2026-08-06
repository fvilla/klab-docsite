# k.LAB Components

Components are the extension mechanism used by k.LAB services to add capabilities without
rebuilding the service that hosts them. A component is a PF4J plug-in that implements the k.LAB
component contract and is packaged as a `.kar` archive by the k.LAB Maven packaging goal. The
`.kar` is intended to be a stripped, dependency-free archive: it contains the component code and
metadata, while common k.LAB and service dependencies are supplied by the hosting service.

Once imported, a component is registered in the service's local component registry. The registry
loads the archive, scans it for k.LAB extension annotations, builds a descriptor, publishes the
new capabilities through the service, and keeps enough source information to support maintenance
and optional updates.

## Repository Layout

Each service keeps its own component repository. In the standard service data layout this is under:

```text
services/<service-type>/components/
```

The repository contains three separate concerns:

```text
components/
  catalog.json
  cache/
    catalog.json
    ...
  plugins/
    *.jar
```

`plugins/` is the only directory scanned by PF4J. Imported `.kar` files are copied or installed
there with a `.jar` extension, because PF4J loads Java archives. Keeping loadable archives under
`plugins/` prevents unrelated repository files, including the Maven cache, from being interpreted
as plug-ins.

`cache/` is used for Maven-sourced artifacts. It records the component archive discovered in the
local Maven repository or downloaded from a remote repository, together with content hashes and
timestamps used to decide whether an update is needed.

`catalog.json` is the registry's local component catalog. It records the descriptors for components
known to the service, including the source archive, source hash, Maven coordinates when applicable,
usage rights, exported capabilities, and the time of registration or update.

When an older repository contains loadable `.jar` files directly in the repository root, startup
migrates them into `plugins/` when possible. Files that are not plug-ins should remain outside
`plugins/`.

## What A Component Can Add

A component can contribute several kinds of service-visible functionality. A single component may
bring any combination of these.

### Libraries

A library is a namespace for k.LAB service verbs and language extensions. It can define:

- k.IM, observation-language, or runtime functions through `@KlabFunction`.
- k.Actors verbs through `@Verb`.
- k.LAB annotations and handlers through `@KlabAnnotation`.
- Import schemata through `@Importer`.
- Export schemata through `@Exporter`.

Library names become part of the public name of the contributed functions, verbs, annotations,
importers, and exporters. This keeps component contributions distinguishable from core k.LAB
extensions and from other components.

### Actors

Actors are specialized libraries for k.Actors use. They can expose singleton actors or actor
classes that behaviors import with a `using` clause. Actor classes may also define verbs that
apply to the actor. Component actors should use explicit path-like names so they remain unique
outside the core distribution.

### Resource Adapters

Resource adapters teach a Resources service how to understand, validate, contextualize, publish,
inspect, or encode a class of resources. A resource adapter declares a unique adapter name,
version, supported geometry, resource type, parameter schema, concurrency model, and optional
runtime constraints such as split behavior or maximum geometry size.

Adapter methods can implement lifecycle operations such as:

- URN syntax validation.
- Local import and staging validation.
- Pre-contextualization checks and cache preparation.
- Encoding and contextualization.
- Inspection, sanitization, publication, and type attribution.

Adapters may be embeddable or service-bound. An embeddable adapter can be used locally by a
runtime close to the data. A service-bound adapter must be invoked through the Resources service
that provides it, which is appropriate when the adapter depends on server-side state or protected
infrastructure.

### Import And Export Schemata

Importers and exporters describe transport formats for k.LAB assets. They may be defined in a
library or attached to a resource adapter. A schema can be based on binary content, such as a file
or stream, or on named properties.

The built-in component I/O library currently defines:

- `component.kar.import`: import a component by uploading a `.kar` archive.
- `component.maven.import`: import a component from Maven coordinates.
- `component.jar.export`: export an installed component archive.

Other components can add domain-specific import and export schemata for resources or other assets.

### Runtime Services

`@KlabFunction` contributions become executable service implementations. Depending on their
signature and metadata, they may serve as contextualizers, filters, producers, value functions, or
other runtime functions used by k.IM, k.Actors, and the observation language. Their descriptors
include declared parameters, inputs, outputs, geometry constraints, artifact type, fill curve, and
parallelization hints.

## Import Paths

### Direct `.kar` Import

A direct import uploads a component archive to a service. The registry validates that the archive
looks like a Java archive with a manifest, copies it into `plugins/`, loads it with PF4J, and scans
it for k.LAB contributions.

Direct imports are intentionally local. They do not record Maven coordinates, so the registry
cannot automatically rediscover a newer build. Updating a directly imported component means
uploading a replacement `.kar` or importing a newer version.

### Maven Import

A Maven import identifies the component with:

```text
groupId:artifactId:version
```

The registry asks the Maven component cache for the artifact with classifier `component` and
suffix `kar`. The cache first looks in the local Maven repository, then in configured remote Maven
repositories when needed. The resulting `.kar` is cached, installed into `plugins/` as a `.jar`,
loaded with PF4J, and registered with its Maven coordinates.

Maven-sourced components keep their coordinates in the component descriptor. That source
information is what enables later update checks.

### Service-to-Service Transfer

An installed component can be exported as a Java archive and imported by another service. This is a
distribution path for already available components, not a Maven-managed source. Unless the target
service imports the same component through Maven coordinates, it should be treated like a direct
local import for update purposes.

## Registration And Discovery

After PF4J loads a component, the registry scans it and builds a `ComponentDescriptor`. The
descriptor records:

- The component id, version, and description from the plug-in descriptor.
- The local source archive and its file hash.
- Maven coordinates, when the component came from Maven.
- Usage rights inferred from the plug-in manifest.
- Libraries, actors, adapters, services, annotations, verbs, importers, and exporters.
- The source service id, when applicable.
- The registration or update timestamp.

The descriptor is saved to `catalog.json` and indexed by contribution type. Service verbs,
adapters, annotations, verbs, importers, and exporters can then be resolved by name. When more than
one descriptor can satisfy a request, the registry prefers the highest version compatible with the
requested version. Exact version requests are matched exactly.

The registry also has a local service component. This makes built-in service libraries and adapters
visible through the same lookup mechanism used for imported components.

## Versioning And Compatibility

Component versions are independent from the k.LAB service version, but they must declare whether
they can run with the hosting k.LAB version. Compatibility is controlled through the plug-in
manifest's PF4J version requirement, conventionally `Plugin-Requires`.

At startup the component manager sets the PF4J system version to the current k.LAB version. During
update checks, a candidate replacement archive is opened before installation and its version
requirement is checked against the current k.LAB version. If the requirement is absent, blank, or
`*`, the archive is accepted as compatible. If it declares an incompatible requirement, the update
is skipped and the existing component remains installed.

For predictable maintenance:

- Use stable semantic versions for released components.
- Use `-SNAPSHOT` only for components that are expected to change in place.
- Set `Plugin-Requires` narrowly enough to prevent loading against incompatible k.LAB releases.
- Keep the PF4J plug-in id stable across versions of the same component.
- Use unique names for libraries, actors, adapters, and service verbs.

Side-by-side descriptors for multiple component versions can exist in the catalog, but PF4J plug-in
ids are unique in the running plug-in manager. In practice, the runtime should be maintained as one
active version of a plug-in id at a time, with the registry selecting the best compatible
descriptor for lookups.

## Update Modes

Components can be updated manually or automatically. Automatic updates apply only to Maven-sourced
SNAPSHOT components.

### Manual Direct Update

Upload a new `.kar` archive with `component.kar.import`, or use the service path that verbs the
same importer. This is the right path for local development builds, private hand-offs, and
components that are not published to Maven.

The update is local to the service that receives the archive. The registry loads the replacement,
rescans its contributions, updates the descriptor, and saves the catalog.

### Manual Maven Update

Import the desired Maven version with `component.maven.import`, or call the registry's Maven
installation path. This works for stable releases and snapshots.

For stable releases, prefer publishing a new version and importing that explicit version. Stable
versions are not expected to change in place, so they are not part of the automatic SNAPSHOT update
loop.

### Explicit SNAPSHOT Check

The registry exposes an explicit update check for Maven-sourced SNAPSHOT components. The check
walks the registered components and considers only descriptors that have Maven coordinates whose
version identifies a SNAPSHOT build.

For each candidate, the Maven cache determines whether:

- The cached artifact is up to date.
- A different artifact exists in the local Maven repository.
- A newer snapshot appears to exist in a configured remote repository.
- The status cannot be established.

When an update is indicated, the registry synchronizes the artifact, compares the candidate file
hash to the installed descriptor hash, verifies k.LAB compatibility, unloads the current component,
installs the replacement archive, registers the new descriptor, and saves the updated catalog.

Hash comparison is important because SNAPSHOT timestamps and repository metadata can be noisy. If
the retrieved archive has the same content hash as the installed archive, the registry does not
replace the component.

### Startup Check

Services can request a one-time update check after component registry initialization. The startup
option is:

```text
-updateComponents
```

The current service startup options enable this by default. Implementations that only use the
`StartupOptions` interface inherit the same default unless they override it.

### Periodic Automatic Check

Services can also schedule repeated SNAPSHOT checks:

```text
-autoUpdateComponents
-componentUpdateIntervalMinutes <minutes>
```

The interval defaults to five minutes and is clamped to at least one minute. Scheduled checks run
quietly: successful updates are logged, and failures are reported through service logging without
stopping the service.

Periodic updates should be enabled deliberately. They are useful for controlled development and
integration environments where SNAPSHOT components are expected to move. Production services
should normally prefer explicit stable versions or an explicit maintenance operation.

## Cache Behavior

The Maven cache keeps a small catalog for each synchronized artifact. Its entries include the Maven
coordinates, cached file, content hash, and last-modified time. The update strategy is:

1. Prefer the local Maven repository when the requested artifact exists there.
2. Compare the local artifact hash with the cached hash.
3. For SNAPSHOT versions not available locally, check remote snapshot metadata.
4. Download or copy only when the cache says an update is needed.
5. Keep the previous cached artifact if retrieval fails.

This makes local development fast: installing a new SNAPSHOT into the local Maven repository is
enough for the next explicit or scheduled check to notice a content change.

## Operational Guidance

Component loading is hot-swappable, but the practical safety of replacing a component depends on
what is using it. Updating a component that is actively serving contextualization, resource
validation, or long-running operations can leave callers with references to classes from the old
plug-in. Windows file locking can also prevent immediate replacement of archives in some cases.

For low-risk operation:

- Update during service startup or a quiet maintenance window when possible.
- Prefer explicit update checks over frequent automatic checks in production.
- Keep component archives dependency-free and small.
- Do not put non-component files in `plugins/`.
- Treat imported components as trusted code. Manifest usage rights govern resource visibility and
  sharing, but they are not a security sandbox.
- Keep stable releases immutable. Publish a new version instead of replacing an old release.
- Use SNAPSHOT automatic updates only where changing artifacts in place is acceptable.

## Packaging Checklist

A component archive should include:

- A unique PF4J plug-in id that is also meaningful as the component id.
- A component version.
- A plug-in class implementing the k.LAB component contract.
- A human-readable description.
- A provider or vendor identity when available.
- A license or rights declaration that can initialize usage rights.
- A `Plugin-Requires` constraint for the compatible k.LAB version range.
- Only the classes and resources needed by the component itself.

The Maven artifact intended for component import should be published with classifier `component`
and suffix `kar`, so the registry can resolve it as:

```text
groupId:artifactId:version:component:kar
```

The import-facing coordinate remains the simpler:

```text
groupId:artifactId:version
```

## Minimal Workflows

Install a component from a local archive:

```text
component.kar.import(file = my-component.kar)
```

Install a component from Maven:

```text
component.maven.import(
  groupId = org.example,
  artifactId = my-component,
  version = 1.2.0
)
```

Install a development SNAPSHOT and let the service check for newer local or remote builds:

```text
component.maven.import(
  groupId = org.example,
  artifactId = my-component,
  version = 1.3.0-SNAPSHOT
)
```

Then run an explicit update check from the hosting service, or start the service with periodic
checks enabled:

```text
-autoUpdateComponents -componentUpdateIntervalMinutes 10
```

The automatic path will update only if the component is Maven-sourced, its version is a SNAPSHOT,
the retrieved archive hash differs from the installed archive hash, and the candidate archive is
compatible with the current k.LAB version.
