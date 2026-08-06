# Project structure

### 1. Overall Directory Structure (Top 2-3 Levels)

```
C:\Users\Ferd\git\klab-ide/
├── .git/                          (Git repository)
├── .idea/                         (IntelliJ IDEA configuration)
├── .mvn/                          (Maven wrapper)
├── src/
│   └── main/
│       ├── java/
│       │   └── org/integratedmodelling/klab/ide/
│       │       ├── api/
│       │       ├── components/
│       │       │   ├── cards/
│       │       │   ├── generic/
│       │       │   └── treeviews/
│       │       ├── events/
│       │       ├── lsp/
│       │       ├── notifications/
│       │       ├── pages/
│       │       ├── test/
│       │       ├── utils/
│       │       ├── IDEContextScope.java
│       │       ├── KlabIDEApplication.java
│       │       ├── KlabIDEController.java
│       │       └── Theme.java
│       └── resources/
│           ├── org/integratedmodelling/klab/ide/
│           │   ├── custom.css
│           │   ├── ide.fxml
│           │   ├── icons/
│           │   └── templates/
│           └── package/
│               ├── images/
│               ├── linux/
│               ├── macosx/
│               ├── windows/
│               └── install4j.utf8
├── target/                        (Build artifacts)
├── jte-classes/                   (JTE template classes)
├── pom.xml                        (Maven build configuration)
├── conveyor.conf                  (Conveyor packaging configuration)
├── mvnw, mvnw.cmd                (Maven wrapper scripts)
└── docs/                         (Project documentation)
    ├── BUILD.md, BUILD_README.md  (Build documentation)
    └── Other documentation files
```

### 2. Build Files Contents

#### pom.xml (464 lines)
The Maven build file for the k.LAB IDE JavaFX application. Key features:
- **Project Info:**
    - Group ID: `org.integratedmodelling`
    - Artifact ID: `klab-ide`
    - Version: `1.0.0-SNAPSHOT`
    - Java Target: 21

- **Key Dependencies:**
    - JavaFX 21 (controls, fxml, web, swing, media, graphics)
    - klab-cli and klab.modeler (1.0.0-SNAPSHOT)
    - klab-editor
    - javafx-graph (2.4.0-SNAPSHOT)
    - LSP4J for language server support
    - AtlantaFX UI themes (2.1.0)
    - Ikonli icon packs (multiple - FontAwesome, Material Design, Carbon Icons, etc.)
    - JUnit 5 testing framework

- **Build Plugins:**
    - javafx-maven-plugin (v0.0.8) - runs and packages JavaFX applications
    - maven-compiler-plugin - targets Java 21
    - maven-dependency-plugin - generates classpath files
    - maven-shade-plugin (v3.5.1) - creates fat JAR (klab-ide-all-1.0.0-SNAPSHOT.jar)

- **Profiles:**
    - `conveyor` profile - handles Conveyor packaging (runs `conveyor make app`)

#### conveyor.conf (118 lines)
Conveyor packaging configuration for cross-platform distribution. Key content:
- **App Metadata:**
    - fsname: `klab-ide`
    - productName/displayName: `k.LAB Modeler`
    - Vendor: `Integrated Modelling Partnership`
    - Version: `1.0`
    - RDNS ID: `org.integratedmodelling.klab.ide`
    - Summary: "Integrated modelling IDE for the k.LAB platform"
    - Description: "A JavaFX-based IDE for knowledge-based modelling with k.LAB."

- **Main Class:** `org.integratedmodelling.klab.ide.KlabIDEApplication`

- **JavaFX Configuration:**
    - JavaFX version: `21.0.6`
    - JavaFX modules: controls, fxml, web, media, graphics, swing

- **Input Artifacts:**
    - Windows/Linux/Mac: Uses `target/klab-ide-all-1.0.0-SNAPSHOT.jar`

- **Platform Support:**
    - Windows (amd64)
    - Linux (amd64 glibc)
    - macOS (amd64 and aarch64)

- **JVM Configuration:**
    - Minimum Java version: 21
    - Additional modules: charsets, crypto, localedata, logging, desktop, XML, scripting, etc.

- **Platform-Specific Settings:**
    - Windows: Code signing disabled (can be enabled in CI), companyName = "Integrated Modelling Partnership"
    - macOS: Code signing disabled, bundleId = `org.integratedmodelling.klab.ide`
    - Linux: Category = "Development"

- **Build Site:**
    - base-url: `https://klab.integratedmodelling.org`

### 3. Package Directory Contents

#### /src/main/resources/package/ Structure:

```
package/
├── images/
│   ├── klab-ide.svg (3,078 bytes) - SVG Scalable Vector Graphics
│   ├── splashscreen.png (8,528 bytes) - 300 x 140 PNG
│   └── splashscreen.svg (36,850 bytes) - SVG format
├── linux/
│   └── klab.png (2,171 bytes) - 96 x 96 PNG
├── macosx/
│   ├── DS_Store (10,244 bytes) - macOS folder metadata
│   ├── klab-background.png (21,940 bytes) - 1000 x 600 PNG for DMG background
│   └── klab.icns (58,056 bytes) - Mac OS X icon resource
├── windows/
│   └── klab.ico (38,732 bytes) - Windows icon resource
└── install4j.utf8 (485 bytes) - Install4J wizard localization strings
```

