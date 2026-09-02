# k.Actors language guide

This file is a user-level introduction and reference for k.Actors as implemented in the current
`klab-services` distribution. It is also intended to give contributors and coding agents enough
context to read, validate, test, and extend k.Actors code without having to reconstruct the
language model from Java interfaces.

The current Xtext grammar is the authority for source syntax. It lives in the sibling
`klab-languages` repository at
`org.integratedmodelling.languages.kactors/src/org/integratedmodelling/languages/KActors.xtext`.
The `KActorsBehavior`, `KActorsAction`, `KActorsStatement`, and `KActorsValue` interfaces in
`klab.core.api` define the semantic contract after parsing. For conceptual
background, see the [reactivity and digital-twin section of the current k.LAB
technical note](KLAB.md#the-reactivity-layer-and-digital-twins).

k.Actors is the reactive member of a three-language architecture. The
[worldview ontology language](ONTOLOGY_LANGUAGE.md) (`.kwv`) defines shared
concepts; [k.IM](KIM.md) (`.kim`) publishes strategies for observing them; and
k.Actors (`.kactor`) instruments observations, digital twins, users, and
sessions with behavior. All three inherit the
[observable expression language](OBSERVABLES.md), but k.Actors accepts an
observable only as a `{{ ... }}` semantic literal.

## 1. What k.Actors is for

k.LAB separates scientific information into resource, semantic, and reactivity
layers. The worldview defines what observations mean, k.IM describes how they
can be resolved, and k.Actors describes how observations and other runtime
agents behave: what they do when started, which messages they accept, what
events they emit, and how they react to events from other agents.

A k.Actors source file defines one **behavior**. At runtime, a behavior becomes an actor with:

- state initialized by an optional `init` action;
- a set of named actions that can receive calls;
- an optional `main` action run after initialization;
- access to imported k.Actors behaviors and Java actor extensions;
- an event bus through which actions can yield an interceptable value once or fire repeatedly;
- a scope connecting the actor to a user, session, digital twin, or observation.

This model supports several usages:

- reactive behavior attached to observations in a digital twin;
- session applications exposing dynamic user interfaces, executable by modular front-ends;
- reusable components that can be imported by other actors and implement UI elements;
- synchronous batch scripts;
- comprehensive test cases covering the entire k.LAB lifecycle;
- reusable traits that contribute an inherited agent personality, and action libraries;
- bridges to Java extensions supplied by k.LAB components.

The core idiom is deliberately verbal. A statement such as `timer.in(15.s)` asks the actor named
`timer` to perform its `in` action. If that action supplies or emits a value (in the example, the current time after 15 seconds have passed from the invocation), a match block after
the call states what the current actor should do with it.

## 2. A minimal behavior

```kactors
behavior examples.clock
    "Wait for a timer event and print it."
    version 1.0
    using
        core.timer as timer,
        core.console as console

action main:
    timer.in(15.s):
        time -> console.format("The timer supplied %s", time)
```

The preamble declares the behavior kind and URN, gives it a mandatory description and version, and
imports two actors under local aliases. `main` starts automatically when the behavior starts. The
call to `timer.in` installs a match action; when the timer supplies a value, that value is bound to the
`time` variable to be consumed in the following statement.

Whitespace is not semantically significant. Indentation is strongly recommended because it makes
the statement and match structure legible. Both single-line `//` and multi-line `/* ... */` comments are accepted.

## 3. Behavior preamble

The general shape of a file is:

```kactors
<kind> <behavior.urn>
    "Human-readable description"
    version <version>
    [worldview <worldview>]
    [inherits <parent.one> [, <parent.two>]]
    [with properties {<name>: <value> [, <name>: <value>] }]
    [using
        <behavior.or.extension> as <alias>[,
        <another.behavior> as <alias>]]

<actions>
```

`version` is required by the grammar. A nonblank description is required by semantic validation.
`using`, `worldview`, `inherits`, and `with properties` are optional and may occur in any order in
the preamble. Properties are freely named values interpreted by runtime conventions.

Behavior URNs are dot-separated lowercase paths. They identify behaviors to resource services and
must be chosen as stable, globally meaningful names when the behavior will be shared.

### 3.1. Behavior kinds

| Source declaration | Intended use                                                                                                                             | Lifecycle expectations |
| --- |------------------------------------------------------------------------------------------------------------------------------------------| --- |
| `behavior` or `behaviour` | A behavior normally bound to an observation, but also runnable independently                                                             | Actor-like and normally long-lived |
| `app` | A session-level interactive application                                                                                                  | Long-lived until explicitly stopped |
| `desktop app`, `web app`, `mobile app` | An application specialized for a front-end platform                                                                                      | Long-lived until explicitly stopped |
| `public ... app` | A public application declaration, available through a k.LAB service facing an authenticated user; it may also carry a platform qualifier | Long-lived until explicitly stopped |
| `component` | A self-contained composable actor created and used from another agent, commonly a UI component                                             | May initialize and run `main`; long-lived while its owner uses it |
| `script` | A synchronous batch job in a session scope                                                                                               | Expected to finish unless it starts emitter work |
| `task` | A restricted behavior attached to any observation for post-processing, documentation, or monitoring                                      | Runs in the request context; cannot modify the knowledge graph |
| `user` | The behavior instrumenting the user that owns the request                                                                                  | Exactly one instance per root user scope |
| `testcase` | A collection of actions annotated with `@test`, run under a test scope                                                                          | Runs tests in declaration order by default, or concurrently with the `parallel` property, and produces test results |
| `trait` | An inheritable agent personality contributing state and actions                                                                           | May declare `init` and `main`; both are adopted through inheritance |
| `library` | A reusable collection of callable actions                                                                                                  | Cannot declare `init` or `main` and is not started independently |

A `USER` behavior always runs in the root user scope that owns the requesting session or context.
Components and traits cannot be started through direct runtime agent creation; they are
instantiated only as imports or incorporated through inheritance.

### 3.2. Imports

Imports make actions from another k.Actors behavior or a Java actor extension addressable:

```kactors
using
    core.timer as timer,
    core.console as console
```

Every import must have a local alias. Aliases must be unique, and `self` is reserved. Calls to an
undeclared receiver are errors unless the receiver is a known actor-valued variable. Imported
actors may be resolved from connected resource services or from installed Java components.

A static action may be called directly on an imported alias. A non-static action requires an actor
instance, normally created through the runtime's `new` facility:

```kactors
tools.describe                         // static: alias call
worker <- tools.new(configuration)     // construct an instance
worker.process(job)                    // non-static: instance call
```

The same rule applies to parsed k.Actors actions and component-provided Java verbs. For an imported
k.Actors behavior, `alias.new(...)` is synthetic and passes its arguments to the behavior's
`init`. For a Java actor, resolution first tries a compatible static `@Verb(name="new")` factory
and then a compatible public constructor. An actor-valued action argument, match capture, loop
variable, or method result may also be used as the recipient of a non-static call. Calls on `self`
may address either kind because `self` is already an instance.

### 3.3. Inheritance and worldviews

`inherits` names behaviors whose actions and protected state become available to the new behavior:

```kactors
behavior examples.specialized
    "Specialize a reusable behavior."
    version 1.0
    inherits examples.common
```

Inherited `init` actions run before the local `init`. Local actions may override inherited actions;
use `@override` to make that intent explicit. Inherited actor state may be changed with `set`, but
must not be redeclared.

Every behavior kind may inherit a `trait`. Otherwise the inherited behavior must have the same
kind as its child. The two specialized behavior kinds are exceptions: `user` and `task` behaviors
may also inherit an ordinary `behavior`. For example, an application may inherit another
application or any trait, but it cannot inherit a script or an ordinary behavior.

`worldview` selects the semantic worldview used to interpret observable declarations and semantic
operations in the behavior.

## 4. Actions

Actions are the callable units of a behavior:

```kactors
action greet(name):
    console.format("Hello %s", name)

static action describe:
    return "A description"
```

An action name is a lowercase identifier. Arguments are names that may be supplied positionally or
by name at call sites. Duplicate action names and duplicate argument names are errors. An argument
may optionally carry one annotation immediately before its name. The standard `@type` annotation
adds the deliberately small amount of type safety available to k.Actors actions:

```kactors
action process(
    @type("examples.worker") worker,
    @type(urn="examples.options") options,
    @type(class="String") label,
    @type(class="java.time.Instant") timestamp):
    worker.run(options, label)
```

The unnamed string and `urn` forms require an agent handle implementing that behavior, including a
behavior derived from it. The `class` form requires a Java runtime type. A single Java identifier
matches the simple class name without regard to case, so `@type(class="boolean")` accepts a
`Boolean`; a canonical name is case-sensitive and accepts that class or a subclass/implementation
assignable to it. `class` must be named explicitly so a Java type cannot be confused with a
behavior URN.

The analyzer checks these contracts when the argument's behavior or Java type is known, including
variables produced by typed Java `@Verb` methods. Calls whose values remain dynamic are accepted
and checked when the generated action executes. Parameter annotations other than `@type` are
preserved in the semantic model for extension-specific use.

`static` controls the permitted recipient, not whether Java code happens to use a static generated
method and not whether the action is a function, supplier, or emitter. Imported aliases represent
actor specifications: they expose static actions and `new`. Ordinary actions operate on actor
instances and can use that instance's initialized state.

Annotations precede an action:

```kactors
@test
action parses_units:
    assert unit("mg/dl").space is empty
```

Annotations carry runtime conventions rather than changing the basic syntax. Common conventions
include `@test` for test actions, `@override` for inherited actions, and `@handle(...)` for actions
that handle runtime messages or scheduled events. Available annotations and their arguments depend
on installed runtime components.

### 4.1. Special action names

- `init` is the constructor-like action. Define actor state here with `def`.
- `main` runs after initialization when the behavior is started.
- Other actions run only when called, inherited, or selected through an annotation such as
  `@handle` or `@test`.

Traits may declare `init` and `main`: these participate in the inherited initialization and
startup behavior of the adopting agent. Components may also declare both because each component is
an actor with its own construction and startup lifecycle. Libraries cannot declare either special
action because they are action collections rather than constructed or started actors.

### 4.2. Function, supplier, and emitter actions

Analysis assigns every action one effective execution type (see Section 5 for the meaning of
"match" and "reactive"):

- A **function** executes synchronously and returns normally. It does not expose reactive match
  actions.
- A **supplier** eventually completes once. A `return` or `yield` executed inside a match action
  supplies its result and removes the listener.
- An **emitter** contains `fire` and may produce zero, one, or many events while its actor remains
  alive. It may use a reactive `return` to stop scheduled emissions and remove its listeners; the
  required return value is available as an exit code.

These properties propagate through calls. If `main` calls another action that calls an emitter,
`main` is effectively emitter-like too. The same applies to suppliers, including actions resolved
from imported behaviors or Java extensions. An action that both fires values and performs a
reactive return remains an emitter; the return is its cleanup/termination path and its operand is
the exit code.

The runtime uses the effective types of `init` and `main` to decide whether a started actor can
finish or must remain alive. Actor-like behaviors, applications, and components are normally
persistent; scripts are normally finite unless their effective work is emitter-like. A trait's
special actions affect the lifecycle of the agent that inherits it rather than starting the trait
independently. Libraries have no lifecycle entry points.

When an action returns or emits an agent whose behavior is known, declare that contract with either
equivalent form:

```kactors
@return("workers.specialized")
action make_worker:
    return create_worker

@return(urn="workers.specialized")
action stream_workers:
    fire worker
```

The annotation types a frame assignment produced by the action, a `for` loop variable whose source
is the action, and a single match variable or `as` capture receiving its output. Subsequent
instance calls are then checked against `workers.specialized`. With multiple destructured match
variables the output's behavior cannot identify the type of each tuple member, so those variables
remain dynamic. An action may have only one `@return`, whose unnamed or `urn` argument must be a
behavior URN. Without this annotation the result keeps its producer provenance but remains
dynamically typed.

### 4.3. Agent messages and `@handle`

Running agents communicate through messages that can cross network boundaries, keyed by globally
unique instance URNs. Each URN includes a runtime-incarnation identifier, so restarting a service
cannot reconnect a new instance to an old endpoint. Communication is bidirectional: a remote
client handle can control and message its service-side peer, agents can message other agents, and
an agent can send a message to the scope that created it. Agent handles remain ordinary
serializable beans; reconnecting a deserialized handle uses its URN rather than serialized broker
or listener state.

Custom k.Actors messages are identified by an uppercase constant. Bind an action to one exact
message constant with either form of the `@handle` annotation:

```kactors
@handle(TEMPERATURE_CHANGED)
action temperature_changed(reading, sender):
    console.format("Received %s", reading)

@handle(class=RESET_REQUESTED)
action reset(payload):
    set status READY
```

The annotation's main unnamed argument, or its named `class` argument, must be a `CONSTANT`.
Agent handles expose the resolved textual constants through `getHandledMessageClasses()`, allowing
clients and debugging tools to inspect the agent's custom-message API. The list includes inherited
handlers after override resolution and excludes reserved runtime handlers such as `@stdin`.
Runtime protocol constants cannot be claimed with `@handle`, even when `@override` is also present.
Besides the console constants, the test runtime reserves `INT.TEST_STARTED`, `INT.TEST_FINISHED`,
`INT.TESTCASE_STARTED`, and `INT.TESTCASE_FINISHED` for reporting test-case lifecycle to clients.
Use `RuntimeAgent.TestMessageType` when producing or inspecting these messages from Java.
When a matching custom message arrives:

- the runtime invokes the annotated action asynchronously using its inferred function, supplier,
  or emitter execution type;
- every declared argument except the exact reserved name `sender` receives the message payload;
- an argument named `sender`, if present, receives an agent handle for the sending URN. Messages
  sent through that handle are addressed back to the sender and identify the current agent as
  their source;
- an exception escaping the handler fails the owning agent and is reported as a lifecycle status
  change.

Handlers contributed by inherited behaviors remain active and execute against the retained
inherited behavior instance, preserving its initialized state. A local handler for the same
constant overrides inherited handlers. This produces a warning unless the local action is also
annotated with `@override`, making the replacement explicit. If multiple inherited behaviors
handle the same constant, the first behavior in the inheritance order wins.

Custom message payloads should normally use portable scalar, list, map, or other types already
supported by the runtime's Jackson configuration. Component-defined serializable DTOs are also
supported when the extension registers the same payload class on both communicating runtimes.
If a receiver does not recognize an advertised DTO class, it receives the decoded map and a
warning instead of loading an arbitrary class named by the message.

Start, stop, status request, status change, and failure are runtime lifecycle messages rather than
custom constants. Remote handles use these to control a running peer and maintain their local
view of its state. Status includes the represented observation ID (`-1` when unbound), when the
agent first started, and the latest message or reactor activity, allowing clients to calculate
idle time. A successful `stop()` call means that the stop request was sent; terminal cleanup is
confirmed by the following stopped status, after which clients may disconnect the handle.
Correlated `ask`/reply is based on the handler responding by
sending a normal message through its injected `sender` handle. The action will automatically encode an ID for the received message so that the receiving sender can recognize it as a response. 

Every behavior implicitly inherits the Java behavior `core.agent`, in the same way that every Java
class ultimately inherits `Object`. It provides the common agent contract without requiring an
`inherits` or `using` clause:

```kactors
worker <- tools.new(configuration)
worker.tell(RELOAD, configuration)
result <- worker.ask(LOOKUP, key :timeout 10.s)
worker.ask(WAIT_FOR_EVENT, key !timeout):
    response -> process(response)
console.println(worker.name(), " ", worker.urn())
```

`new` follows the construction rules described under imports. `tell` requires a message-class
constant and one arbitrary serializable payload; it publishes the message and returns immediately.
`ask` accepts the same two ordinary arguments and is a supplier: it waits for a correlated response
from the receiver. An optional temporal quantity may be supplied as inline `:timeout` metadata;
the runtime default is 30 seconds. Use the negative metadata flag `!timeout` when no deadline should
be installed. This is appropriate for the ordinary reactive form shown above: installing the
supplier listener does not block the action, and the match action simply remains dormant if no
response arrives. A matching function or supplier `@handle` action replies with its returned value.
A handler failure completes the request exceptionally. Emitter handlers do not have a single
automatic result, but may explicitly reply through their injected `sender` handle.

`name()` returns the agent's display name and `urn()` its runtime-wide instance URN. The same verbs
work on `self` and on any agent-valued variable. The runtime initializes this identity on the
generated agent and every retained inherited-behavior delegate before the agent starts.

The `core.agent` verbs are ordinary inherited actions, not reserved names. A behavior may replace
one by declaring an action with the same name; validation emits the normal inheritance warning
unless the action carries `@override`. Calls then select the local action. This is intentionally
also true of message-related verbs, providing a controlled extension point for future policies
such as authorization-aware stopping. The base `new` implementation is a construction contract:
calling it on an actor specification invokes the compiler/runtime construction path, while calling
the unoverridden implementation on an existing instance is invalid.

Messaging is available only when the scope used to create or reconnect the agent has a connected
messaging channel. Agent creation still succeeds without one: messaging is disabled and the
returned agent contains an info-level notification explaining why.

### 4.4. Interactive agent consoles

Use `@stdin` to make an action receive lines from an attached client-side agent console:

```kactors
behavior examples.console
    "A manually testable console behavior."
    version 1.0
    using
        core.console as console

@stdin
action read_line(line, sender):
    console.format("received: %s%n", line)
```

`@stdin` is shorthand for the reserved `STDIN` agent-message class and takes no annotation
arguments. The action follows the same binding rules as `@handle`: each ordinary parameter
receives the input line and an optional parameter named exactly `sender` receives the sending
agent handle. Inherited `@stdin` actions are retained; a local one overrides them.

The core `console` actor sends output to every console currently attached to the agent. It exposes:

- `print(values...)` and `println(values...)` for standard output;
- `format(pattern, values...)` and its `printf` alias;
- `error(values...)`, `errorln(values...)`, and `errorf(pattern, values...)` for standard error;
- `flush`, which flushes the local fallback writer.

An `AgentConsole` attaches when constructed with a connected client-side `Agent` handle. Its
`sendLine(...)` method forwards one logical line, `onOutput(...)` receives standard-output and
standard-error chunks, and `run(...)` provides a blocking terminal loop over ordinary Java input
and print streams. Closing the console detaches it without stopping or disconnecting the agent.
If no remote console is attached, the core console verbs fall back to the runtime's local output
stream. A bounded copy of early startup output is also retained and replayed when the first console
attaches, so output from `main` is not lost while a remote client is being created.

## 5. Calls, arguments, and event matching

### 5.1. Calling actions

Calls use a local action name or an explicit receiver:

```kactors
helper
self.helper
timer.in(15.s)
console.format("Value: %s", value)
service.lookup(key="elevation", refresh=true)
```

A naked action name addresses `self`. An explicit prefix addresses an imported actor or an actor
stored in a visible variable.

Arguments may be positional, named, or mixed as permitted by the target action. Inline metadata can
also be included in the argument list:

```kactors
button("Run" :tooltip "Start the computation" +enabled)
```

Metadata is interpreted by the receiving verb or front end; it is not a substitute for ordinary
action arguments.

The recipient of a call may also be an ordinary Java object rather than an agent. Public instance
methods are then available using their lowercase k.Actors spelling. An exact method name is tried
first, followed by `lower_underscore` to Java `lowerCamelCase` conversion. A zero-argument property
call also tries the corresponding POJO getter, so `file.absolute_path()` invokes
`file.getAbsolutePath()` and `value.empty()` may invoke `value.isEmpty()`. Setter-property syntax is
not synthesized; Java values should normally be treated as immutable unless their public API
explicitly exposes a mutating method such as `list.add(value)`.

When analysis knows the recipient's Java class—from a literal, an action parameter's
`@type(class=...)`, or a known Java return type—the compiler selects a compatible public method and
emits a direct Java call. If the class or overload cannot be established statically, the generated
code uses the same name and argument conventions through runtime reflection. This lets dynamically
obtained Java objects remain usable without weakening validation for calls whose types are known.
Methods inherited only from `Object` are not exposed through this interoperability layer.

### 5.2. Match actions

Append `:` to a supplier or emitter call to define asynchronous reactions to its outputs:

```kactors
timer.in(15.s):
    elapsed -> console.format("Elapsed: %s", elapsed)
```

Use parentheses for multiple alternatives:

```kactors
worker.run(job): (
    result -> console.print(result)
    empty -> console.print("No result")
    exception as error -> console.print(error)
)
```

A function call cannot have match actions. An emitter cannot be used where a single value is
required, such as the right side of an assignment or as a condition. A supplier may be used there;
execution waits for its single result.

`yield` in a reactor match supplies the result of the enclosing action, which otherwise defaults to the matched object. Callers may then use that
action as a supplier in assignments, arguments, and other value positions:

```kactors
action describe(key):
    worker.lookup(key): (
        result -> yield result.description()
        empty -> yield "No result"
        exception as error -> fail error
    )

action report(key):
    description <- describe(key)
    console.println(describe(other_key))
```

The reactor call remains nonblocking: `describe` returns its future immediately, and the matching
branch completes that future when it yields. A branch that does not yield leaves the action pending
unless another execution path returns, yields, or fails. The match block itself is not an
assignment RHS or call argument. In essence, `switch` and the action call match logic are similar: a `switch` statement specifies a _synchronous_ match to the returned value of the action, one of which must be executed in order for execution to continue; while a action with match reactions specifies _asynchronous_ reactions which may or may not be executed. If the action called is an emitter, the matched code may execute multiple times until the matcher expires due to a `return` or to the agent stopping. 

Current match syntax includes:

| Pattern | Meaning                                                                                                                                       |
| --- |-----------------------------------------------------------------------------------------------------------------------------------------------|
| `value -> ...` | Bind any emitted value to the `value` variable                                                                                                |
| `first, second -> ...` | Destructure sequential values into multiple local variables (completed with `unknown` when the number is higher than the arity of the result) |
| `true`, `false`, a number, quantity, or uppercase constant | Match that literal/category                                                                                                                   |
| `Type as value` | Match a runtime type and optionally capture it                                                                                                |
| `%regular expression% as text` | Match text with a regular expression and optionally capture it                                                                                |
| `{{semantic observable}} as observation` | Match an observation by semantics                                                                                                             |
| `in (one, two, three) as value` | Match membership in a set of values                                                                                                           |
| `[boolean expression] as value` | Match using an expression evaluated in scope                                                                                                  |
| `@annotation as value` | Match an annotated object                                                                                                                     |
| `unknown` | Match no-data                                                                                                                                 |
| `empty` | Match an empty result                                                                                                                         |
| `exception as error` | Match an error or exception and optionally capture it                                                                                         |
| `*` | Match a truthy value                                                                                                                          |
| `#` | Match anything, including values not accepted by `*`                                                                                          |

Names introduced by a match are local to its action-on-match. A value captured with `as` has the
same scope.

### 5.3. Concurrency and `then`

Reactive calls normally install listeners and let execution continue. Prefix a following statement
with `then` when it must wait for the preceding reactive call to supply its first value. When the
preceding statement is a group, every reactive call in that group must supply a value before
execution continues:

```kactors
(
    worker.prepare(job): ready -> console.print(ready)
    then worker.commit(job)
)
```

Using `then` without a preceding reactive call is suspicious and produces a warning. Calls used as
assignment values, conditions, `return` values, or `fire` values are also value-required and
therefore synchronize when the target is a supplier.

## 6. Values and expressions

k.Actors has literals but delegates mathematical and logical expressions to a language service.
Expressions appear between square brackets and are compiled independently, with identifiers
validated against variables visible at that point:

```kactors
if [temperature > threshold] alert(temperature)
return [value * scale + offset]
```

`self` refers to the current agent inside expressions. Other conventional k.LAB bindings may be
available according to runtime scope.

Common value forms include:

| Form | Example |
| --- | --- |
| Number | `10`, `3.14` |
| Boolean | `true`, `false` |
| String | `"hello"` |
| Quantity | `15.s`, `10.km`, `5/m` |
| Range | `0 to 100` |
| Constant | `READY`, `MESSAGES.SAY_HELLO` |
| Identifier | `temperature` |
| Semantic observable | `{{geography:Elevation in m}}` |
| Expression | `[temperature > 20]` |
| Ternary value | `ready ? "yes" : "no"` |
| List | `(1, 2, 3)` |
| Map | `{name: "sample", count: 3}` |
| Localized string key | `#WELCOME_MESSAGE` |
| Current/numbered event or argument value | `$`, `$$`, `$0`, `$1`, ... |

A semantic literal is passed to actions as a `KimObservable`, not as its textual URN. This remains
true when the literal is nested inside a list or map, so Java extensions can safely inspect its
semantics, unit, namespace, and other model fields.

A quantity literal is likewise passed as a `Quantity` retaining its numeric value, unit, and
currency. Java varargs verbs may accept zero or more values after their fixed parameters; omitted
varargs do not create a synthetic argument during parameter negotiation.

A value prefixed with a backtick is deferred. The runtime passes a reevaluatable computation
instead of its current result:

```kactors
action use_twice(x):
    console.println(x)
    console.println(x)

action calculate(a, b):
    use_twice(`[a + b])
