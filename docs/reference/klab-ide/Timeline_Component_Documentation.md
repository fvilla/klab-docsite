# Timeline Component

The Timeline component is a JavaFX UI component that displays a timeline with alternating vertical sections of contrasting grey colors. It is configured with a start and end time (in milliseconds from epoch) and a temporal resolution (time unit and multiplier).

## Features

- Configurable start and end times (in milliseconds from epoch)
- Configurable temporal resolution (time unit and multiplier)
- Alternating vertical sections of contrasting grey colors
- End time can be changed using a slider, and the background updates accordingly
- Time labels showing the start and end times in human-readable format
- Support for adding events at specific timestamps
- Events are displayed as colored icons on the timeline
- Events can have different types (DEFAULT, INFO, WARNING, ERROR, SUCCESS)
- Events can trigger actions when clicked
- Timeline automatically extends when events beyond the end time are added

## Usage

### Basic Usage

```java
// Create a timeline with start time (now), end time (1 hour later), 
// and temporal resolution of 5 minutes
long startTimeMs = System.currentTimeMillis();
long endTimeMs = startTimeMs + 3600000; // 1 hour in milliseconds
Timeline timeline = new Timeline(startTimeMs, endTimeMs, TimeUnit.MINUTES, 5);

// Add the timeline to a container
myContainer.getChildren().add(timeline);
```

### Changing the End Time Programmatically

```java
// Update the end time to 2 hours later
timeline.updateEndTime(startTimeMs + 7200000);
```

### Using the TimelineDemo Component

The TimelineDemo component provides a complete example of how to use the Timeline component with various configurations.

```java
// Create a timeline demo
TimelineDemo demo = TimelineDemo.createDemo();

// Add the demo to a container
myContainer.getChildren().add(demo);
```

### Using the TimelineComponent from Components Class

The Timeline component is also accessible through the Components class.

```java
// Create a timeline component
Components.TimelineComponent timelineComponent = new Components.TimelineComponent();

// Add the component to a container
myContainer.getChildren().add(timelineComponent);
```

### Working with Events

The Timeline component supports adding events at specific timestamps. Events are displayed as colored dots on the timeline and can trigger actions when clicked.

#### Event Types

Events can have different types, which determine the color of the icon displayed on the timeline:

- `DEFAULT`: Magenta dot (default)
- `INFO`: Blue dot
- `WARNING`: Orange dot
- `ERROR`: Red dot
- `SUCCESS`: Green dot

#### Adding Events

You can add one or more events to the timeline using the `insertEvents` method:

```java
// Create an event with a timestamp, type, and click handler
long eventTime = System.currentTimeMillis() + 1800000; // 30 minutes from now
Consumer<Timeline.Event> clickHandler = event -> {
    System.out.println("Event clicked: " + event.getTimestamp());
    // Perform action when the event is clicked
};

Timeline.Event event = new Timeline.Event(eventTime, Timeline.EventType.INFO, clickHandler);

// Insert the event into the timeline
timeline.insertEvents(event);
```

#### Automatic Timeline Extension

If you add an event with a timestamp beyond the current end time of the timeline, the timeline will automatically extend to include the event:

```java
// Create an event beyond the current end time
long futureTime = timeline.getEndTimeMs() + 3600000; // 1 hour beyond end time
Timeline.Event futureEvent = new Timeline.Event(futureTime, Timeline.EventType.WARNING, clickHandler);

// Insert the event - this will automatically extend the timeline
timeline.insertEvents(futureEvent);
```

#### Getting Timeline Events

You can retrieve the list of events on the timeline using the `getEvents` method:

```java
List<Timeline.Event> events = timeline.getEvents();
for (Timeline.Event event : events) {
    System.out.println("Event at " + event.getTimestamp() + " of type " + event.getType());
}
```

## Implementation Details

The Timeline component is implemented in the following files:

- `Timeline.java`: The main component implementation, including the Event class and EventType enum
- `TimelineDemo.java`: A demo component showcasing the Timeline with various configurations
- `Components.java`: Contains a TimelineComponent class that creates a TimelineDemo instance

The Timeline component extends `Components.BaseComponent` and follows the same patterns as other components in the application.

### Key Classes and Enums

- `Timeline`: The main component class
- `Timeline.Event`: Inner class representing an event on the timeline
- `Timeline.EventType`: Enum defining the types of events (DEFAULT, INFO, WARNING, ERROR, SUCCESS)

### Key Methods

- `Timeline.insertEvents(Event... events)`: Adds one or more events to the timeline
- `Timeline.updateEndTime(long newEndTimeMs)`: Updates the end time of the timeline
- `Timeline.getEvents()`: Returns a list of all events on the timeline

## Customization

The Timeline component can be customized by:

1. Changing the start and end times
2. Changing the temporal resolution (time unit and multiplier)
3. Subclassing and overriding methods to change the appearance or behavior

## Example: Creating a Timeline with Custom Colors

```java
// Subclass Timeline to customize colors
public class CustomColorTimeline extends Timeline {
    private static final Color CUSTOM_LIGHT = Color.rgb(230, 240, 255);
    private static final Color CUSTOM_DARK = Color.rgb(200, 220, 255);

    public CustomColorTimeline(long startTimeMs, long endTimeMs, TimeUnit timeUnit, int multiplier) {
        super(startTimeMs, endTimeMs, timeUnit, multiplier);
    }

    @Override
    protected void drawTimeline() {
        // Override to use custom colors
        // Implementation would be similar to the original but with custom colors
    }
}
```
