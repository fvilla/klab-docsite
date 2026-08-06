# KnowledgeGraphView
- Added a simple callback mechanism to `KnowledgeGraphView` that fires when the view is brought back into view/focus.

### Key additions
- New field: `private Runnable onBroughtIntoView;`
- New public setter:
  ```java
  public void setOnBroughtIntoView(Runnable callback)
  ```
- Invocation points:
    - When the node’s `visibleProperty` changes from false to true
      ```java
      this.visibleProperty().addListener((obs, wasVisible, isNowVisible) -> { if (isNowVisible) invokeBroughtIntoViewCallback(); });
      ```
    - When `setDigitalTwin(..., boolean inFocus)` is called with `inFocus == true`
      ```java
      if (inFocus) { invokeBroughtIntoViewCallback(); }
      ```
- Safe execution on the JavaFX Application Thread via `Platform.runLater(...)` when needed.

### How to use
```java
knowledgeGraphView.setOnBroughtIntoView(() -> {
  // e.g., refresh data, rerun layout, update controls, etc.
  System.out.println("Graph view is visible again!");
});
```

### Notes
- The callback runs only when visibility becomes true again or when the view is programmatically brought into focus through `setDigitalTwin(..., true)`.
- This does not trigger on initial construction unless the view transitions from not visible to visible or is set in focus with `inFocus = true`.