```

Here `x` aliases the deferred expression. Each use of `x` evaluates it again using the lexical actor
scope and frame captured where the back-ticked value was created. The result is not memoized, so
expressions that inspect changing runtime state may produce a different value on each use. Passing
the deferred value through a k.Actors parameter or storing it in actor/frame state preserves this
behavior.

Deferred evaluation is chiefly useful for computable values such as expressions and ternary
expressions, giving them closure-like behavior. Deferring a literal is legal but only recomputes
the same literal. An ordinary value without the backtick is evaluated before the call or
assignment. When a deferred value crosses into a Java method, is used as an identifier, or becomes
an input binding to another expression, that boundary consumes and evaluates it. Runtime
`@type` checks are likewise postponed until the deferred argument is first consumed.

Standalone expressions accept the same backtick prefix, so `` `[a + b] `` is the normal concise
form for a deferred computation. Ternary values retain the deferred flag in the same way.

A ternary expression restricts its condition to expressions, literals and variable identifiers,all of which must evaluate to boolean. Either branch may be a literal or
expression value, a functional verb, or a functional switch:

```kactors
description <- concise
    ? strings.lowercase(message)
    : switch message (
        "hello" -> yield "A greeting"
        # -> yield [message + " (unclassified)"]
    )
```

Only the selected branch is evaluated. A supplier branch waits for its one result; an emitter is
not legal in a ternary because a ternary must produce one value.

