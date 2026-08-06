# Scopes in k.LAB Services

Scopes are the execution envelope of k.LAB. They are how an identity, a set of
permissions, a service topology, a communication channel, and a lifecycle are
kept together while work moves across clients and services.

Most service functions are not meant to run as anonymous, stateless verbs. They
run in a scope. The scope says who is asking, which services are available to
that caller, where state is hosted, how messages and notifications return to the
caller, and when the created state can be released.

This document describes the scope model from the point of view of the running
system. Class and API names are included only where they clarify the workflow.

## Mental Model

A scope is a live handle, not just an identifier.

It carries:

- the authenticated identity and its roles, groups, and anonymous/authenticated
  status;
- the service catalog visible to that identity;
- the current lifecycle status and notifications;
- arbitrary scope data shared by child scopes;
- messaging and reactive behavior for events, errors, status changes, and actor
  communication;
- a stable ID when the scope must be referenced by another process.

Scopes are hierarchical:

```text
service process
  ServiceScope

authenticated user
  UserScope
    SessionScope
      ContextScope
        ContextScope views focused within observations, relationships,
        observers, resolution constraints, or transactions
```

The service scope belongs to a service process. User, session, and context
scopes belong to a user workflow and may have peer objects in several services.

Scopes are not serialized and sent wholesale between processes. Instead, the
originating side sends authentication plus compact scope identifiers and
headers. The receiving service reconstructs or looks up the matching local peer
scope in its own `ScopeManager`.

Because the concrete Java scope classes inherit from each other, code should use
the scope type (`SERVICE`, `USER`, `SESSION`, `CONTEXT`, and the session
subtypes) when it needs to discriminate the role of a scope.

## Scope Kinds

### Service Scope

A service scope is created when a service process starts. It is the root scope
for that service. It gives the service access to its owning identity, logging,
availability flags, locality, and other services it may need outside of any
particular user request.

There are two main service-scope modes:

- A local user-owned service runs under a user identity. This is represented by
  `UserServiceScope`. It is used when the Engine starts local services for a
  user who has already authenticated.
- A networked or partner service runs under a service or partner identity. It
  uses service-level credentials and the hub-mediated service catalog.

The service scope is different from a service-side user scope. The first owns
the service process. The second mirrors an authenticated client user inside that
service.

### User Scope

A user scope is the root of all work performed by one authenticated identity.
It restricts service access to the services and operations visible to that
identity. It also owns the service catalog used by ordinary service verbs.

At client side, authentication creates a client user scope. At service side, an
incoming authenticated request creates or reuses a service-side user scope. The
service-side user scope contains clients for the services advertised by the
Engine, plus the hosting service itself when appropriate.

An anonymous user scope is valid when authentication is absent or fails and the
requested endpoint allows anonymous access. It should be treated as a legitimate
identity with limited privileges, not as an exception. It is still important to
log anonymous creation paths because unexpected anonymous scopes usually point to
missing authentication propagation.

### Session Scope

A session scope is a stateful child of a user scope. It represents a user
session, application, script, API session, or similar unit of work.

In the normal Engine workflow there is one user session per runtime service for
the user, with an ID derived from the username or federation ID. Dots are
normalized to underscores so the ID can safely be used in propagated scope
tokens.

The session scope pins its host runtime service. Calls made with that session
carry both the session ID and the ID of the runtime that hosts it. This lets a
receiving service reconstruct the same session peer if the scope is not already
registered locally.

### Context Scope

A context scope is the live handle to a digital twin. It is the scope used to
create, register, resolve, query, and contextualize observations.

A context scope belongs to a session and is hosted by a runtime. It carries the
digital twin configuration, the host runtime ID, a context ID, optional current
transaction, observation focus, observer, source and target observations for
relationships, and resolution constraints.

Context scopes can have child context views. These child views do not create new
digital twins by themselves. They focus the same digital twin at a particular
observation, relationship, observer, transaction, geometry, namespace, or other
resolution constraint.

The root context scope is registered by the runtime. Focused child scopes are
often reconstructed from request headers by starting from the registered root
and applying the propagated focus.

### Service-Side Peer Scopes

Each service keeps its own local peer scopes in its `ScopeManager`:

- `ServiceUserScope` mirrors a user inside one service.
- `ServiceSessionScope` mirrors a session inside one service.
- `ServiceContextScope` mirrors a context or contextualized view inside one
  service.

