# Progress yet to make

1. Extend correlated Agent#ask with cancellation propagation and richer remote failure details.
2. Provide a match syntax for a behavior using its full URN path that can match an agent's or an agent handle's
   behavior, considering also any inherited traits or behaviors.
3. A behavior's inheritance list is now made of Import objects that can carry a local name to enable using a `super`-like syntax on overridden methods. This should be supported by the compiler.
4. Provide Java @Actor definitions that apply to a known Java type (e.g. Number or String) so that a literal may receive
   messages and gets compiled into a call to the (static) verb. So `"string".substring(x)` becomes possible as long as
   the string is in a variable. These can also work with casts.

# Progress made

* Casts are now implemented syntactically for all statements with value semantics, as well as functional message calls and other functional expressions in parameter lists. 

* There is now syntactic support for the new statements `switch` and `yield` (the latter should only be used, java-like, within `switch` to serve as the functional return value of the switch). 

* Casts with 'as' are admitted in return, yield, fire, for, do, while and if, as well as after a parameter of a call, an expression or an identifier. No semantic support or translation is yet available. Switch is also used in all statement/calls that admit a value.