Uppercase constants may be dot-separated paths. They remain one constant value rather than a
property lookup, which is useful for namespacing message APIs such as
`@handle(MESSAGES.SAY_HELLO)`.

Square brackets always delimit an expression, so `[1, 2, 3]` is an expression producing a list,
whereas `(1, 2, 3)` is the grammar's literal list form.

## 7. State and variable scope

k.Actors distinguishes actor state from frame-local variables.

### 7.1. Actor state

Declare actor state with `def` in `init`:

```kactors
action init:
    def count 0
    def status READY
```

Change known actor state with `set` in later actions:

```kactors
action increment:
    set status next_status()

action classify(item):
    set status switch item (
        true -> yield READY
        # -> yield UNKNOWN
    )
```

`def` outside `init`, `set` of unknown state, redeclaration of inherited state, and assignment to an
import alias are invalid. A `set` source may be a literal or expression value, a functional verb,
or a functional switch, just like a frame assignment. A supplier is joined before the state is
updated; an emitter is rejected because it cannot supply one assignment value.

### 7.2. Frame-local variables

Use `<-` for variables local to the current action or group and its nested groups:

```kactors
action report(item):
    formatted <- console.format("Value: %s", item)
    doubled <- [item * 2]
    console.print(formatted)
```

The right side may be a literal or square-bracket expression, a functional verb (function or
supplier), or a functional switch. A local variable cannot shadow actor state. Variables
introduced by action arguments, loop iteration, and match captures are also frame-local.