These objects are local to the service that owns them. If another service needs
to use the same logical session or context, it creates its own peer using the
propagated scope ID, host runtime ID, and digital twin configuration.

## The Engine As Orchestrator

The Engine is the orchestrator of scope creation and propagation.

At startup it authenticates the user certificate and creates the default user
scope. It then builds a `ServiceMonitor`, discovers local and remote service
clients, starts local services when needed, and watches service status.

For local services, the Engine can pass the hub authentication response it
already received during user authentication. This is encoded as a local
authentication package and handed to newly started service processes through
startup options or the `KLAB_LOCAL_AUTHENTICATION_RESPONSE` environment
variable. A local service that receives this package reconstructs the same user
identity without making a new authentication request to the hub. If the package
is absent, unreadable, or reconstructs an anonymous user, the service falls back
to its ordinary certificate/hub authentication path.

Once the Engine sees the service set as operational, it advertises the user
scope to services. The notification contains the user's email address and the
service inventory visible to that user. Each service uses that notification to
populate the service catalog of its service-side user scope. This is what lets
later code use the scope to find services instead of maintaining independent
routing tables.

The Engine also re-advertises the user scope to a service that becomes
operational after the first notification. This matters during local startup,
where the four critical services may become reachable in different orders.

The Engine does not merely start processes. It establishes the authenticated
user, injects or propagates that user to local services, builds the client-side
service graph, and teaches services the corresponding service-side graph.

## Creation Workflows

### Engine Authentication

1. The Engine authenticates a certificate or uses an explicit certificate
   supplied by the caller.
2. Authentication returns an identity and a list of service references.
3. The Engine creates the client-side user scope.
4. The Engine stores the latest authentication response so it can be handed to
   local services.
5. The service monitor creates service clients in the user scope.
6. When services are operational, the Engine sends a user-scope notification to
   each service.

The client user scope is the root of normal client work.

### Local Service Startup

1. The Engine starts local service processes for resources, reasoner, runtime,
   and resolver when they are not already reachable.
2. If an authentication package is available, the Engine injects it into the
   process environment.
3. The service reads startup options. If the package is present, it decodes the
   package and reconstructs the user identity and advertised services.
4. If reconstruction produces a non-anonymous user identity, the service creates
   a user-owned service scope.
5. If reconstruction fails, or no package was injected, the service
   authenticates through its configured certificate and hub path.

If a local service is already running, the Engine cannot inject a fresh
authentication package into that process. The service will continue with the
identity it already has until it is restarted.

### Service-Side User Scope Creation

Every authenticated service request passes through service authorization before
controller or service code sees it.

1. The authorization layer validates the token and local-service secret, when
   applicable.
2. It creates an authorization object containing username, token, local flag,
   groups, roles, request headers, and later the resolved scope.
3. The service `ScopeManager` gets or creates a `ServiceUserScope` for that
   username.
4. If this is the first request for that user in the service, the service builds
   a user identity from the authorization and registers the user scope.
5. Controller code retrieves the resolved scope from the authorization object.

If no lower-level scope header is present, the resolved scope is the user scope.

### Session Creation

A session is created when user code asks for a user session on a runtime.

1. The client user scope computes the session ID from the username or federation
   ID.
2. If the client already has a session scope with that ID, it reuses it.
3. Otherwise it creates a client session scope bound to the selected runtime.
4. The runtime is asked to declare the session.
5. The service-side runtime creates or registers the matching service session
   scope.
6. The client registers the returned session locally.

When another service later receives a request for the same session but does not
have a registered peer, it may reconstruct the peer session if the propagated
session ID matches the authenticated user or federation and the host runtime ID
is known.

### Context Creation

A context is created from a session and a digital twin configuration.

1. The client session scope builds a client context scope.
2. The hosting runtime is asked to declare the context.
3. The runtime assigns the context ID if the configuration did not already
   contain one. The normal ID shape is the session ID followed by a generated
   context component.
4. The runtime registers a service context scope and creates the digital twin.
5. The client applies the returned configuration and registers the client
   context scope.
6. If federation messaging is active, queues are configured so context events
   can move across peers.

When a non-host service needs the context, it does not own the digital twin. It
registers a peer scope and typically uses a client digital twin handle backed by
the host runtime.

### Context Reconnection and Reconstruction

If a service receives a context-scoped request and the context peer is not
registered locally, the service tries to reconstruct it.

It needs:

