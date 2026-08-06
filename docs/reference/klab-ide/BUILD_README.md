# Building k.LAB Modeler with Conveyor

This project uses [Conveyor](https://www.hydraulic.dev/) for packaging the k.LAB Modeler as an executable for Windows, Linux, and macOS.

## Prerequisites

1.  **Conveyor**: Install it from [hydraulic.dev](https://www.hydraulic.dev/).
2.  **JDK 21**: Ensure you have JDK 21 installed.
3.  **Environment Variables**:
    *   `CONVEYOR_AGREE_TO_LICENSE=1` (Required by Conveyor)
    *   `PROJECT_VERSION` (Automatically handled by the Maven profile)

## Build Commands

You can build for specific platforms using the `conveyor` Maven profile and the `conveyor.target` property.

### 1. Windows (64-bit)
To build a Windows MSIX installer:
```bash
mvn -Pconveyor -Dconveyor.target=windows-msix package
```
To build a Windows ZIP:
```bash
mvn -Pconveyor -Dconveyor.target=windows-zip package
```

### 2. Linux
To build a Debian package:
```bash
mvn -Pconveyor -Dconveyor.target=linux-deb package
```
To build a Linux Tarball:
```bash
mvn -Pconveyor -Dconveyor.target=linux-tarball package
```

### 3. macOS
To build a macOS DMG:
```bash
mvn -Pconveyor -Dconveyor.target=macos-dmg package
```
To build a macOS ZIP:
```bash
mvn -Pconveyor -Dconveyor.target=macos-zip package
```

### 4. All Platforms (Default)
To build the default "app" target (which includes all configured machines if using `make site` or specific local architecture if using `make app`):
```bash
mvn -Pconveyor package
```

## Output
The built artifacts will be located in the `output/` directory (relative to the project root).

## Configuration Notes
- **Code Signing**: Currently disabled for all platforms. For production releases, you must provide certificates in `conveyor.conf`.
- **Target Machines**: Configured in `conveyor.conf` to support `windows.amd64`, `linux.amd64.glibc`, `mac.amd64`, and `mac.aarch64`.