An `as` clause adapts the evaluated object to a named behavior before it is consumed:

```kactors
specialized <- existing as examples.specialized_worker
specialized.process(job)

return result as examples.report
fire event as examples.event

if condition as examples.boolean_adapter process
for item in source as examples.iterable_adapter process(item)
```

Adaptation is supported on local `<-` assignments, `return`, `fire`, and the selector of a
`switch`, as well as conditions and iterables in `if`/`else if`, `while`, `do`, and `for`.
The target URN may resolve to either a k.Actors behavior or a Java actor extension.

A k.Actors target declares exactly one unary adaptation action:

```kactors
@adapt
action from_record(source):
    return source
```

The action must be a function or supplier. A supplier is awaited before the `as` expression
continues; an emitter cannot be an adapter. A Java actor target instead declares one public,
non-void method annotated with `@AgentAdapter`. It accepts exactly one source parameter, may also
accept one injected `RuntimeAgent.Scope`, and may be static or instance-based. It returns the
adapted object directly or as a `CompletableFuture`, which is joined by the runtime.

The selected adapter must accept the original value's runtime type. A value adapted for control
flow must additionally be convertible to the required boolean or iterable contract. After
validation, an assigned variable is treated as an agent implementing the target behavior, so its
action calls are validated against that behavior. Adaptation does not mutate the original object;
the adapter decides whether to wrap it, derive a new agent, or reject the conversion.

