#!/usr/bin/env python3
import os

def collect_requirements(root_dir):
    """
    Walks through the current directory recursively to find files that look like requirements files,
    reads their content, and returns a set of requirement lines.
    """
    requirements_set = set()
    # Recursively walk through the current directory
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            # Adjust the pattern as needed. Here we collect files like 'requirements.txt' or 'requirements-dev.txt'
            if file.startswith("requirements") and file.endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            # Remove leading/trailing whitespace
                            line = line.strip()
                            # Skip empty lines and comments
                            if line and not line.startswith("#"):
                                requirements_set.add(line)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    return requirements_set

def write_requirements(requirements, output_file="inventor-requirements.txt"):
    """
    Writes the sorted set of requirements to the specified output file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for requirement in sorted(requirements):
                f.write(requirement + "\n")
        print(f"Combined requirements written to {output_file}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")

def main():
    requirements = collect_requirements('../src')
    write_requirements(requirements)

if __name__ == "__main__":
    main()
