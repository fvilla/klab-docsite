# Groovy expressions

k.LAB expressions use Groovy by default. The public entry point is `Expression`; a
`Language.LanguageProcessor` analyzes source into an `Expression.Descriptor`, and the descriptor
compiles into an executable `GroovyExpression`.

There are two related modes of use:

1. **Stand-alone expressions** execute ordinary Groovy with variables supplied by the caller.
2. **Contextual expressions** are analyzed with the observations visible to a contextualizer. The
   processor distinguishes scalar values from observation objects and rewrites k.LAB semantic
   syntax before the scalar computation builder generates its buffer loop.

## Stand-alone use

The shortest route is through the language service:

```java
Language language = new LanguageService();

Expression expression =
    language.compile(
        "(price * quantity) - discount",
        Language.DEFAULT_EXPRESSION_LANGUAGE);

Object result =
    expression.eval(
        null,
        Map.of("price", 12.5, "quantity", 4, "discount", 3));
```

`eval` accepts any combination of maps and String/value pairs:

```java
expression.eval(null, "price", 12.5, "quantity", 4, "discount", 3);
expression.eval(null, Map.of("price", 12.5), "quantity", 4, "discount", 3);
```

Map keys must be strings and every string argument used as a key must be followed by a value.
Malformed arguments cause a `KlabIllegalArgumentException`. Additional parameters override the
default bindings of the same name.

Ordinary stand-alone Groovy that contains no k.LAB semantic literals is left unchanged. The source
is compiled once; each evaluation creates a fresh script and binding, so one `Expression` can be
evaluated concurrently. Compiled classes are transient: a serialized expression recompiles itself
on its first evaluation after deserialization.

### Scope bindings

Passing a `Scope` binds it as `scope`. A `ContextScope` also supplies these convenience variables:

| Variable | Value |
| --- | --- |
| `context` | `ContextScope.getContextObservation()` |
| `observer` | `ContextScope.getObserver()` |
| `source` | `ContextScope.getSourceObservation()` |
| `target` | `ContextScope.getTargetObservation()` |

For example:

```java
Expression expression =
    language.compile("scope.getType()", Language.DEFAULT_EXPRESSION_LANGUAGE);
Object scopeType = expression.eval(scope);
```

### Semantic literals outside contextualization

The Groovy processor recognizes a concept identifier such as `geography:Stream` and an observable
declaration enclosed in double braces such as `{{each geography:Stream}}`. They are resolved at
evaluation time through the `Reasoner` obtained from the supplied scope:

```java
Expression conceptExpression =
    language.compile("geography:Stream", Language.DEFAULT_EXPRESSION_LANGUAGE);
Concept stream = (Concept) conceptExpression.eval(scope);

Expression observableExpression =
    language.compile("{{each geography:Stream}}", Language.DEFAULT_EXPRESSION_LANGUAGE);
Observable streams = (Observable) observableExpression.eval(scope);
```

A scope with an accessible `Reasoner` service is required when either semantic literal is used.
Occurrences inside quoted strings or comments remain ordinary text.

## Analyze, inspect, then compile

Use a processor directly when descriptor information or contextual observation lists are needed:

```java
ExpressionCode code =
    ExpressionCode.of(
        "(elevation.max - elevation) / slope",
        Language.DEFAULT_EXPRESSION_LANGUAGE);

Expression.Descriptor descriptor =
    processor.analyze(
        code,
        scope,
        List.of(targetObservation),
        List.of(elevationObservation, slopeObservation));

if (Utils.Notifications.hasErrors(descriptor.getNotifications())) {
  // Report the analysis errors; do not compile.
}

for (Expression.Descriptor.Identifier identifier : descriptor.getIdentifiers().values()) {
  String name = identifier.name();
  Observation observation = identifier.observation();
  int scalarUses = identifier.scalarReferenceCount();
  int objectUses = identifier.nonScalarReferenceCount();
  List<String> members = identifier.methodsCalled();
}

Expression expression = descriptor.compile();
```

The first output is also known as `self`. Explicit inputs do not replace an output that has the
same identifier. Null observation entries are ignored.