## 8. Control flow and statements

Every action contains one or more statements. Parentheses create a group, which establishes a
nested frame and can carry metadata or a tag:

```kactors
(
    console.print("first")
    console.print("second")
) :name "Example group" #example_group
```

Supported control flow follows familiar forms:

```kactors
if [value > 10] console.print("large")
else if [value > 0] console.print("positive")
else console.print("zero or negative")

while [running] tick

do tick while [running]

for item in items (
    if [item == stop_value] break
    process(item)
)

description <- switch status (
    READY -> yield "ready"
    RUNNING -> yield "running"
    * -> log(status)
)
```

Conditions may be literals, identifiers, expressions, or calls. They must evaluate to boolean.
`for` iterables may be values, expressions, or calls and must evaluate to an iterable. `break` is
only valid inside a loop.

### 8.1. `switch` and `yield`

A `switch` evaluates its selector once and tests its cases in source order using the same match
criteria as a verb's match actions. The first matching branch runs synchronously. Supplier verbs
called while executing a branch are joined before execution proceeds, so the switch does not
install an asynchronous listener and escape its lexical frame.

`yield` supplies the value of the nearest enclosing functional switch, or completes the enclosing
k.Actors action when executed in a verb match:

```kactors
result <- switch input (
    number as value -> yield [value * 2]
    empty -> yield unknown
    exception as error -> fail error
    * -> console.format("ignored: %s", input)
)
```