### 4. Icon Files (Complete List)

**Packaging/Distribution Icons:**

1. **Windows Icon**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/package/windows/klab.ico`
    - Type: MS Windows icon resource
    - Contains: 5 icons (16x16 and 32x32, 32 bits/pixel)
    - Size: 38,732 bytes
    - Used by: Conveyor (Windows installer and shortcuts)

2. **macOS Icon**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/package/macosx/klab.icns`
    - Type: Mac OS X icon resource (ic12 type)
    - Size: 58,056 bytes
    - Used by: Conveyor (macOS .app bundle)

3. **Linux Icon**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/package/linux/klab.png`
    - Type: PNG image data (96 x 96, 8-bit/color RGBA)
    - Size: 2,171 bytes
    - Used by: Conveyor (Linux desktop shortcuts)

4. **General/SVG Icons**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/package/images/klab-ide.svg`
    - Type: SVG Scalable Vector Graphics
    - Size: 3,078 bytes
    - Used by: Conveyor (Linux), general application icon

**Splash/Background Graphics:**

5. **Splash Screen PNG**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/package/images/splashscreen.png`
    - Type: PNG image (300 x 140, 8-bit/color RGBA)
    - Size: 8,528 bytes

6. **Splash Screen SVG**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/package/images/splashscreen.svg`
    - Type: SVG Scalable Vector Graphics
    - Size: 36,850 bytes

7. **macOS DMG Background**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/package/macosx/klab-background.png`
    - Type: PNG image (1000 x 600, 8-bit/color RGBA)
    - Size: 21,940 bytes
    - Used by: macOS DMG installer background

**Embedded Application Icons (in resources):**

8. **Elephant Logo PNG**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/org/integratedmodelling/klab/ide/icons/klab-elephant.png`

9. **IM Logo PNG**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/org/integratedmodelling/klab/ide/icons/klab-im.png`

10. **Elephant Logo SVG**
    - Path: `/c/Users/Ferd/git/klab-ide/src/main/resources/org/integratedmodelling/klab/ide/icons/klab_elephant.svg`

### 5. Main Application Entry Point

**Primary Entry Point:**
```java
org.integratedmodelling.klab.ide.KlabIDEApplication
```

**Location:** `/c/Users/Ferd/git/klab-ide/src/main/java/org/integratedmodelling/klab/ide/KlabIDEApplication.java`

**Key Details:**
- Extends `javafx.application.Application`
- Main method: `public static void main(String[] args)` - calls `launch()`
- Start method loads FXML from `ide.fxml` resource
- Window title: "k.LAB Modeler :: v1.0 pre-alpha :: © 2025 Integrated Modelling Partnership"
- Minimum window width: 1200px
- Initial scene size: 1480 x 1060
- Sidebar width: 270px
- Uses AtlantaFX theme system
- Custom CSS: `/src/main/resources/org/integratedmodelling/klab/ide/custom.css`
- FXML: `/src/main/resources/org/integratedmodelling/klab/ide/ide.fxml`

**Supporting Files in Main Package:**
- `IDEContextScope.java` - Context scope management
- `KlabIDEController.java` - Main IDE controller (60KB+)
- `Theme.java` - Theme management for AtlantaFX

### 6. Jpackage/Installer Configuration

This project uses **Conveyor** for cross-platform packaging, NOT jpackage directly.

**Conveyor Configuration Details (conveyor.conf):**

**Entry Point:**
- GUI Main Class: `org.integratedmodelling.klab.ide.KlabIDEApplication`

**Icon Mappings (Conveyor):**
```
icons {
  windows = "src/main/resources/package/windows/klab.ico"
  mac = "src/main/resources/package/macosx/klab.icns"
  linux = "src/main/resources/package/images/klab-ide.svg"
}
```

**Classpath Configuration (for Conveyor):**
```
classpath = [
  "target/classes",
  "target/dependency/*"
]
```

**JVM Arguments (Conveyor):**
```
--add-modules=javafx.controls,javafx.fxml,javafx.web,javafx.media,javafx.graphics,javafx.swing
```

**Build Targets:**
- `windows.amd64`
- `linux.amd64.glibc`
- `mac.amd64`
- `mac.aarch64`

**Maven Integration:**
- Maven profile: `conveyor`
- Executes: `mvn -P conveyor package`
- Calls Conveyor binary: `conveyor make app`
- Sets environment variable: `PROJECT_VERSION=${project.version}`
- Maven plugin: `maven-antrun-plugin` (v3.1.0)

**Dependencies for Packaging:**
1. `maven-dependency-plugin` - copies runtime dependencies to `target/dependency/`
2. `maven-shade-plugin` - creates fat JAR `klab-ide-all-1.0.0-SNAPSHOT.jar`

**Software Versions:**
- Java: 21
- Maven: 3.13.0 (compiler plugin)
- Conveyor: Latest (specified in project, not in pom.xml)
- JavaFX: 21.0.6

### Summary

This is a **JavaFX-based IDE application** for the k.LAB modelling platform that uses **Maven for building** and **Conveyor for cross-platform packaging and distribution**. The project provides native installers for Windows (.exe, .msi), macOS (.dmg, .app), and Linux (.deb, .rpm). All necessary platform-specific icons and assets are included, with comprehensive build configuration for automated releases across all major operating systems.
