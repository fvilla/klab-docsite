# Provenance and the lifecycle of knowledge

The science that addresses the life cycle of scientific artifacts from their source through their transformation, analysis, and interpretation is named **provenance**, and provides a useful starting point to clarify the rationale of semantic modeling. The provenance conceptual model (our reference is the [Open Provenance Model - OPM](http://openprovenance.org)) provides terminology to refer to this process, such as _entity_ for any scientific artifact that can be stored and communicated, and _activity_ for any process that produces an entity from zero or more others. Semantic modeling builds on provenance to enable a scientific process that hinges on the _meaning_ associated with every scientific entity and activity. We argue that the re-elaboration of the scientific process made in semantic modeling meets, _by design_, all the [FAIR](http://go-fair.org) (Findable, Accessible, Interoperable and Reusable) principles, and can greatly enhance the return of investment of science by easing communication across disciplines and societal sectors, and ensuring the longest useful life for its products, beyond the original rationale for their production.

As described more formally in the [k.LAB core ontology (ODO-IM)](https://github.com/integratedmodelling/odo-im) and its [documentation](ODO_IM.md), semantic modeling extends the terms of the Open Provenance Model as follows:

* *Resource* is the equivalent of the OPM _entity_, representing any communicable, storeable artifact that embodies scientific knowledge - such as a dataset, report or
equation. Resources are always semantically characterized by the concept
they describe (the _observable_) and are intended as directly
_actionable_, i.e. machine-readable in all of their parts and
implications with no need for human intervention. Resources are _published_ online with their metadata and are identified by an unmodifiable Uniform Resource Name (URN).
* *Contextualization* is the semantic equivalent of the OPM _activity_,
representing the production of a Resource (using zero or more other
Resources) and recognizing that a Resource that serves as _context_ must
be provided (_acknowledged_) by the observing agent to bootstrap the
process.
* *Description* is the semantic equivalent of the OPM _plan_, linking a
semantic statement (the _observable_) to a computational strategy to
build a Resource that represents it. Descriptions can be stored online and perused by a machine-driven process to produce resources based on a semantic query for their observable in a chosen context.

Based on these definitions, semantic modeling proceeds by enabling two main tasks:

. the definition of _observable expressions_, which carry the meaning of observable concepts and allow modelers to capture complex meanings and linguistic distinctions
commonly adopted in day-to-day scientific practice;
. the definition of _models_, statements that embody methodological "recipes" (corresponding to Descriptions, or semantically-enabled OPM Plans) that have observable expressions as inputs and outputs, representing synthetic statements of scientific methods that are normally only expressed as non directly actionable artifacts, such as equations in scientific articles or complex computer code.

## How provenance is collected and propagated

## How to add provenance for resources