The operand of `yield` may itself be a value or expression, a functional verb, or a nested
functional switch. The same three alternatives are accepted after `return`, `fire`, and `<-` (and
after `set` for existing actor state). 
Functional supplier calls wait for their result; emitter calls are invalid at these single-value
boundaries.

If any branch of a switch contains a yield, the switch is functional and may be used wherever that
syntax position accepts a value. A matching branch that completes without yielding gives that
switch a null/unknown result; a switch with no yield branch is statement-only. A nested switch owns
its own yields. In a verb match, `yield` classifies the enclosing action as a supplier and completes
its result when that branch runs. Callers - not the reactor match itself - use that action in value
positions.

`return` inside a switch retains the ordinary action contract: it returns from a function or
supplier action, or terminates an emitter with its exit value. It does not merely return from the
switch.

### 8.2. `return`, `fire`, and `fail`

```kactors
return result
return compute(input)
return switch input (
    READY -> yield "ready"
    # -> yield "other"
)

fire event
fire [buildEvent(self)]
fire compute_event(input)

fail "The request cannot be completed"
```

`return` completes a synchronous function, or completes a supplier with a value when executed
inside a match action. In an emitter, a reactive return stops scheduled emission and removes
listeners without changing the action's emitter type; its required operand is available as an exit
code. When an executed `return` belongs to `main`, it also terminates the agent even when the
behavior is otherwise persistent; a return inside conditional control flow only does so when that
branch actually runs. `fire` publishes an event without completing an emitter. `fail` aborts with
an optional message; failure in `init` or `main` terminates the actor.

Every `return` has an operand. This is part of the grammar contract as well as the value returned
by functions and suppliers; emitters interpret the same operand as an exit code when terminating
their reactive work.

### 8.3. Assertions and test cases

Assertions are primarily intended for `testcase` behaviors:

```kactors
testcase examples.units
    "Check unit parsing."
    version 1.0
    using
        core.units as units

@test
action parses_space_dimension:
    assert units.dimension("mg/m^3", axis="space") is 3
```

An assertion may check that a call or expression succeeds, use `is ok`, or compare its result with
a value. A bare expression such as `assert [left == right]` is a truth check: it succeeds when the
evaluated result is truthy and otherwise records a failed assertion. An explicit comparison keeps
its expected operand distinct, including an explicitly expected `null`. Several assertions may be
comma-separated and may share statement arguments. Assertions in non-test behaviors are allowed
with a warning and may be omitted from production compilation.

### 8.4. Embedded text

Text between matching `%%%` markers is an executable text statement, chiefly used by applications:

```kactors
%%%
  ## Results

  Select an observation to begin.
%%%
```

The application/front-end determines how Markdown, templates, and text metadata are rendered.

## 9. Metadata and tags

Statements, groups, calls, and annotations can carry metadata. The syntax is:

- `:key value` for keyed metadata;
- `+flag` for a positive flag;
- `!flag` for a negative flag;
- `#tag` to give a statement or group a stable local identity.

For example:

```kactors
(
    button("Run") #run_button
) :layout "horizontal" +enabled
```

Metadata semantics are conventional and depend on the receiving actor, compiler, or application
front end. Tags are especially important in applications: they let later actions address a widget
or layout element without changing ordinary variable scope. `#lowercase` is a tag, while
`#UPPERCASE` is a localized-string reference.

## 10. Major usage patterns

### 10.1. Observation behaviors

A `behavior` can be bound to observations created by [k.IM models](KIM.md), as long as the observation has _agent_ semantics. The behavior then runs with the
observation as its reactive peer, allowing it to react to scheduled events, inspect
state, communicate with other observed agents, or trigger new observations. Observations that are not agents may be bound to a `task`, which can only monitor or observe events with restrictions that reflect its non-agentic nature.

Binding belongs to [k.IM](KIM.md) rather than the k.Actors grammar. A typical k.IM model uses a `@bind`
annotation naming the behavior, and may add a selection condition. The k.LAB technical note's city example
illustrates this pattern; the current k.IM guide documents the convention and
its boundary with the grammar.

Use observation behaviors when the modeled system contains agents that engender structural change in response to events, not
merely when a value can be recomputed by an ordinary process model.

### 10.2. Applications

