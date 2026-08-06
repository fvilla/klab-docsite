### What I changed
- Added a Conveyor configuration file `conveyor.conf` at the project root that describes how to package the app for Windows/macOS/Linux, including icons, Java settings, main class, and classpath.
- Extended `pom.xml` with a new Maven profile `conveyor` that:
    - Copies all runtime dependencies into `target/dependency` using `maven-dependency-plugin` during `prepare-package`.
    - Invokes Conveyor during the `package` phase using `maven-antrun-plugin` (`conveyor make app`).
- Wired the application version from Maven into Conveyor via the `PROJECT_VERSION` environment variable so distributions are versioned consistently.

### Files added/updated
- `conveyor.conf` (new):
  ```
  app {
    fsname = "klab-ide"
    productName = "k.LAB Modeler"
    vendor = "Integrated Modelling Partnership"
    version = ${?PROJECT_VERSION}
    version ??= "0.0.0-SNAPSHOT"
    id = "org.integratedmodelling.klab.ide"
    summary = "Integrated modelling IDE for the k.LAB platform"
    description = "A JavaFX-based IDE for knowledge-based modelling with k.LAB."

    icons {
      windows = "src/main/resources/package/windows/klab.ico"
      mac = "src/main/resources/package/macosx/klab.icns"
      linux = "src/main/resources/package/images/klab-ide.svg"
    }

    jvm {
      minVersion = "21"
      mainClass = "org.integratedmodelling.klab.ide.KlabIDEApplication"
      classpath = [
        "target/classes",
        "target/dependency/*"
      ]
      jvmArgs = [
        "--add-modules=javafx.controls,javafx.fxml,javafx.web,javafx.media,javafx.graphics,javafx.swing"
      ]
    }

    windows { signing.enabled = false; companyName = "Integrated Modelling Partnership"; appUserModelId = "org.integratedmodelling.klab.ide" }
    mac { signing.enabled = false; bundleId = "org.integratedmodelling.klab.ide" }
    linux { category = "Development" }
  }
  ```
- `pom.xml` (updated): Added a `conveyor` profile containing:
  ```xml
  <profile>
    <id>conveyor</id>
    <build>
      <plugins>
        <plugin>
          <groupId>org.apache.maven.plugins</groupId>
          <artifactId>maven-dependency-plugin</artifactId>
          <version>3.6.1</version>
          <executions>
            <execution>
              <id>copy-runtime-dependencies</id>
              <phase>prepare-package</phase>
              <goals><goal>copy-dependencies</goal></goals>
              <configuration>
                <outputDirectory>${project.build.directory}/dependency</outputDirectory>
                <includeScope>runtime</includeScope>
                <overWriteIfNewer>true</overWriteIfNewer>
              </configuration>
            </execution>
          </executions>
        </plugin>
        <plugin>
          <groupId>org.apache.maven.plugins</groupId>
          <artifactId>maven-antrun-plugin</artifactId>
          <version>3.1.0</version>
          <executions>
            <execution>
              <id>conveyor-make</id>
              <phase>package</phase>
              <goals><goal>run</goal></goals>
              <configuration>
                <target>
                  <exec executable="conveyor">
                    <arg value="make"/>
                    <arg value="app"/>
                    <env key="PROJECT_VERSION" value="${project.version}"/>
                  </exec>
                </target>
              </configuration>
            </execution>
          </executions>
        </plugin>
      </plugins>
    </build>
  </profile>
  ```

### How to build installable distributions
1. Prerequisites:
    - Install Conveyor from https://www.hydraulic.dev/ and ensure the `conveyor` command is on your PATH.
    - JDK 21 available (Conveyor embeds a runtime; the build process still requires JDK tools).
    - Add env variables (at this time: CONVEYOR_AGREE_TO_LICENSE=1; PROJECT_VERSION="1.0.0")
   
2. Build:
    - Windows/macOS/Linux (from project root):
      ```
      mvn -Pconveyor -DskipTests package
      ```
      or using the wrapper:
      ```
      ./mvnw -Pconveyor -DskipTests package
      ```
3. Outputs:
    - Conveyor writes platform-specific installers into its output directory (typically `out/`). Look for artifacts like `.msi`/`.exe` on Windows, `.dmg` on macOS, and `.deb`/`.rpm`/`.tar.gz` on Linux.

### Notes
- Code signing is disabled by default in `conveyor.conf`. To enable in CI, configure Conveyor’s signing settings (certs/Apple notarization) and remove/override `signing.enabled = false`.
- The app version used in the installers is taken from `${project.version}` via the `PROJECT_VERSION` environment variable.
- Runtime dependencies are copied into `target/dependency` so Conveyor can build from `target/classes` plus all required JARs.
- 
