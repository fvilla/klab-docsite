# Storage in the k.LAB runtime

This document is the central implementation guide for observation storage in k.LAB. It describes
how a quality receives a storage contract, how that contract becomes shards and primitive buffers,
how contextualizers access the buffers, and how data is finalized and persisted. The public API is
defined by `Storage`, `StorageManager`, and `Data.ShardingStrategy`; the main implementation is in
`StorageManagerImpl`, `StorageImpl`, and `ScannerAdapters`.

Storage belongs to a digital twin. A `StorageManager` owns one `Storage` per quality observation,
and a `Storage` owns time-indexed groups of non-overlapping `Shard` objects. A shard owns one native
primitive buffer. Contextualizers never receive the buffer itself: they access it sequentially
through a typed `Storage.Scanner`.

## Core contract

The three layers of the storage contract are:

| Layer | Responsibility |
|---|---|
| `Data.ShardingStrategy` | Declares primitive type, fill curve, split count, minimum split size, and maximum buffer size. |
| `Storage` and `Storage.Shard` | Own the observation data and describe its physical partitioning for an event. |
| `Storage.Scanner` | Provides sequential, primitive, optionally read-only access to one shard. |

The native strategy is part of `Observation.ContextualizationData`. Once storage exists, that
strategy describes the bytes in its shards and must not be silently reinterpreted. A setting change
affects storage attributed after the change; it does not migrate existing storage.

`Storage.Type` maps to scanner and buffer types as follows:

| Native type | Scanner | Primitive buffer width | Normal semantic use |
|---|---|---:|---|
| `DOUBLE` | `DoubleScanner` | 8 bytes | Numeric quality, full precision |
| `FLOAT` | `FloatScanner` | 4 bytes | Numeric quality, reduced precision |
| `INTEGER` | `IntScanner` | 4 bytes | Integer state |
| `LONG` | `LongScanner` | 8 bytes | Long integer state |
| `KEYED` | `KeyScanner` backed by integer codes | 4 bytes | Classified/concept state |
| `BOOLEAN` | `BooleanScanner` | 1 byte | Presence or verification state |

The generic `Scanner` deliberately has no boxed `get` or `add` operation. Typed scanners exist so
large contextualizations can execute without per-value allocation or boxing.

## Attributing the native strategy

`CompiledDataflow.harmonizeSharding()` attributes storage before the first contextualization of a
new quality:

1. `RuntimeService.getDefaultShardingStrategy()` derives a semantic default. Quantification,
   measurement, and valuation use `DOUBLE`; categorization uses `KEYED`; verification uses
   `BOOLEAN`.
2. Model computations and adapter/component declarations contribute their sharding requirements.
3. Compatible requirements from dependent actuators are harmonized. Numeric primitive types may
   override one another; numeric and non-numeric types are incompatible.
4. The runtime applies service settings. `USE_SHORT_FLOAT_REPRESENTATION=true` changes a resulting
   `DOUBLE` type to native `FLOAT`. `PARALLELIZE_OBSERVATIONS=false` forces one split; otherwise the
   runtime suggests the available processor count.
5. The result is written to the observation's contextualization data. `StorageManager.createStorage`
   requires this field and fails if it is missing.

Existing positive-ID observations retain the strategy recorded when they were created. This is
necessary for reconstruction: the strategy is used to select the mapped-buffer representation and
to validate persisted shard data.

The strategy's fill curve is derived from geometry when no stronger declaration exists. Regular
two-dimensional space uses `D2_XY`, regular three-dimensional space uses `D3_XYZ`, and other cases
use `D1_LINEAR`. Split policy is applied to the event-local geometry when shards are first created.

## Creating and finding storage

Each `ServiceContextScope` owns a `StorageManagerImpl`. The manager indexes storage by observation
ID:

- `createStorage(observation)` creates it lazily from the observation's attributed strategy;
- `getStorage(observation)` returns an existing entry or reconstructs one from contextualization
  data and knowledge-graph shard descriptors;
- `finalizeStorage(temporaryId, finalId)` rekeys storage when transaction commit assigns the
  persistent observation ID;
- `clear()` and `deleteStorage(...)` close mapped buffers and remove the context's persisted files.

Calling `getStorage` without an existing or reconstructable contract is an error. Storage creation
is not the place to infer semantics or consult current settings: attribution must already have
happened during dataflow compilation.

## Shards, events, and buffers

`StorageImpl.getNativeShards(event)` selects a shard group using the scheduler event. Time is the
moving dimension in the current implementation: initialization uses timestamp zero and later
events use their start timestamp. Other non-space dimensions are reserved in the cache key but are
not yet fully generalized.

On first access, the event-local scale is split according to the native strategy. The resulting
shard geometries do not overlap and their union represents the observation geometry for that
event. Each `ShardImpl` records its geometry, index/count, timestamp, strategy, persistence policy,
and native type.

`ShardStorage` allocates an ojAlgo mapped `BufferArray` of the exact primitive width. Scratch buffer
files live in the storage manager workspace. They are closed when the manager closes; on Windows,
ojAlgo may retain mappings until garbage collection, so deterministic deletion of every scratch
file is not currently guaranteed.

## Scanning and contextualizer binding