An `app` is incorporated into a session actor; a new k.LAB session is instantiated whenever an application is run, so that the environment it acts upon (including any digital twins created or manipulated) remain under its sole ownership. Its action/group structure describes both behavior
and, through UI verbs and metadata, a view hierarchy. In applications, UI verbs may create widgets to be rendered by a front-end interface; their emitted events
drive match actions; tagged widgets can be enabled, disabled, reset, or updated under the application agent control.

```kactors
web app examples.observer
    "Submit an observation from a browser application."
    version 1.0
    using
        core.ui as ui,
        core.runtime as runtime

action main:
    (
        ui.button("Observe elevation"):
            click -> runtime.submit({{geography:Elevation in m}}):
                result -> ui.show(result)
    ) :layout "vertical" #main_panel
```

Exact UI verbs and metadata are supplied by installed components. The group/tag/event pattern is
part of k.Actors; widget verbs and styling keys are extension APIs and must be checked against the
active UI component documentation.

### 10.3. Components

A `component` is a self-contained actor that exists in its own right but is created, owned, and
used from inside another agent rather than bound directly to an observation. Components are useful
for reusable UI panels, controllers, or reactive subsystems. Their public actions form the
component API; `init` accepts construction state and `main` starts their behavior.

### 10.4. Scripts

A `script` automates a finite batch workflow in session scope. Prefer functions and suppliers, and
let `main` return when work is complete. Calling an emitter makes the effective script lifecycle
persistent, so only do so when the script is intentionally a long-running monitor.

```kactors
script examples.batch
    "Compute one observation and report completion."
    version 1.0
    using
        core.runtime as runtime,
        core.console as console

action main:
    result <- runtime.submit({{geography:Elevation in m}})
    console.print(result)
```

### 10.5. Tasks and user behaviors

A `task` is observation-scoped like an ordinary behavior, but the observation need not have
`SemanticType.AGENT` type. Tasks run with restricted capabilities: they may post-process results,
produce documentation, or monitor resources and observations, but cannot modify the knowledge
graph. Every task can declare `main`.

A `user` behavior instruments the root `UserScope` owning the request. It can configure or react to
user-level activity independently of the session or context from which it was requested. A runtime
retains at most one user-behavior instance for each root user scope it serves. Different users may
therefore have independent USER agents; stopping or releasing one permits a replacement for that
same user to be created.

### 10.6. Test cases

A `testcase` groups `@test` actions. It runs in its own session like applications and scripts. After
inherited and local initialization and the optional `main` action have run, every local action
annotated with `@test` runs automatically in source declaration order. Supplier tests are joined
before the next test starts. Set `with properties {parallel: true}` in the preamble to launch all
`@test` actions concurrently on separate virtual threads instead; the testcase waits for every
finite test before completing. A failed test is recorded in the report but does not abort the
remaining tests or fail the testcase agent; after every test has been attempted, the finite agent
terminates normally and publishes the complete report. The tests deliberately share their agent
and its state, while retaining independent action scopes and report entries, so this mode can expose
races and exercise runtime concurrency. An absent or false `parallel` property preserves sequential
execution, and a non-boolean value is a validation error.
Use testcases for runtime services, semantic
operations, actors, and application behavior—not only pure functions. Test scopes collect action
and assertion results for later reporting. Output written through `core.console` remains visible in
the live agent console and is also retained, in emission order and with its stdout/stderr stream,
under the report for the test action that produced it. This association remains correct when tests
run in parallel because output is attributed through each action's scope. The testcase scaffolding
collects results and computes statistics that may be preserved after the testcase has completed. It
is used to exercise k.LAB complex observation behaviors against their intended results. A suite of
testcases will be made available to cover every k.LAB functionality at each release cycle.

Keep each test action focused, use descriptive action names, and prefer explicit match branches for
`empty` and `exception` when testing reactive calls.

### 10.7. Traits and libraries

A `trait` is an inheritable agent personality. It can package actions and protected state, and it
may define `init` and `main`; those special actions are incorporated into the adopting agent
through inheritance. Traits are not instantiated or bound independently. Use small traits with
clear action contracts and declare overrides explicitly in consuming behaviors.

A `library` is an importable collection of callable actions. It is not an inherited personality
and has no construction or startup lifecycle, so `init` and `main` are invalid in a library.

### 10.8. Java actor extensions

Components can expose Java classes as actors and Java methods as verbs. From k.Actors they look like
ordinary imports and calls. The runtime validator is responsible for:

- locating the component and actor class;
- matching call arguments to Java parameters;
- enforcing names, optionality, literal Java types, and agent-behavior requirements declared
  through `@Verb.Argument`; values whose runtime type or agent behavior is not yet known remain
  dynamically validated at execution time;
- distinguishing static verbs from instance verbs;
- classifying each verb as a function, supplier, or emitter;
- reporting the Java runtime class used by generated code.

A Java verb that returns or emits a known agent declares its behavior through
`@Verb(producesAgent="workers.specialized")`. Component discovery copies this into
`FunctionDescriptor.behaviorUrn`; analysis then applies the same assignment, loop, and match-capture
typing used for k.Actors `@return`. The imported alias remains the valid recipient of a static Java
verb. The produced value acquires the declared behavior type only when `producesAgent` is present;
otherwise calls on that value remain dynamically resolved.

Directly compatible arguments are matched positionally, with runtime-scope injection, primitive
numeric coercion, enum conversion, and Java varargs packing. If that match fails, the compiler
environment may negotiate the target Java parameter types against the supplied values and return
a complete adapted argument list in declaration order. This is the extension point for compound
conversions such as satisfying separate numeric and `TimeUnit` parameters from one temporal
quantity. The default component registry does not yet implement such conversions: analysis emits
a parameter-mismatch error when the mismatch is statically evident, and runtime invocation fails
explicitly when it is only discoverable dynamically.

For a Java import, the compiler binds the alias to the implementation `Class`. Runtime reflection
therefore requires an alias-selected verb to be a Java `static` method. A static `new` verb may
return an object; subsequent calls use that object as their recipient and may select its
non-static methods. Calling a non-static Java verb directly on the class alias is rejected during
analysis and is also refused by runtime method selection. k.Actors imports follow the same source
contract: static alias calls use a lazily created internal target, while `new` creates a separate
initialized behavior instance.

