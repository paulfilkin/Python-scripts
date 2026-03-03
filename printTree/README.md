# Directory Tree Generator

A Python script that generates a markdown file (`tree.md`) showing the directory structure of a given folder. It automatically detects project types and offers to exclude build/generated files.

## Usage

```bash
python directory_tree.py
```

You'll be prompted for the folder path. If a known project type is detected, you'll be asked whether to exclude build/generated files (default: Yes). The output is written to `tree.md` inside the provided folder.

## Project Type Detection

The script detects project types by looking for marker files in the root folder:

- **Android Studio** - detected via `build.gradle`, `build.gradle.kts`, `settings.gradle`, or `settings.gradle.kts`
- **Visual Studio / .NET** - detected via `.sln`, `.csproj`, `.vbproj`, or `.fsproj`

Multiple project types can be detected simultaneously.

## Exclusions

### Common (always applied)

`.git`, `node_modules`, `__pycache__`

### Android Studio (when build exclusion enabled)

- Directories: `.gradle`, `gradle`, `build`, `.idea`, `.cxx`, `.externalNativeBuild`, `captures`
- Files: `local.properties`, `gradlew`, `gradlew.bat`
- Extensions: `.iml`

### Visual Studio / .NET (when build exclusion enabled)

- Directories: `bin`, `obj`, `.vs`, `packages`, `TestResults`
- Extensions: `.user`, `.suo`
