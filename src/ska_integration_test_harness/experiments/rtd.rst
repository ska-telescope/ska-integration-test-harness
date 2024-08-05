# Test Documentation Generator

NOTE: this is a draft of the RTD file that could accompany this script

## Overview

The Test Documentation Generator is a Python script designed to automatically generate markdown documentation from Python test files and Gherkin feature files. It's particularly useful for projects using Behaviour Driven Development (BDD) methodologies.

## Installation

To use the Test Documentation Generator, you need Python 3.6 or higher. Clone the repository and install the required dependencies:

```bash
git clone https://github.com/your-repo/test-documentation-generator.git
cd test-documentation-generator
pip install -r requirements.txt
```

## Usage

Run the script from the command line, providing the input folder containing your Python and feature files, and the desired output folder for the markdown files:

```bash
python document_steps.py <input_folder> <output_folder>
```

For example:

```bash
python document_steps.py ../../tests out/
```

This will process all Python (.py) and feature (.feature) files in the input folder and its subfolders, generating corresponding markdown files in the output folder.

## Key Components

### FileScanner

This class is responsible for parsing Python files to extract test steps and scenarios. It uses the `ast` module to analyse the abstract syntax tree of Python files.

### MarkdownFormatter

The MarkdownFormatter class handles the generation of markdown content. It formats the extracted steps and scenarios into a readable markdown structure.

### FolderProcessor

This class orchestrates the entire process. It walks through the input folder, identifies relevant files, and coordinates the parsing and markdown generation for each file.

### PostProcessor

The PostProcessor creates an index file that provides links to all generated markdown files, preserving the folder structure of the original files.

## File Handling

The script handles two types of files:

1. **Python Files (.py)**: These are parsed to extract test steps (decorated with `@given`, `@when`, `@then`) and scenarios (decorated with `@scenario`).

2. **Feature Files (.feature)**: These Gherkin syntax files are converted directly to markdown, preserving their structure and formatting.

## Output Structure

The generated documentation follows this structure:

```
out/
├── features/
│   └── [Feature files converted to markdown]
├── steps/
│   └── [Python files converted to markdown]
└── index.md
```

The `index.md` file provides a navigable structure of all generated documentation.

## Customization

You can customize the script's behaviour by modifying the following classes:

- `StepVisitor`: Adjust how steps and scenarios are extracted from Python files.
- `MarkdownFormatter`: Modify the markdown formatting for different elements.
- `FolderProcessor`: Change how files are processed or add support for new file types.

## Limitations

- The script assumes a specific structure for test files and may need adjustments for different project structures.
- It does not verify the correctness of the test implementations, only extracts and documents them.

## Contributing

Contributions to improve the Test Documentation Generator are welcome. Please submit a pull request or open an issue on the GitHub repository.

## License

[Specify your license here]