This boundary is what lets k.Actors remain small while exposing the full k.LAB runtime and
third-party libraries.

Ordinary values returned by those verbs may continue through the Java-object interoperability
layer described in section 5.1. List, set, and map literals are emitted as mutable Java collections
(`ArrayList`, `LinkedHashSet`, and `LinkedHashMap` respectively), so their normal public operations
can be called from k.Actors. This is separate from Java actor resolution: the value does not need an
actor descriptor, an agent behavior URN, or message dispatch unless it is actually an agent handle.

### 10.9. Core string operations

Import `core.strings as strings` for null-safe, static string functions. The actor exposes
`lowercase`, `uppercase`, `capitalize`, `labelize`, `trim`, `normalize`, `length`, `isempty`,
`contains`, `startswith`, `endswith`, `equalsignorecase`, `indexof`, `count`, `matches`, `replace`,
`substring`, `split`, `tokenize`, `join`, `concat`, `repeat`, and `abbreviate`.

`split` treats its separator literally and preserves empty fields. `tokenize` splits whitespace
while retaining double-quoted phrases. `matches` is the exception to literal matching and accepts
a Java regular expression. Every operation is a function and can therefore be nested directly
inside another call:

```kactors
console.println(strings.uppercase(strings.trim(message)))
```

## 11. Validation checklist

Syntactically valid code can still be logically invalid. Before compilation, behavior analysis
checks at least the following:

- the behavior has a nonblank description;
- imports have unique aliases and do not use `self`;
- actions and action arguments are not duplicated;
- libraries do not declare `init` or `main`; traits and components may declare both;
- calls to `self` name a known local or inherited action;
- explicit receivers are imported or are visible actor variables;
- imported aliases call only static actions (apart from the synthetic or exposed `new` verb);
- function calls do not declare match actions;
- emitters are not used where one value is required;
- calls and their arguments satisfy extension-provided validation;
- `@return` declarations contain one resolvable behavior URN;
- identifiers in values and expressions are visible in the current lexical scope;
- assignments obey actor/frame scope and do not overwrite imports or inherited state;
- conditions are boolean and `for` inputs are iterable;
- `break` occurs inside a loop;
- `then` follows reactive work worth waiting for;
- `fire` and `return` statements supply exactly one value or call;
- reactive returns in emitters retain their value as an exit code, while the action remains an
  emitter.

Warnings and errors retain source offsets and lengths, allowing IDEs and clients to place
diagnostics on the responsible code.

## 12. Running and evolution

The resources service parses a `.kactor` source into `KActorsBehavior`. The runtime service accepts
that behavior at its agent-running endpoint, analyzes it, optionally compiles it to Java, and starts
it in the requested user/session scope. The returned runtime agent can receive messages and report
status until it finishes or is explicitly stopped. When the creating scope is connected to
messaging, the returned handle's URN also identifies its bidirectional message endpoint; otherwise
the agent runs normally with messaging disabled and an explanatory info notification.

Runtime agent instances are single-use. An agent may be started once and explicitly stopped once;
after stopping it is removed from the runtime registry and cannot be restarted. Finite agents that
complete naturally may remain registered for inspection, but their existing instance still cannot
run again.

Java scope implementations may override `RuntimeAgent.Scope.setup()` to install facilities
immediately before execution and `dispose()` to release them when the root agent scope terminates.
Each hook is called at most once. Stopping an agent before it starts calls only `dispose()`.

Scopes may also override `beforeAction(actionName, annotations)` and
`afterAction(actionName, annotations)` to instrument individual action invocations. The first hook
runs after arguments have been validated and bound but before the first action instruction. The
second runs from a `finally` block after the last instruction, including exceptional and early
return paths. For supplier actions it runs when the supplier future completes, after its eventual
reactive result or failure. The annotation list is immutable and contains the semantic annotations
declared on that action. Each invocation receives its own derived scope; `getCurrentAction()`
returns the stable semantic action name on that scope and returns null on the lifecycle root scope.
Implementations can therefore keep per-action records directly in the scope without sibling or
concurrent actions overwriting one another.

Scope ownership follows the behavior kind:

- a `task` or ordinary `behavior` runs in the exact user, session, or context scope from the
  request;
- a `script`, `app`, or `testcase` receives a new private session traced from the requesting
  user's root scope. The runtime releases that session automatically when the agent finishes,
  fails during startup, or is explicitly stopped;
- a `USER` behavior runs in the root user scope that owns the request;
- a component or trait cannot be run independently.

Only tasks and behaviors may request an observation binding. A positive observation ID requires a
context-scoped request; the runtime retrieves that observation from the context's knowledge graph
and fails creation if it does not exist. The running agent exposes both the represented
observation, when any, and its exact creation scope to Java extensions through the `RuntimeAgent`
API. A source-only compile creates neither an agent nor a private session.

When called in a focused context, the runtime may bind a `BEHAVIOR` or `TASK` to the focused
observation. The runtime owns that observation; remote
handles retain only its numeric ID. `DO_NOT_BIND_OBSERVATION` forces an unbound agent. Calls made
from a user scope, such as manual runs from the IDE, remain user-scoped and do not require a
context.

The parser grammar is ahead of parts of the Java compiler, and extension-provided verb catalogs are
still evolving. When documentation, historical examples, and implementation disagree:

1. use `KActors.xtext` for accepted source syntax;
2. use the `KActors*` API interfaces and `KActorsVisitor` validation for current semantic rules;
3. use tests in `klab.services.resources` to prove parsing/adaptation assumptions with real files;
4. use `BehaviorAnalyzerTest` for semantic and lifecycle rules;
5. treat the 2021 technical note and older example projects as conceptual or migration material.

When adding a language construct, update all five surfaces together: grammar, syntax adapter,
public API model, visitor/analyzer, and real-file tests. A construct is not complete merely because
the Xtext parser accepts it.
