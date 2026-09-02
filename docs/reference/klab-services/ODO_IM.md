# Ontology of Descriptions and Observations for Integrated Modelling (ODO-IM)

<a id="intro"></a>
## Introduction

The _Ontology of Descriptions and Observations for Integrated Modelling_
(ODO-IM) is a core ontology developed to support integrated semantic
modeling in k.LAB , a semantic web software platform for science. ODO-IM
provides ontological grounding for the scientific models produced by
modelers in k.LAB. The ontology is developed and maintained by the
[_Integrated Modelling Partnership_](http://www.integratedmodelling.org)
 in support of its commitment to
modular, distributed, semantically explicit, and integrated scientific
computing and modeling. The modularity of ODO-IM is achieved through a
series of decomposable knowledge-bases that allow for extensibility and
reusability according to the [FAIR principles](https://www.go-fair.org/fair-principles/) - Findable, Accessible, Interoperable, and Reusable.

ODO-IM is an ontology of scientific observations and the scientific
descriptions of such observations; the ontology assumes a
phenomenological, descriptive, and linguistic perspective and, like
other ontologies (e.g. the _Descriptive Ontology for Linguistic and
Cognitive Engineering_ (DOLCE) ), remains agnostic concerning the
metaphysical status of the world in a fundamental sense. In this
ontology scientific observations are interpreted and defined as
contextual relationships between two entities, an _observer_ and an
_observation target_, which could be a physical object and an event.
This type of observation relationship needs to be constrained within the
current scientific practices that (very) often employ scientific
artefacts, such as datasets and data models, to carry out observations.
What ODO-IM postulates is that:

____
scientific products and explanations result from observations that are
based on perspectives, including scales and contexts.
____

For this reason, ODO-IM is concerned with the definition of Observable
concepts, Predicates that specialize Observables, and the Descriptions
of the scientific processes that produce scientific artifacts. Note that
ODO-IM does not explicitly mention the distinction between universal and
particular that is often integral to foundational ontologies , such as
in the _Basic Formal Ontology_ (BFO) and the _Unified Foundational
Ontology_ (UFO) . While a commitment to universal and particular is not
part of ODO-IM, _concrete_ and _abstract_ categories are implicitly
included; indeed Observables and Predicates abstractions which can be
concretized to compute an `observation`. For example, when a
scientific description invokes a countable observable, such as an insect
or a plant, the concept is `reified`. The inclusion of the
concrete-abstract distinction is implicit because there are no
super-classes for `concrete` or `abstract` entities in the ontology.
Instead, those emerge when a scientific description is identified and
realized by the system. In this sense, a concrete entity is considered a
_token_-instance, while its abstraction is analogous to a _type_ . For
example, the `Elio` is the token-instance of the type CAT.

The three backbone categories of ODO-IM are (i) Description, (ii)
Observable, and (iii) Predicate (see Figure #fig:backbone[1]
representing the conceptual model the ontology). The ontology builds
upon the _Provenance Ontology_ (PROV-O) that aims to trace origins and
changes of information and thus are crucial for representing scientific
knowledge. (i) Description captures the activities that produce
scientific artifacts derived from contextualized observations.
Sub-classes of Description can be used to describe the scientific
assertions that incarnate Observables into observations within a
context, such as models and computational workflows. (ii) Observable are
concepts that serve as the object of a scientific Description and
provide the basic semantics for the resulting observation. (iii)
Predicate can be combined to Observable to create restrictions on the
meaning of the Observable.

**image**  general.png[The ODO-IM conceptual backbone]

As anticipated, in ODO-IM, scientific observations are
phenomenologically-driven and dependent upon perspectives, contexts, and
scales, which means that the observer can decide the focus of the
observation, then its description, on _structural_ aspects (i.e.
continuant-like object) or _functional_ aspects (i.e. occurrent-like
object). For this reason we do not commit to any specific foundational
ontology that would bind the whole project to one worldview (for
instance notions of continuants and occurrents, or particulars and
universals).(Note: See for a general overview of foundational
ontologies and their applications.] Each observation can be made under a
static (structural) or a dynamic (functional) perspective. This imply
that in ODO-IM the viewpoints of the observers and the ``x
qua'' Observable have ontological priority over the classification of
entities beyond the observation context.

<a id="prov-mod"></a>
## From provenance to semantic modeling

ODO-IM captures the scientific process following the standard provenance
terminology and provides constructs that enable explicit semantics into
the provenance model of PROV-O, building the conceptual foundation for
the semantic web of scientific observations implemented in k.LAB. At the
core, the scientific process is seen as the transformation of existing
knowledge artifacts into others that incorporate and define scientific
advancement; such transformations are enacted by _agents_ as scientific
_activities_, such as measurement, symbolic integration or numeric
simulation, under the guidance of _plans_ representing the `script`
for the transformation and incorporating the scientific hypotheses and
methodologies guiding the process. These artifacts, agents, activities,
and descriptions have direct counterparts in the PROV-O concept
hierarchy, namely: _entity_, _agent_, _activity_ and _plan_.

To enhance the provenance model with an explicit observational
grounding, we must recognize that any scientific artifact reflects a
chosen `overall` entity of the world, providing the spatial and
temporal aspects for successive observations. Therefore the first step
of any scientific activity is the choice of a _context_ of reference,
including its identity (e.g. a model organism, a region of space) and
the required granularity of description for any successive observations
in it, such as the representations of time and space (_scale_) adopted
for the observation. With this in mind, ODO-IM extends the fundamental
PROV-O classes as follows:

* *Resource* is the ODO-IM sub-class of PROV-O _entity_, representing
any communicable, storable artifact that embodies scientific knowledge -
such as a dataset, report, or equation. Resources are always
semantically characterized by the concept they describe (the Observable)
and are intended as directly `actionable`, i.e. machine-readable in
all their parts and implications with no human intervention.
* *Contextualization* is the ODO-IM sub-class of PROV-O _activity_,
representing the production of a Resource (using zero or more other
Resources) and recognizing that a Resource that serves as _context_ must
be provided (i.e. acknowledged) by the observing agent to bootstrap the
process.
* *Description* is the ODO sub-class of PROV-O _plan_, which links a
semantic statement (the Observable) to a computational strategy to build
the Resource mentioned above that represents it - the k.LAB software
stack defines an AI-driven process that finds, connects, and uses
Descriptions from a networked, distributed repository to respond to
logical queries of the form `observe _observable_ in _context_`.

Based on these definitions, ODO-IM grounds a conceptual model to
facilitate:

. the definition of Observable concepts and their combinations through
semantic operators and Predicates that intuitively capture complex
meanings and linguistic distinctions commonly adopted in day-to-day
scientific practice;
. the definition of scientific methodological `recipes` (_models_) as
Descriptions that have Observables as inputs and outputs, representing
the synthetic statements of scientific methods that are typically only
expressed as non-directly actionable artifacts, such as equations in
scientific articles or complex computer code.

The conceptual architecture of ODO-IM is not used directly by
practitioners but is instead perused by writing statements in the
_knowledge-Integrated Modeling_ language (k.IM) [more information
forthcoming). k.IM is supported by the k.LAB software stack and defines
ODO-IM compatible axioms using syntactic rules and conventions closely
modeled on the English language. The use of k.IM facilitates semantic
annotation and makes the building of integrated semantic web
applications accessible to the largest possible set of practitioners.

<a id="core"></a>
## ODO-IM core elements

ODO-IM core ontology has been designed to capture scientific
observations encompassing complex epistemological dimensions of
discovery, classification, and conceptualization of entities based on
several activities, such as measurements and evaluations. Scientific
observations are themselves informational artefacts , typically encoded
and stored in physical supports, and represent a particular state of
affairs based on the perspectives, goals, hypothesis, knowledge, and
capabilities of the observer(s). Consequently, observations are
cognitive abstractions guided by empirical and scientific practices
.Yet, the label `observation` carries an ambiguity that lies between
its meaning in terms of a type of activity (`doing an observation`)
and a type of information, i.e. a _content_, that can be replicated,
copied, transcribed, and analyzed to create more content.(Note: An
up-to-date review of information entities in ontologies is presented by
Sanfilippo .] Thus it is important to remark that in k.LAB scientific
observations are formal contextualized information/semantic content and,
in this regard, scientific observations cannot exist without a context
(and one or more observers).

Observables and Predicates are abstract concepts(Note: Here
`concept` is intended as `type` rather than `universal` .]
employed to describe scientific observations that can be computed
according to a Description to produce a Resource. A Description provides
a plan to contextualize an observation into a Resource that represents
it within a spatio-temporal and semantic frame of reference that
provides a context for its computation (the Description that produces
the context itself is a specialized sub-class of Description,
Acknowledgement - i.e. `commitment`, whose computational aspects are
trivial). The next sections illustrate the main components that
constitute a scientific observation description in k.LAB, namely
Observable, Predicate, and Description and their associated definitions.

### Observable

The notion of _observable_ has been debated for a long time in several
academic literature. In physics, in which probably the standard
definition of observables was proposed, an observable is a physical
measurable property , such as temperature and mass. In philosophy, the
`nature` of observables was the object of discussion, in particular by
logical empiricists who attempted to distinguish and define different
aspects of the scientific practice, such as sensory/perceived objective
evidence and unobservable theories . Despite the efforts in defining
observables, especially in the philosophical corpus, what can be
accounted as such has been the object of disagreement. For example, are
observables only entities that can be `directly` observed through the
perception, or should we include in the catalog of observables also
entities that are observed or measured through the mediation of more or
less complex technologies, such as a thermometer, a water monitoring
buoy, satellite observations, and a magnetic resonance imaging (MRI),
and if yes, how the observations derived from complex technologies are
connected with their `unobservable` preconditions based on articulated
theories ? Recently it has been suggested that perhaps the idea of
observations conceived in the old-fashioned way is not any-more
appropriate and useful . Leaving aside (i) the strict `direct` versus
instrumentation-mediated observability issue, which it has been
partially surpassed also due to the contemporary over-reliance of
technology in most of the scientific fields, and (ii) the philosophical
literature that argues in favor of a broader and often pervasive role of
technology in our lives, such as for postphenomenology , a more modern
reading of `observables` is through empirical/observation _data_ , and
to extend observations from direct empiricism to a more complex
interpretations .

The relation between _data_ and _phenomena_ has been discussed in a
seminal work written by Bogen and Woodward , in which data is described
as an observable evidence for the phenomena - although data cannot be
explained by theories - the phenomena is instead rather unobservable and
accessible through data, yet theories explain phenomena and not data
(pp. 305-306). This view has been re-elaborated by Votsis , who
considers data as evidence for theories when auxiliary hypotheses are
adequately employed. In a clarification of the work of Bogen and
Woodward, Teller offered a contemporary analysis of the `phenomena`
following the hierarchical structure of models proposed by Giere in
which the relations between world, data, theories, and models are
articulated. In particular relevant for our discussion is the idea that
physical quantifiable qualities that are included in models(Note: In
this writing we will not discuss the different kinds of models presented
in Giere .), such as mass, temperature, and weight, are (i) interpreted
and contextualized within the scientific `enterprise`, and (ii)
related to real-world entities to provide the basis for further
interpretations .

In the context of k.LAB the dichotomy between data and phenomena, and
observable and unobservable is somewhat unnecessary since scientific
observations are, as already mentioned, information entities derived and
elaborated through hypothesis and contextualization of other scientific
artefacts (e.g. datasets, data models, and images) taken as
phenomenological evidence and interpreted based on scientific
humanly-driven perspectives , perspectives that are also domain-based .
Thus ODO-IM Observables, with the capital O that refers to the concept
`observable`, are central elements for describing observation and are
defined as abstract concepts that represent entities that can be
observed through the mediation of scientific artifacts, such as physical
objects, processes, and qualities. Examples of Observables are `city`
and `land cover type`, which are classified according to ODO-IM as
`subject` and `quality`. Note that in ODO-IM Observables are agreed
upon and negotiated within scientific communities and should be also
negotiated beyond them in a transdisciplinary effort. In the following a
description of the main Observable's concepts is provided, more
specifically: (i) _countable_, (ii) _process_, (iii) _quality_, and
_configuration_ (see Figure #fig:observable[2]).

**image**  observables.png[ODO-IM taxonomy of Observables]

#### Countable.

In philosophy, countable entities are often called
_sortals_.(Note: See the `Sortal` for a richer and articulated
review .] countable can be identified as individuals carrying a
principle of _identity_ and having _unity_, then countable are wholes
having boundaries , i.e. temporal/spatial/conceptual. So when we refer
to countable, we answer the question `How many x are
there?`, for example, how many people and lakes are in a certain
region? In k.LAB countables are reified by _instantiation_ Description
and are organized into: (i) _substantial_, (ii) _event_, and (iii)
_relationship_.

* A substantial (here adopted in a similar fashion of UFO and DOLCE ) is
a concept that captures endurant-continuant like entities, such as
`lamb`, `mountain`, and `person`. Substantials, which are often
understood with the less technical term _object_, describe entities that
endure in time by being wholly existent and bear qualities. In k.LAB
only substantials can determine the context for observations; indeed the
first Resource in any scientific process modeled according to ODO-IM
must be acknowledged (i.e. explicitly declared). Thus, despite the
assumed observational perspective (structural-functional), this aspect
manifests the overall ontological priority of substantials over
non-substantials, such as events and processes. _Subject_ and _agent_
are sub-classes of substantial, while the latter carries agentive
characteristics, i.e. intentionality , the former does not.
* In the ontological literature, events are typically classified as
perdurants/occurrents (e.g. ), which corresponds to event instances,
i.e. tokens, that happen in time, are composed of temporal parts, and
involve participants . However, in the case of ODO-IM, events are
Observables inheriting their abstract-type `repeatable` or
`reusable` characteristics. The notion of _repeatability_ has been
analyzed by Galton in the context of processes as abstract patterns ,
ODO-IM adopts a similar view for events in which those are cognitively
salient abstract scripts that can be reused to described and give
structure to one or more qualitative change in substantial Observables.(Note: Although each of these accounts of events present analyses
relevant for ODO-IM, nevertheless, these works are not entirely adherent
with events described in ODO-IM. In particular, in the recent paper of
Guarino et al., , the examination of events from a metaphysical and
semantic perspective is way more detailed and refined than the one
provided in ODO-IM in which, for example, at this stage of development,
interpretations of modifiers are not provided, and the description of
the individual (token) qualitative changes is not relevant for our
current discussion.] The idea of events as abstract scripts is inspired
by the influential paper of Schank and Abelson , in which scripts are
descriptions of a series of contextualized events where participants
play roles. Many of the scripts considered in refer to planned
intentional events; however in the context of current k.LAB
applications, events are also natural and thus might be generated
outside human interventions. ODO-IM events are identified by (i) their
temporal boundaries, a start and end point (over a time interval ) which
limit the time-span of the event in a cognitive relevant interval, (ii)
the presence of substantials that participate to the events and exhibit
changes, and (iii) as being _made_ by processes (this aspect of event
has also been called durative ), for example, the event `season` is
made by processes such as `precipitation`. The relation between events
and processes opens the debate concerning the level of description of
those concepts; this is discussed below when we introduce the _process_
construct. Examples of events are `birth`, `conference`, and
`wildfire`; considering the latter (i.e. `wildfire`), the
qualitative change is described, for example, as the water vaporized
from the vegetation.
* A relationship(Note: In this writing, we do not engage in the
discussion concerning the difference between `relation` and
`relationship` .] is a countable concept directionally connecting two
substantials. Relationships in ODO-IM are _structural_ and _functional_
whether the observerâ€™s focus is on static or dynamic aspects of the
relationship. Structural relationships between two substantials (relata)
allow another substantial (relator) to emerge. Note that the connection
between two relata is what allowed the relator to emerge, i.e. to be
observed, an interpretation that is inspired, although with some
significant differences from Guarino and Guizzardi .(Note: Among the
most prominent differences, in the work of Guarino and Guizzardi , the
connection between the relata (for the author the `relation`) is
derived from the relator that is what bound the relata being its
truthmaker. Instead in ODO-IM the relata is dependent upon the
relationship itself.] For example, `city A is connected to city B`
generates the subject `road` that links the two cities. Focusing on
functional relationships, those generate events, for instance, the
functional relationship `skier using a mountain (for recreation)`
comprises interaction(s) between the subject skier and mountain, which
generates for instance the event `ski slalom`. So structural
relationships engender or define subjects (e.g. parenthood between human
individuals engenders families) qualities bearer, and functional
relationships engender/define events that are composed of processes.

#### Process.

As mentioned before, events and processes are connected as the former is
composed of the latter. One of their linkage examined in the ontological
literature that is pertinent to ODO-IM is the perspectival nuances that
involve the events and processes descriptions . While events are
countable boundary objects, processes are described as open-ended and
homogeneous . In addition, processes are described as experienced
dynamically at a certain time, while events are historical records that
can be remembered . Both event and process are involved in changes, for
example, the former triggers something else, such as another event, and
changes occur to its participants (`change of state` ), the latter
perpetrates those changes in a `state of change` mode. Thus
while `storm` and `earthquakes` are events with a start and
termination points, `pollination` is an ongoing course that is
described with a focus on its on`going interactions or affects. Processes
in k.LAB are realized through _simulation_ Description.

#### Quality.

Observable qualities require an intermediate entity to produce a
Resource that represents it, e.g. a `reference` is needed to carry out
a measurement. In this regards, the intermediate entity, for example a
substantial, bears quality, or from the other way around, qualities are
inherent to the intermediate entity . For example `temperature` cannot
be measured without a reference entity, such as water, atmosphere and a
substantial body. In addition `temperature` can be measured only in
reference to a conventional unit or other numeric scale in order to
produce a quantifiable outcome, such as `25 degrees Celsius`.

The hierarchy of quality is organized following the sub-classes of (i)
_contextual_, (ii) _presence_, (iii) _enumerable_, and (iv)
_quantifiable_. (i) Contextual quality defines _spatial_ and _temporal_
aspects of a description providing its context. Both are required to
frame the scale in which a description is given. From a phenomenological
point of view, the experience of time involves factors that range from
duration to granularity, ordering, and change ; nevertheless, ODO-IM
focuses on the informational representation of time as a quality that
defines the granularity and extent of a description. Following this
target, in this ontology, time is treated as a way to capture temporal
features such as the duration of an event and change over a specified
_interval_ of reference, for example, months or years . Spatial
qualities are also accounted for with a similar topological description,
noting important differences compared with temporal qualities, for
example, variable dimensionality. The notions of extent and granularity,
as well as operations such as union and intersection, are similar in
both dimensions and can be accounted similarly. In ODO-IM spatial
characteristics are represented in terms of regions of space that can be
associated with intervals to create temporal and spatial notions. In
addition to space and time, other dimensions may be used to account for
conceptual topologies (e.g. a multi-hypothesis space) over which
observed states. Consequently the representation of Resources may be
distributed.

While (ii) presence specifies the existence of the quality itself, a
semantic equivalent of a boolean â€œtruth value", (iii) enumerable quality
defines the quality on based on a resemblance with others of its kind,
thus providing quality classification. Differently from the other
qualities, (iv) allows for the expression of more fine-grained
measurable qualities by referring to a unit of reference or fractions
and therefore is, assigned to a numeric value when an observation is
concretized, e.g. volume and mass. Thus quantifiable qualities refer to
all those qualities that can be quantified and are contextualized by
_quantification_ Descriptions and includes several sub-classes ranging
from _continuous numerically quantifiable quality_, which includes
important notions such as physical property and probability, to _value_
that specifies monetary and preference qualities referencing a specific
value attribution and trading system (see e.g. ). Continuous numerically
quantifiable quality are divided into: _physical property_,
_probability_, _relative quantity_, and _uncertainty_.

* Physical property is contextualized by _measurement_ Description and
classifies qualities of physical entities, such as substantials.
Physical properties are divided into _extensive_ and _intensive_; while
extensive physical properties are influenced by the physical structure
of the inhered entity, the same does not hold for intensive physical
properties.(Note: For more details see the _IUPAC Compendium of
Chemical Terminology_ and
https://en.wikipedia.org/wiki/Intensive_and_extensive_properties.]
Examples of the former are _volume_ and _length_, instead of the latter
_temperature_ and _duration_.
* Probability is the measurement of the likelihood of occurrence of
`favorable events` that is contextualized as a _probability
description_. Probability has one sub-class, called _presence
probability_, that frames the probability focus on subjects in a certain
context.
* When a quality requires another (compatible) quality to be assessed is
called _relative_ and has a similar semantics as `integral` qualities
in the conceptual spaces theory, which mentions the example of hue and
brightness when considering the color of an object . _Ratio_
(contextualized by _ratio description_) and _proportion_ are sub-classes
of relative quantity.
* The last continuous numerically quantifiable quality is uncertainty;
as mentioned by Floridi , the scientific literature provides several
definitions of uncertainty, such as in physics, mathematics, statistics
and epistemology, yet generally speaking uncertainty can be defined as
partial epistemological content (i.e. information) concerning a state or
a result . In ODO-IM, uncertainty is contextualized by _uncertainty
description_ and is treated as a quantifiable quality that can be
assigned to a description, with no further assumption about the method
of measurement or range of values.

Besides continuous numerically quantifiable, other sub-classes of
quantifiable qualities are _numerosity_, _priority_, and _value_.

* Numerosity defines the number of countable things in a group and is
contextualized by the _counting_ Description.
* Priority describes a monotonic ordering of concepts that is
contextualized in terms of a numeric _ranking_ Description.
* Finally value(Note: We acknowledge the abundant and complex
literature on values, particularly the philosophical one, see e.g. .
Yet, in ODO-IM, the value concept has a less ambitious purpose defined
within its quantification scope.] is a quality assigned to an entity by
a subject, typically an agent, based on specific criteria. Value in
contextualized by _valuation_ Description. In ODO-IM values can be
either _monetary_ or non-monetary (expressing on a _preference_)
following the ecosystem services classification of values . The
assignment of value is expressed as a priority, i.e. abstract ranking,
based on the characteristics of the valued entity and can potentially
change over time .(Note: The paper of Porello and Guizzardi treats
preferences as ternary relations, here we consider unary predicates as
the agent making the valuation is always explicitly known in k.LAB and
contextual to any observation made.]

#### Configuration.

The last Observable in this list is configuration, which presents
conceptual and operational differences compared with other ODO-IM
concepts. Indeed configurations are somewhat external to the userâ€™s
control since these constructs cannot be directly introduced while
modeling and can only be created by the system through a _detection_
Description. Configurations represent emergent patterns that are
generated by observations of quality and relationship concepts.
Configurations are dependent upon the observer that decides the focus on
particular aggregations. For example `social network` is a
configuration that emerges from the functional relationship ``social
connection''.

#### Ontological analysis of some Observables.

As mentioned in Section link:#intro[1), ODO-IM undertakes a
phenomenological, descriptive, and linguistic ontological position of
scientific observations. In particular, scientific observations depend
upon perspectives, more precisely structural and functional, and
Observable concepts `live` in context, which signifies that
Observables are observed not in isolation but in relation to each other,
allowing the identification of further ontological constraints. Once the
focus shifts on the relationships between Observables both
(a) _patterns of dependence_ and (b)
_presence of arity_. Both a and b are
connected; while the former specifies whether the Observable is
dependent upon another (based on the observation perspective), the
latter defines absence or presence of dependence and, in case of
presence, its numerosity. Although the ontological literature includes
several other meta-ontological properties , here we focus only on
dependence (and its arity) as it is the most pertinent due to the
observational purpose of ODO-IM.

More specifically, (i) _substantials_ and _events_ are the only
Observables that can be considered as guiding perspectives for an
observation, either structural if the focus is on the substantials as
the main context or functional when an event is the primary context of
the observation. In this sense, when an observation is described,
substantials and events are independent bounded observables that can be
assumed as guiding perspectives for an observation, either structural or
functional, respectively. Note that when the observer decides to perform
a structural observation, the context is bound to a substantial one, and
events can become dependent upon substantial participants; the opposite
situation is instead manifested when events are selected as the primary
context.

While substantials and events have an arity of dependence for their
observability equal to 0 in their corresponding observational
perspectives, (ii) _qualities_ and _processes_ always inhere and are
dependent upon other Observables, meaning from any standpoint,
exhibiting an arity of dependence \geq 1. Indeed while
qualities inhere to substantial, processes do to events. Finally, (iii)
_structural_ and _functional relationships_ are dependent from both
their target and source (i.e. = 2) to be observed and conceptualized as
countable. Table #table:table1[1] summarizes the aforementioned points.

<a id="table:table1"></a>
| | |*Observation perspective* ||
|---|---|---|---|
|*Arity of dependence* |*Dependence* |*Structural* |*Functional*|
|`0` |No |Subject |Event|
|`1` |Yes |Quality |Process|
|`2` |Yes |Structural relationship |Functional relationship|

### Predicate

In ODO-IM, Predicates are abstract concepts that (i) cannot be directly
supported by scientific observations and (ii) provide a linguistic tool
to characterize Observables further. For example, important uses for
Predicates are to describe more specific qualities that often cannot be
observed, only attributed, e.g. color in substitution of ``reflected
wavelength'' of an object, and to define arbitrary discrete scales, such
as `very short`, `short`, `tall`, and `very tall`.

Broadly speaking, predicates are often considered the linguistic
counterpart of _properties_ identifiable using the copula `is` in
sentences as `x is P` . This association between the predicate and the
`is` generated semantic vaguenesses, summarised by the so-called
Frege-Russell ambiguity thesis citing Villko and Hintikka , in which
`is` carries multiple meanings, namely _predication_, _identity_,
_existence_, and _subsumption_. Long ago, this issue has also been the
object of debate in knowledge representation and formal ontologies;
notable are the works of Brachman in semantic networks , and Guarino and
Welty on identity and subsumption . ODO-IM mitigates some of the
ambiguities mentioned above by recognizing the difference between
Predicates that describe general aspects of
the Observable, their physical *location*, their
contextual involvements, and finally some Predicates
categorize epistemic dimensions of the
Observable. (Note: the organization of Predicates in ODO-IM
resolve mostly the ambiguity between general predication and identity.]
Predicate category includes (i) _attribute_, (ii) _realm_, and (iii)
_role_, the latter (iv) _domain_ and (v) _identity_ (see Figure
#fig:predicate[3]).

* Attribute is the most generic Predicate that can be used to specialize
Observables. Attributes describe inference to Observable in the
following ways: (i) as capability or disposition of the Observable, such
as `reproductive`, `human visible`, and `pervious`, (ii) as states
or phases of Observables that have been reached or are ongoing, such as
`pollinated`, `irrigated`, `adult`, and finally (iv) as subjective
_ordering_ by defining non-quantitative rankings to be attributed to
Observables, such as `severe`, `mild`, `hot`, `damaged`.
* Realm restricts the physical location of an Observable, for example,
the temperature of the `atmosphere` or the amount of soil in the
`soil stratum`. This predicate can be intended, in a similar fashion
to that of realms included in the International Union for Conservation
of Nature (IUCN) , as parts of the biosphere which are divided into
terrestrial, subterranean, atmospheric, marine, and freshwater.
* Role is a dependent and contingent Predicate that is played by other
entities and is bound to a context. The same entity can play multiple
roles simultaneously in different contexts without affecting its
identity or core semantics. Note that role is different from other
predicates because it describes external characterizations of
Observables (contexts), for example, an insect may be a `pollinator`
in one particular ecosystem but not in another.

While the Predicates mentioned above specify either traits that are
contextually or non-contextually ascribed to Observables or the location
where Observables are placed, _epistemic predicates_ have the function
of explaining Observables either based on (i) their domain of
application or (ii) categorization established within scientific
communities following some of the accounts proposed by the so-called
`philosophy of science approach` .(Note: Here we extend the idea of
`natural kinds` and their explanatory and inductive roles in science
to other kinds or classifications, such as for artifacts and domains of
knowledge . Note that the explanatory and inductive relevance of
`natural kinds` is central to the positions assumed by Boyd , which is
far more articulated than our exposition of epistemic Predicates in
ODO-IM [#f1]#[f1]#.] Domain Predicates assign Observables to a
scientific discipline using domain-specific ontologies as reference; for
instance, the Observable quality `elevation` belongs to the
`geography` ontology. Focusing now on the most challenging Predicate,
i.e. identity, this concept has been widely discussed in ontology and
metaphysics , and it is outside the scope of this technical report to
address its vast and diverse literature;(Note: In the context of
applied ontology and conceptual modeling, Guizzardi and colleagues
proposed an analysis of the so-called `Powertypes`, i.e. types having
instances that present both types- and instances-like aspects.
Powertypes exhibit similarities with ODO-IM identities that should be
further investigated in the future.] thus, for this analysis, the aim is
to propose a description of identity as meant in ODO-IM and for its use
within k.LAB software. Identity in this ontology represents abstract
classes of entities with unique identifiers that are grouped (i.e.
classified) based on cognitive relevant aspects, normally subsuming a
large number of characteristics, such as morphological, functional, and
behavioral, for example, concepts that belong to the kingdoms of
animalia and plant, the classification of rocks, and artifacts. To give
a more explicit example, the concepts belonging to the taxonomy of
marine mammals, e.g. cetaceans and pinnipeds, are identities in the
ODO-IM sense. In k.LAB, identities play an important role and are
managed through what in the system is called _authority_ , following a
strategy to link concepts with referenced external terminologies (e.g.
IUPAC for chemistry ), thesauri (e.g. the FAO AGROVOC ) and information
providers (e.g. the Global Biodiversity Information Facility (GBIF) ).
An example is the identity `water` that associates the meaning of
water in reference to the IUPAC classification .

An interesting final consideration concerning epistemic Predicates is
their recursive aspect; indeed, both domain and identity represent
categorization systems in a taxonomical fashion that, in a simplified
way, correspond to simplified ontologies within the ontology ODO-IM. In
other words, epistemic Predicates are themselves kinds of ontologies,
more specifically taxonomies. In addition, as mentioned in footnote
link:#f1[[f1]), epistemic Predicates have explaining and inferring
functions. In particular, the former, i.e. _explainability_, is a
characteristic that recently Guizzardi and Guarino have been attributing
to the role of ontologies and ontological analysis for domain models,
including in the context of scientific practical explanations (e.g.
goal-based explanations), an aspect that should be further analyzed also
for epistemic Predicates.

**image**  predicate.png[ODO-IM taxonomy of predicates]

### Description

The main concrete element of ODO-IM, except for Resource that is derived
from the PROV-O , is Description (see Figure #fig:description[4]). It
defines one or more Observable aspects within a scale of observation
through a `recipe` that creates a Resource that represents it in the
selected spatio-temporal context. In ODO-IM Description is a _plan_
(PROV-O entity), the latter denotes a set of activities performed by an
agent for a purpose . Although often in literature plans have been
defined as types of descriptions , ODO-IM descriptions are specific
plans, specialized according to the Observable, that define a set of
ordered activities undertaken by the system to produce an outcome, i.e.
Resource. More specifically, Descriptions are derived from the
Resource-in-input and Resource-in-output processes.

As outlined above, Descriptions interface with Observables by providing
a strategy to contextualize them, thereby setting the conditions for
Observables to be observed, thus to exist . Observables do not have
temporal or spatial characteristics, yet Descriptions facilitate the
concretization in context of Observables when invoked. The category
Description is divided into three first-level sub-classes: (i)
_instantiation_, (ii) _resolution_, and (iii) _detection_.

* *Instantiation.* This Description reifies concepts, specifically
countable, by building the Resources that incorporate them into concrete
token. In this way, instantiation creates concrete concepts. The
sub-classes of instantiation are _acknowledgment_ and _connection_; the
former consists of the intention/commitment to generate the concept and
directly specifies all details of the outcome. The first step of any
scientific process is acknowledging one instance that serves as context
for the remaining activities. The latter, connection, contextualizes
relationships.
* *Resolution.* This type of Description explains the concept through
its process realization based on a scale: while instantiation only
produces a concept at time t by invoking it, resolution
initiates a modeling process that results in a corresponding outcome.
* *Detection.* This class contextualizes a configuration and can produce
a model resolution.

Resolution, which describes the explanation of a previously instantiated
observable, is further articulated as _simulation_ and _state
attribution_; the former is applied in the context of a process, the
latter is a concept container that includes all Descriptions that
attribute `values` when applied to: _classification_, _quantification_
and _verification_. These three sub-classes of state attribution apply
respectively to (a) enumerable qualities (whose attributed values must
be concepts subsuming a specified conceptual space, e.g. soil types),
(b) quantifiable qualities whose values are numeric, and (c) presence
that can be asserted by means of simple truth values (true/false).

**image**  description_final.png[ODO-IM taxonomy of descriptions]

Quantification is the most articulated, presenting the following
subsumed elements(not included in Figure #fig:description[4] for reasons
of space): (i) _counting_, (ii) _measurement_ (iii) _probability
description_ (iv) _ranking_, (v) _ratio description_ that expresses a
relationship between two or more numerical quantities that produce
another number as an outcome, (vi) _uncertainty description_ which uses
numerical data to express the uncertainty concerning another state, and
finally (vii) _valuation_ that produces a numeric estimate of the
"worth" of an entity in a given context and perspective.

<a id="appendix_a"></a>
## PROV-O classes

An extensive description of the PROV-O elements can be found in , in
this work we simply report the PROV classes that we included, which are:
_activity_, _entity_, _agent_, _instantaneous event_ and _role_ (and
their sub-classes). Two remarks on __entity__ (Note: the
PROV _entity_ is conceived as a synonym of artefact/informational
object.] are necessary. First we added Description as a sub-class of
_plan_ that is a sub-class of entity, and second we defined another
sub-class of entity that is Resource. In particular, Resource, as
mentioned in the introduction, this element in ODO-IM is generated by
some contextualization of Observables and is any scientific artifact
that lives in the `resource layer` of k.LAB. Those include literals,
datasets, data services, computations, and computational services
without a semantic characterization. Resources are uniquely identified
by a URN, which are resolved to their contextualized values through
network services.

<a id="properties"></a>
## Object Properties

### Object property.

In ODO-IM while 20 object properties are imported from the PROV-O, for
example `prov:wasInfluencedBy` that defines the agent-to-agent
responsibility, 21 object properties have been newly created for this
application, those are:

* `affects`: a process affects a quality in its context when it is able
to change the state of the correspondent quality as time moves on. If
this relationship exists, the state that describes the quality is
dynamic.
* `appliesTo`: allows restricting the range of observables that an
observable applies to.
* `confers`: specifies the attribute or role conferred by a process.
* `contextualizes`: defines the relationship that links an observation
to its observable.
* `creates`: specifies the qualities or countable generated by the the
process.
* `describesQuality`: defines the quality using another quality or an
attribute.
* `emergesFrom`: establishes observables emerged from quality or
countable.
* `increasesWith`: defines the increase proportionaliy of quality and
ordering..
* `decreasesWith`: defines the decrease proportionaliy of quality and
ordering.
* `exposesTrait`: has as a domain an enumerable quality and as a range a
trait.
* `hasDestination` and `hasSource`: define the links between types of
relationship and the class of subjects.
* `hasRole`: points to the roles of an observable in the current
context.
* `hasScale`: specifies the scale of a description.
* `impliesDestination`: this object property is used for a role that
applies to a relationship, to restrict the type of destination the
relationship can lead into.
* `impliesObservable`: this property embodies the notion of
`implication` of another observable, whose existence is implied by
observing a particular trait. For example, the trait `warm` implies
presence of a process in which energy moves particles causing heat, or
more prosaically, observability of buildings in a point implies that a
building is there.
* `inherits`: specifies the predicate inherited in an observable.
* `limitedBy`: used to limit the possible value of a categorical
observer to a partial union of sub-types.
* `participates`: defines the participation of substantial in event or
process.
* `relatedTo`: most generic stated restriction used to imply an allowed
dependency.
* `representedBy`: can be used to restrict an observable when it is
observed through another - e.g. geographical direction by presence of
moss on trees.
* `requires`: used for compulsory declared elements to be coupled to an
observable.