- the authenticated user;
- the propagated context scope token;
- the host runtime service ID;
- access to that runtime in the user's service catalog;
- the digital twin configuration from the host runtime.

The service reconstructs or creates the parent session first, then creates the
context peer, copies available services into it, registers it, and applies the
request identity. If the context token contains observation or observer focus,
the service contextualizes the peer after the root context is available.

Without the host runtime ID, context reconstruction cannot be reliable because
the service cannot know which runtime owns the digital twin configuration and
state.

## Propagation Across Processes

Scope propagation uses two parallel channels: identity propagation and scope
position propagation.

Identity propagation is carried by authentication. A client call made with an
identity sets the authorization token. For service identities this is the
service token. For user identities this is the user identity token. Local
services may also use a local service secret so that privileged localhost verbs
can be distinguished from ordinary remote requests.

Scope position propagation is carried by headers. The important headers are:

- `klab-scope`: the session ID or compact context token;
- `klab-service`: the service ID of the runtime hosting the session or context;
- `klab-transaction`: the current digital twin transaction, when any;
- `klab-context-observation`: the focal context observation ID, when needed;
- `klab-source-observation`: the source observation ID for relationship scope;
- `klab-target-observation`: the target observation ID for relationship scope.

For a session, `klab-scope` is simply the session ID.

For a context, `klab-scope` starts with the root context ID and may append an
observation path and observer marker. Conceptually:

```text
session.context[.observation-path][#observer]
```

The receiving service parses this token to determine whether the request needs
a session or context scope and whether the resolved context must be focused
inside observations or switched to another observer.

The token is only a locator. It must be evaluated together with the
authenticated identity and service ID. A token without authentication is not a
scope.

## Scope Resolution In Services

When a request reaches a service, the authorization layer resolves the scope
before application code runs.

The resolution algorithm is:

1. Validate the request token, local privilege, and expiration where applicable.
2. If local privilege applies and the incoming token is missing or anonymous,
   repair the authorization from the local service owner when the owner is a
   non-anonymous user.
3. If no valid identity remains, create anonymous authorization.
4. Get or create the service-side user scope.
5. If there is no `klab-scope` header, use the user scope.
6. If there is a session token, look up or reconstruct the session scope.
7. If there is a context token, look up or reconstruct the context scope, then
   contextualize it using transaction and observation headers.
8. Attach the resolved scope to the authorization object used by controllers.

This means controllers and service implementations should normally receive a
ready scope from the request principal. They should not parse authentication or
scope headers themselves unless they are part of the authorization layer.

## Service Access Through Scopes

All normal service functions are accessed through scopes.

At client side, service clients call the HTTP layer with the current scope. The
HTTP layer adds the authentication and scope headers needed by the receiving
service. Session and context verbs automatically carry the host runtime ID.
Context verbs also carry transaction and observation focus when available.

At service side, implementation code asks the scope for other services:

```text
scope.getService(RuntimeService)
scope.getService(ResourcesService)
scope.getService(Resolver)
scope.getService(Reasoner)
```

Those lookups are identity-aware because the service catalog is stored in the
scope. A local service scope prefers local services when possible. A service-side
user scope uses the service inventory advertised by the Engine.

The runtime, resolver, reasoner, resources service, knowledge graph, dataflow
compiler, and digital twin code all use scopes this way. For example,
submitting an observation requires a context scope; retrieving resources uses
the requesting scope; knowledge graph queries receive a scope so visibility,
runtimeAgent, provenance, and context are preserved.

Public service endpoints such as health and status can be scope-light. Ordinary
stateful operations should not be.

## Messaging And Reactive Behavior

User, session, and context scopes are reactive scopes. They can send
notifications, errors, status changes, and actor messages. When federation data
provides a broker, scopes may set up messaging queues so events can reach peers
across processes.

The scope dispatch ID is derived from the username or federation ID. Session and
context scopes use their own IDs for dispatch where needed. Context peers use
messaging to keep distributed digital twin events and client-side updates
connected.

Messaging is intentionally tied to scope identity. A message emitted from a
context scope is not just an event. It is an event from a particular user,
session, context, observer, and service topology.

## Deletion And Lifetime

Scope lifetime is explicit for sessions and contexts and mostly process-bound
for user and service scopes.

Client-side scope cleanup:

1. Closing a client context unregisters it locally and asks the hosting runtime
   to release the context.
