# Workflow editor integration

`WorkflowEditor` is the generic JavaFX shell for Resources-service `Flow` objects. It is opened as
an auxiliary tab in the `WorkspaceEditor` containing the flow's target asset. The canonical model,
storage, authorization, REST, CRUD, URN, and provenance documentation remains in
`klab-services/docs/WORKFLOWS.md`.

## Enabling workflows

Install one `WorkflowUIProvider` on the `WorkspaceView`:

```java
workspaceView.setWorkflowUIProvider(
    new WorkflowUIProvider() {
      @Override
      public List<Workflow> availableWorkflows(NavigableAsset asset, UserScope scope) {
        return workflowCatalog.forAsset(asset, scope);
      }

      @Override
      public WorkflowEditor.StageEditor stageEditor(
          Workflow workflow,
          Flow flow,
          Flow.State state,
          Workflow.StateSchema schema,
          boolean readOnly,
          Runnable validationChanged) {
        return stageEditors.editorFor(schema.getId(), state, readOnly, validationChanged);
      }
    });
```

The provider is propagated to open workspace editors and inherited by editors opened later. The
no-op provider returns no startable workflows. Accessible existing flows are still listed because
they are obtained from the selected workspace's `ResourcesService`.

`availableWorkflows(asset, scope)` must return only applicable schemas. Their `Workflow.name` is
used in the menu; the ID is the fallback. Returning an empty list suppresses **Start workflow**.
The overall **Workflows** section is suppressed only when there are no startable workflows and no
accessible open or closed flows for the exact asset URN.

## Specialized stage contract

`WorkflowEditor.StageEditor` contains four values:

- `content`: the JavaFX node inserted between the common instructions and controls;
- `valid`: a predicate controlling every confirmation button;
- `metadata`: exports the validated stage contents as `Flow.State.metadata`;
- `readOnly`: informs the specialized component whenever mutation is forbidden.

The specialized editor must call `validationChanged.run()` whenever validity changes. On
confirmation, the shell saves exported metadata, then applies the chosen transition using the
updated flow revision. It owns the shared attachment UI, transition buttons, cancellation, stage
deletion, error reporting, and refresh behavior.

Returning `null` from `stageEditor` uses a generic metadata browser. Override `startFlow` only when
creation requires additional policy, such as setting `Flow.publicRead` through generic Resources
CRUD; the default calls `ResourcesService.createFlow`.

## Navigation and authorization

The tree context menu has a separated **Workflows** section with **Start workflow**, **Open flows**,
and **Closed flows** submenus. Multiple flows on the same asset are independent menu entries. New
flows focus their INIT stage. Existing flows focus the first open stage assigned to the user, then
the first visible current stage.

Public-read flows always open as read-only full-flow browsers. A private open stage is editable by
an `ADMIN`, its owner, or an assigned `EDITOR`. Closed flows are read-only; only `ADMIN` receives
the **Reopen flow** action. Server authorization repeats these rules, so hiding or disabling a
client control is never the security boundary.