Always inspect descriptor notifications before compiling. `compile()` rejects a descriptor with
error notifications, and invalid Groovy syntax raises `IllegalArgumentException`. Exceptions
thrown by a running Groovy script are wrapped in a `KlabException` with the processed source.

## Contextual transformations

When outputs or inputs are supplied, their stated names (or semantic code names when no stated name
exists) become known identifiers. Processing preserves whitespace, strings, and comments while
classifying each use.

Assume `elevation` and `slope` are quality observations and `river` is a non-quality observation:

| Source use | Processed use | Descriptor meaning |
| --- | --- | --- |
| `elevation` | `elevation` | One scalar use; the generated loop reads the current buffer value. |
| `elevation.max` | `elevationObs.max` | One object use; the generated code uses an observation wrapper. |
| `river` | `riverObs` | A non-quality observation is an object even when used bare. |
| `self` | `self` or `selfObs` | Refers to the first output, as a scalar or object according to use. |
| `geography:Stream` | A generated concept field | Resolved lazily through the contextual reasoner. |
| `{{each geography:Stream}}` | A generated observable field | Resolved lazily through the contextual reasoner. |
| `unknown` | `null` | The k.LAB unknown value, when contextual preprocessing is active. |

An identifier may have both scalar and object uses. For
`(elevation.max - elevation) / slope`, `elevation` reports one of each. `methodsCalled()` records
the accessed member names, such as `max`; Groovy property access and a zero-argument getter have the
same object-use implications here.

### From descriptor to scalar loop

`ScalarComputationGroovy` consumes the descriptor as follows:

1. Semantic literals become lazy fields on the generated computation class.
2. Observation dependencies become constructor fields. Repeated dependencies are wired once, and
   `self` uses the field already owned by `ExpressionBase`.
3. Every scalar quality dependency gets a typed scanner and a loop-local value.
4. Every object use gets an `ObservationWrapper`, which delegates normal observation operations.
5. The processed expression is placed inside the target scanner's fill loop.

The generated code therefore evaluates scalar values at each buffer position while keeping object
operations outside the scalar-value binding. This is why `elevation` and `elevation.max` must become
different variables.

The generated method already receives `scope`; `observer`, `context`, `source`, and `target` are
materialized from it when referenced. `scale`, `space`, and `time` are recognized as predefined
identifiers but the current scalar template does not synthesize them yet.

## Compiler options

Options are supplied to `analyze` (or to the language-service shortcut):

| Option | Effect |
| --- | --- |
| `IgnoreContext` | Do not match identifiers to supplied or scanned observations. Semantic literal processing still applies. |
| `ScanContext` | Add the observations visible from a `ContextScope`; its context observation becomes `self` when no explicit first output exists. |
| `DoNotPreprocess` | Preserve the source exactly and skip all k.LAB rewriting and identifier analysis. Use this for Groovy syntax that intentionally resembles k.LAB syntax. |

`DoNotPreprocess` also means that unquoted concept and observable literals are not valid Groovy and
must be handled by the caller.

An `ExpressionCode` parsed from scalar-forcing syntax retains its forced-scalar flag in the Groovy
descriptor. Scalar execution policy remains the responsibility of the contextual computation
builder.

## Current boundaries

- Located-observation syntax such as `elevation@S(...)` is recognized but not implemented. Analysis
  emits an error and compilation is refused, instead of producing corrupted Groovy.
- `ObservationWrapper` delegates the observation API, but aggregate properties `min` and `max` do
  not yet have storage/histogram integration. They throw `UnsupportedOperationException`; they no
  longer return placeholder numeric values.
- Automatic scalar-template bindings for `scale`, `space`, and `time` remain to be implemented.
- The processor uses the Groovy 3 lexer for token analysis while execution uses Groovy 4. Strings
  and comments are shielded from that lexer, and regression tests cover the supported
  transformations, but new Groovy syntax should be tested before it is relied upon in contextual
  expressions. `DoNotPreprocess` is the escape hatch for stand-alone code.
