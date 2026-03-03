import os

# Common folders/files to always ignore
COMMON_EXCLUDED = {'.git', 'node_modules', '__pycache__'}

# Android Studio exclusions
ANDROID_EXCLUDED_DIRS = {'.gradle', 'gradle', 'build', '.idea', '.cxx', '.externalNativeBuild', 'captures'}
ANDROID_EXCLUDED_FILES = {'local.properties', 'gradlew', 'gradlew.bat'}
ANDROID_EXCLUDED_EXTENSIONS = {'.iml'}

# Visual Studio / .NET exclusions
VS_EXCLUDED_DIRS = {'bin', 'obj', '.vs', 'packages', 'TestResults'}
VS_EXCLUDED_EXTENSIONS = {'.user', '.suo'}


def detect_project_type(path):
    """Detect the project type based on marker files."""
    items = os.listdir(path)
    project_types = []

    if any(f in items for f in ('build.gradle', 'build.gradle.kts', 'settings.gradle', 'settings.gradle.kts')):
        project_types.append('android')

    if any(f.endswith(('.sln', '.csproj', '.vbproj', '.fsproj')) for f in items):
        project_types.append('visualstudio')

    return project_types


def should_exclude(item, item_path, project_types, exclude_build):
    """Determine if an item should be excluded based on project type."""
    is_dir = os.path.isdir(item_path)
    _, ext = os.path.splitext(item)

    # Common exclusions always apply
    if is_dir and item in COMMON_EXCLUDED:
        return True

    if not exclude_build:
        return False

    # Android exclusions
    if 'android' in project_types:
        if is_dir and item in ANDROID_EXCLUDED_DIRS:
            return True
        if not is_dir and (item in ANDROID_EXCLUDED_FILES or ext in ANDROID_EXCLUDED_EXTENSIONS):
            return True

    # Visual Studio exclusions
    if 'visualstudio' in project_types:
        if is_dir and item in VS_EXCLUDED_DIRS:
            return True
        if not is_dir and ext in VS_EXCLUDED_EXTENSIONS:
            return True

    return False


def get_directory_tree(path, project_types, exclude_build, indent=0):
    """Returns the directory tree of the given path as a list of lines."""
    lines = []
    if not os.path.exists(path):
        lines.append(f"Error: The path {path} does not exist.")
        return lines

    if not os.path.isdir(path):
        lines.append(f"Error: {path} is not a directory.")
        return lines

    for item in sorted(os.listdir(path)):
        item_path = os.path.join(path, item)

        if should_exclude(item, item_path, project_types, exclude_build):
            continue

        lines.append("  " * indent + f"- {item}")
        if os.path.isdir(item_path):
            lines.extend(get_directory_tree(item_path, project_types, exclude_build, indent + 1))

    return lines


folder_path = input("Enter the folder path: ")

if not os.path.isdir(folder_path):
    print(f"Error: {folder_path} is not a valid directory.")
    exit(1)

project_types = detect_project_type(folder_path)

if project_types:
    detected = ', '.join(t.title() for t in project_types)
    print(f"Detected project type(s): {detected}")
    exclude_input = input("Exclude build/generated files? [Y/n]: ").strip().lower()
    exclude_build = exclude_input != 'n'
else:
    print("No specific project type detected - applying common exclusions only.")
    exclude_build = False

output_file = os.path.join(folder_path, "tree.md")

lines = [f"# Directory structure for: {folder_path}", ""]
if project_types:
    lines.append(f"Project type(s): {', '.join(t.title() for t in project_types)}")
    lines.append(f"Build/generated files excluded: {'Yes' if exclude_build else 'No'}")
    lines.append("")
lines.extend(get_directory_tree(folder_path, project_types, exclude_build))

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines) + "\n")

print(f"Directory tree written to {output_file}")