`Storage.scan(event, request, scannerClass, readOnly)` is the access boundary. For a request that
matches the native geometry, fill curve, and split policy, it opens one scanner per native shard.
Write scanners reset the shard histogram only after pending persistence has been flushed; read-only
scanners reject `add(...)`.

The requested scanner class is a real contract, not a hint. The storage layer either returns an
instance assignable to that class, supplies a compatible primitive adapter, or fails explicitly.
It must never return a scanner of another type and defer failure to reflection.

During a quality contextualization, `AbstractExecutor` opens native output scanners and conformant
read-only scanners for quality dependencies. It constructs one task per output shard and binds
component method parameters by the declared input/output name. Parameters may request:

- the `Observation` itself;
- the scanner's `Shard` view;
- generic `Storage.Scanner`;
- the matching typed scanner;
- `DoubleScanner` over native float storage, or `FloatScanner` over native double storage.

The last two cases use `ScannerAdapters`. These are primitive, write-through decorators. A
float-to-double read uses primitive widening; a double-to-float write uses primitive narrowing and
therefore has exactly the precision loss requested by `USE_SHORT_FLOAT_REPRESENTATION`. The reverse
adapter supports a component explicitly requesting floats over double-native storage. The adapter
delegates `shard()`, `size()`, `hasNext()`, and `nextLong()` to the native scanner, so cursor,
geometry, histogram, mutability, and persistence identity are unchanged. It allocates one small
adapter per scanner, never one object per value and never a converted buffer.

No conversion is permitted between floating-point scanners and boolean or keyed scanners. Such a
declaration is a component contract error and fails during binding with the native and requested
types in the message.

### Component author rules

Component contextualizers should follow these rules:

- Declare `DoubleScanner` when the algorithm operates in double precision. It remains compatible
  with short-float runtime storage through primitive mediation.
- Declare `FloatScanner` only when float arithmetic is intentional. It can consume double-native
  storage, but reads narrow to float.
- Declare generic `Scanner` only when the implementation does not call typed value methods or
  dispatches explicitly by `scanner.shard().getNativeType()`.
- Mark input and output parameters accurately. Inputs receive read-only scanners; writing through
  them is always an error.
- Do not retain a scanner beyond the contextualizer invocation or share it with another shard task.
  A scanner owns mutable cursor state.
- Do not assume one shard. Parallelism settings and geometry can produce several independent
  invocations.

Components do not need recompilation when `USE_SHORT_FLOAT_REPRESENTATION` changes. Scanner
interfaces remain the API contract, and the runtime mediates the compatible floating-point
representation at invocation time.

## Finalization, histograms, and persistence

After a shard task succeeds, `Storage.finalizeRun(nativeScanner)` snapshots the shard histogram and,
when the digital-twin persistence policy survives shutdown, schedules the native buffer for
persistence. Finalization deliberately receives the native output scanner rather than a component
adapter.

Persistence runs through a single maintenance executor. Before a writable scanner resets data or
histogram state, pending persistence is flushed so an asynchronous writer cannot observe a new
run's mutations. Each shard is written to a unique temporary file and moved into place atomically
when supported by the filesystem.

The current file format contains a magic number, format version, native type, element width, value
count, and a big-endian primitive payload. Reads validate the header and exact file length. A
backward-compatible reader accepts the original headerless native-endian format when its length is
exactly valid. Knowledge-graph `HAS_DATA` relationships retain shard descriptors; the files retain
the primitive payload.

## Concurrency and failure behavior

Different shard scanners may execute concurrently on virtual threads. A scanner and its cursor are
task-local. `StorageImpl` uses concurrent maps for shard groups and backing state, while shard
creation is synchronized to prevent duplicate allocation.

Scanner contract failures must be reported before reflective contextualizer invocation. Execution
retains the first concrete task failure as the executor cause; the generic `Execution failed`
exception is used only when no more specific cause was recorded. This distinction is important
because collective contextualization otherwise reports only the parent failure.

## Unsupported or incomplete operations

The following remain explicit implementation boundaries:

- geometry-aware scanner split/merge and fill-curve remapping when the requested sharding strategy
  differs from native storage;
- unit mediation in scanner decorators;
- temporary scanners from `StorageManager.getTemporaryScanner(...)`;
- complete generalized indexing for moving dimensions other than time;
- a durable, mergeable key descriptor for `KEYED` storage;
- cleanup of orphan persisted shards and fully deterministic mapped-file unmapping;
- applying partial-quality actuator coverage to execution storage.

Callers must not silently fall back to native scanners when one of these operations is requested.
An explicit unsupported-operation failure protects buffer order, type safety, and data integrity.

## Verification

Focused scanner mediation tests are in `ScannerAdaptersTest`. Storage width and durable buffer
round-trip tests are in `StorageManagerImplTest`; broader persistence and contextualization tests
exercise storage through the runtime module. The minimum focused verification is:

```powershell
.\mvnw.cmd -pl klab.core.services -am "-Dtest=ScannerAdaptersTest,StorageManagerImplTest" "-Dsurefire.failIfNoSpecifiedTests=false" test
```

Changes to attribution or executor binding should additionally compile and test
`klab.services.runtime` because that module owns sharding harmonization and component invocation.