2. Closing a client session unregisters it locally, closes messaging, and asks
   the hosting runtime to release the session.
3. Engine shutdown closes the client scope manager, which closes registered
   client sessions and contexts.

Service-side scope cleanup:

1. The runtime release endpoint verbs `close()` on the resolved session or
   context scope.
2. A service context close sends a context-closed message, disposes the digital
   twin when the service owns it, closes closeable scope data, closes messaging,
   and releases the scope from the service `ScopeManager`.
3. A service session close closes active context peers and releases the session
   from the service `ScopeManager`.
4. The `ScopeManager` removes the ID from its registry and logs the release.

Digital twin lifetime is related to, but not identical to, scope lifetime. A
context has a persistence policy:

- `ONE_OFF`: intended to disappear when out of scope.
- `IDLE_TIMEOUT`: removed after an inactivity timeout.
- `SERVICE_SHUTDOWN`: closed when the hosting service shuts down.
- `REINITIALIZED_ON_TIMEOUT`: reset to an empty state after inactivity.
- `EXPLICIT_ACTION`: persistent until an authorized explicit action deletes it.

The runtime also checks for orphan contexts and idle contexts. If a context has
no registered scope and is not persistent, the runtime can remove its knowledge
graph and storage state. If it is configured for reinitialization, it can reset
the digital twin instead of deleting it.

Service-side user scopes are created on demand and normally live for the
service process lifetime. The explicit logout path is not the primary cleanup
path for the current service workflow.

## Anonymous Identities

Anonymous identities are valid, but unexpected anonymous identities in local
service workflows usually indicate propagation loss.

Common causes are:

- the Engine authenticated correctly but did not retain an authentication
  response to hand to local services;
- a local service was already running, so the Engine could not inject the local
  authentication package into its process environment;
- the local authentication package was missing, unreadable, or decoded to an
  anonymous user;
- the service authenticated independently through a path that returned
  anonymous;
- a privileged localhost request arrived with an anonymous owner service scope;
- the request carried a scope token but no usable authenticated identity;
- the session ID did not match the authenticated user or federation;
- a context-scoped request omitted the host runtime service ID needed for
  reconstruction.

When debugging anonymous scopes, follow the chain in this order:

1. Engine certificate authentication and returned identity.
2. Local authentication package preparation in the Engine service monitor.
3. Process startup path for each local service.
4. Service startup authentication and `UserServiceScope` creation.
5. User-scope notification from Engine to each service.
6. Per-request authorization and `ScopeManager.getOrCreateUserScope`.
7. Session/context token parsing and reconstruction.

The logging around these steps is intentionally important. Anonymous is not
always an error, but the transition from an authenticated Engine user to an
anonymous service-side user should be visible in logs.

## Practical Rules

- Pass a scope to every non-public service operation.
- Use the narrowest correct scope: user for identity-level operations, session
  for session lifecycle, context for observations and digital twin work.
- Let service authorization resolve scopes from headers. Controller and domain
  code should use the resolved principal scope.
- Do not serialize scope objects. Propagate authentication, scope ID, host
  runtime ID, and contextual headers.
- Always include the host runtime ID for session and context scopes.
- Use the scope's service catalog instead of constructing service clients ad
  hoc.
- Prefer scope type over concrete-class checks when the distinction matters.
- Treat anonymous as a valid but low-privilege identity, and log how it was
  reached when it was not expected.
- Restart already-running local services after authentication propagation
  changes; an already-running process cannot receive a newly prepared startup
  authentication package.

## End-To-End Example

The normal local Engine workflow looks like this:

```text
User certificate
  -> Engine authentication
  -> client UserScope
  -> ServiceMonitor starts local services with authentication package
  -> each local service creates UserServiceScope from the package
  -> Engine advertises user scope and service inventory
  -> service ScopeManagers create ServiceUserScope peers
  -> user asks runtime for a session
  -> client and runtime create/register SessionScope peers
  -> user creates a context
  -> runtime creates/registers ContextScope and digital twin
  -> downstream service verbs carry authentication plus scope headers
  -> receiving services resolve or reconstruct peer scopes
  -> all service functions execute through the resolved scope
  -> close/release removes scope peers and, depending on persistence, digital
     twin state
```

The important invariant is that the same logical user workflow is represented
by local peer scopes in every process that participates. Each peer is created
from authentication plus scope tokens, registered locally, used to route all
work, and released when its lifecycle ends.
