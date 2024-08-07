# pylint: skip-file

import argparse
import ast
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# This script is used to generate markdown files
# from Python files containing test steps and scenarios.
# The script scans the Python files and extracts the test steps
# and scenarios using AST.
# It then generates a markdown file with the extracted information
# for each input file.
# Use the script as follows:
# python document_steps.py <input_folder> <output_folder>

# for example:
#  python3 document_steps.py ../../.. out/
# produces
# out
# ├── features
# │ └── tests
# │     ├── features
# │     │ ├── ai_generated_scenarios.md
# │     │ ├── check_abort_command.md
# │     │ ├── check_command_not_allowed.md
# │     │ ├── check_invalid_json_not_allowed.md
# │     │ ├── dish_vcc_initialization
# │     │ │ ├── xtp_30249_csp_mln_init.md
# │     │ │ ├── xtp_30250_restart.md
# │     │ │ ├── ...
# │     │ ├── load_dish_cfg_command.md
# │     │ ├── ...
# │     │ ├── test_harness
# │     │ │ ├── five_point_scan.md
# │     │ │ ├── science_scan_after_calibration_scan.md
# │     │ │ ├── subarray_health_state.md
# │     │ │ ├── ...
# │     │ ├── tmc_csp
# │     │ │ ├── xtp_29249_on.md
# │     │ │ ├── xtp_29250_off.md
# │     │ │ ├── xtp_29251_standby.md
# │     │ │ ├── ...
# │     │ ├── tmc_dish
# │     │ │ ├── xtp-29077.md
# │     │ │ ├── xtp-29351_off.md
# │     │ │ ├── ...
# │     │ ├── tmc_sdp
# │     │ │ ├── xtp_27257_recovery_after_failed_assign.md
# │     │ │ ├── xtp-29230_on.md
# │     │ │ ├── ...
# │     │ ├── xtp-28259.md
# │     │ ├── xtp-28282.md
# │     │ ├── ...
# │     ├── tmc_csp
# │     │ └── suggestions_for_new_stuff
# │     │     ├── esempio_scenario_ai.md
# │     │     └── via
# │     │         ├── ai_generated_scenarios_GB.md
# │     │         └── positive_scenarios_single_transitions.md
# │     └── tmc_csp_refactor3
# │         ├── features
# │         │ ├── abort_restart_subarray.md
# │         │ └── subarray_commands.md
# │         └── specifications
# │             ├── obsstate_invalid_single_transitions.md
# │             ├── obsstate_valid_single_transitions_automatic.md
# │             └── obsstate_valid_single_transitions_commands.md
# └── steps
#     └── tests
#         ├── alarm_handler
#         │ ├── test_dishvcc_alarm_configurator.md
#         │ └── test_pointing_data_alarm.md
#         ├── check_command_allowed
#         │ ├── test_command_not_allowed_assigning_resources.md
#         │ ├── test_command_not_allowed_empty.md
#         │ ├── ...
#         ├── conftest.md
#         ├── dish_vcc_configuration
#         │ ├── conftest.md
#         │ ├── test_load_dish_cfg.md
#         │ ├── test_load_dish_cfg_negative_scenario.md
#         │ ├── ...
#         ├── invalid_json_tests
#         │ ├── test_assign_not_allowed_with_invalid_json.md
#         │ └── test_configure_invalid_json.md
#         ├── tmc_csp
#         │ ├── conftest.md
#         │ ├── test_delay_model.md
#         │ ├── test_scan_ai_generated.md
#         │ ├── ...
#         ├── tmc_csp_dish
#         │ └── test_dish_vcc_initialization.md
#         ├── tmc_csp_refactor3
#         │ ├── conftest.md
#         │ ├── test_abort.md
#         │ └── test_command_triggered.md
#         ├── tmc_dish
#         │ ├── conftest.md
#         │ ├── test_xtp-29077.md
#         │ ├── ...
#         ├── tmc_harness_testcases
#         │ └── bdd_scenarios
#         │     ├── test_central_node_telescope_health_state.md
#         │     ├── ...
#         ├── tmc_robustness
#         │ ├── AssignResources_Failure_Handling_tests
#         │ │ ├── test_assign_resources_handling_on_csp_obsstate_empty_failure.md  # pylint: disable=line-too-long # noqa E501
#         │ │ ├── test_assign_resources_handling_on_csp_obsstate_resourcing_failure.md  # pylint: disable=line-too-long # noqa E501
#         │ │ ├── ...
#         │ ├── Configure_failure_handling_tests
#         │ │ ├── test_configure_handling_on_csp_obstate_configuring.md
#         │ │ ├── ...
#         │ ├── Incremental_AssignResources_Failure_Handling_tests
#         │ │ ├── test_incremental_assign_resources_csp_subarray_failure.md
#         │ │ ├── ...
#         │ ├── test_mid_successive_configure.md
#         │ ├── ...
#         └── tmc_sdp
#             ├── conftest.md
#             ├── test_xtp_27257_recovery_after_failed_assign.md
#             ├── ...

#


class MarkdownFormatter:
    """Class for managing the output and MD formatting."""

    @staticmethod
    def generate_markdown(
        filepath: str, steps: List[Dict], scenarios: Dict[str, str]
    ) -> str:
        """Generate markdown content from steps and scenarios."""
        current_time = datetime.now().strftime("%d %B %Y %H:%M:%S")
        markdown = f"# Test Steps and Scenarios from {filepath}\n\n"
        markdown += f"Last updated on: {current_time}\n\n"

        if scenarios:
            markdown += "## Scenarios\n\n"
            for func_name, scenario_name in scenarios.items():
                markdown += f"- {scenario_name} (`{func_name}`)\n"
            markdown += "\n"

        if steps:
            markdown += "## Steps\n\n"
            for step in steps:
                markdown += (
                    f"### {step['type'].capitalize()}: {step['name']}\n\n"
                )
                markdown += f"**Function:** `{step['function']}`\n\n"
                markdown += (
                    f"**Signature:**\n```python\n{step['signature']}\n```\n\n"
                )
                markdown += f"**Description:**\n{step['docstring']}\n\n"
                markdown += "---\n\n"
        else:
            markdown += "No steps found in this file.\n"

        return markdown

    @staticmethod
    def write_markdown(content: str, output_file: str) -> None:
        """Write markdown content to a file."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as file:
            file.write(content)
        print(f"Markdown file '{output_file}' has been generated.")
        print(
            f"Last updated on: {datetime.now().strftime('%d %B %Y %H:%M:%S')}"
        )

    @staticmethod
    def format_feature_file(content: str) -> str:
        """Format feature file content as Markdown."""
        markdown = "# Feature\n\n"
        lines = content.split("\n")
        in_scenario = False
        in_example = False
        example_table = []

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("Feature:"):
                markdown += f"## {stripped_line}\n\n"
            elif stripped_line.startswith(
                "Scenario:"
            ) or stripped_line.startswith("Scenario Outline:"):
                if in_example:
                    markdown += MarkdownFormatter._format_example_table(
                        example_table
                    )
                    example_table = []
                    in_example = False
                in_scenario = True
                markdown += f"### {stripped_line}\n\n"
            elif (
                stripped_line.startswith("Given ")
                or stripped_line.startswith("When ")
                or stripped_line.startswith("Then ")
                or stripped_line.startswith("And ")
                or stripped_line.startswith("But ")
            ):
                markdown += f"- {stripped_line}\n"
            elif stripped_line.startswith("Examples:"):
                in_example = True
                markdown += f"#### {stripped_line}\n\n"
            elif in_example and "|" in stripped_line:
                example_table.append(stripped_line)
            elif stripped_line == "" and in_scenario:
                if in_example:
                    markdown += MarkdownFormatter._format_example_table(
                        example_table
                    )
                    example_table = []
                    in_example = False
                in_scenario = False
                markdown += "\n"
            else:
                markdown += f"{line}\n"

        # Handle case where file ends with an example table
        if example_table:
            markdown += MarkdownFormatter._format_example_table(example_table)

        return markdown

    @staticmethod
    def _format_example_table(table_lines: List[str]) -> str:
        """Format an example table in Markdown."""
        if not table_lines:
            return ""

        # Strip leading and trailing pipes and spaces
        cleaned_lines = [
            line.strip().strip("|").strip() for line in table_lines
        ]

        # Split each line into cells
        table_data = [line.split("|") for line in cleaned_lines]

        # Strip spaces from each cell
        table_data = [[cell.strip() for cell in row] for row in table_data]

        # Find the maximum width for each column
        col_widths = [
            max(len(cell) for cell in col) for col in zip(*table_data)
        ]

        # Generate the formatted table
        formatted_table = (
            "| "
            + " | ".join(
                cell.ljust(width)
                for cell, width in zip(table_data[0], col_widths)
            )
            + " |\n"
        )
        formatted_table += (
            "| " + " | ".join("-" * width for width in col_widths) + " |\n"
        )
        for row in table_data[1:]:
            formatted_table += (
                "| "
                + " | ".join(
                    cell.ljust(width) for cell, width in zip(row, col_widths)
                )
                + " |\n"
            )

        return formatted_table + "\n"


class StepVisitor(ast.NodeVisitor):
    """Visitor class to extract steps and scenarios from AST."""

    def __init__(self):
        self.steps: List[Dict[str, str]] = []
        self.scenarios: Dict[str, str] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Visit a function definition in the AST.

        Pre-conditions:
        - node is an instance of ast.FunctionDef

        Post-conditions:
        - If the function is decorated with 'given', 'when', or 'then',
          a step is added to self.steps
        - If the function is decorated with 'scenario', an entry is added
          to self.scenarios
        """
        assert isinstance(node, ast.FunctionDef), "Node must be a FunctionDef"

        initial_steps_count = len(self.steps)
        initial_scenarios_count = len(self.scenarios)

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(
                decorator.func, ast.Name
            ):
                if decorator.func.id in ["given", "when", "then"]:
                    self._process_step(node, decorator)
                elif decorator.func.id == "scenario":
                    self._process_scenario(node, decorator)

        assert (
            len(self.steps) >= initial_steps_count
        ), "Steps should not decrease"
        assert (
            len(self.scenarios) >= initial_scenarios_count
        ), "Scenarios should not decrease"

    def _process_step(
        self, node: ast.FunctionDef, decorator: ast.Call
    ) -> None:
        """
        Process a step decorator.

        Pre-conditions:
        - node is an instance of ast.FunctionDef
        - decorator is an instance of ast.Call

        Post-conditions:
        - If a valid step name is extracted, a new step is added to self.steps
        - If no valid step name is extracted, a warning is printed
        """
        assert isinstance(node, ast.FunctionDef), "Node must be a FunctionDef"
        assert isinstance(decorator, ast.Call), "Decorator must be a Call"

        initial_steps_count = len(self.steps)

        step_type = decorator.func.id
        step_name = self._extract_step_name(decorator)
        if step_name is not None:
            self.steps.append(
                {
                    "type": step_type,
                    "name": step_name,
                    "function": node.name,
                    "signature": self._get_signature(node),
                    "docstring": ast.get_docstring(node),
                }
            )
        else:
            print(
                "Warning: Could not extract step name "
                f"for function {node.name}"
            )

        assert (
            len(self.steps) >= initial_steps_count
        ), "Steps should not decrease"

    def _extract_step_name(self, decorator: ast.Call) -> Optional[str]:
        """
        Extract the step name from a decorator.

        Pre-conditions:
        - decorator is an instance of ast.Call

        Post-conditions:
        - Returns a string if a valid step name is found, None otherwise
        """
        assert isinstance(decorator, ast.Call), "Decorator must be a Call"

        if decorator.args:
            if isinstance(decorator.args[0], ast.Str):
                return decorator.args[0].s
            elif isinstance(decorator.args[0], ast.Call):
                if decorator.args[0].args and isinstance(
                    decorator.args[0].args[0], ast.Str
                ):
                    return decorator.args[0].args[0].s
        elif decorator.keywords:
            for keyword in decorator.keywords:
                if keyword.arg in ["text", "name"] and isinstance(
                    keyword.value, ast.Str
                ):
                    return keyword.value.s
        return None

    def _process_scenario(
        self, node: ast.FunctionDef, decorator: ast.Call
    ) -> None:
        """
        Process a scenario decorator.

        Pre-conditions:
        - node is an instance of ast.FunctionDef
        - decorator is an instance of ast.Call

        Post-conditions:
        - If a valid scenario name is extracted, a new entry is added
          to self.scenarios
        - If no valid scenario name is extracted, a warning is printed
        """

        scenario_name = None
        if decorator.args:
            # Handle positional arguments
            if len(decorator.args) >= 2 and isinstance(decorator.args[1], ast.Str):
                scenario_name = decorator.args[1].s
        else:
            # Handle keyword arguments
            for keyword in decorator.keywords:
                if keyword.arg == "scenario_name" and isinstance(keyword.value, ast.Str):
                    scenario_name = keyword.value.s
                    break

        if scenario_name is not None:
            self.scenarios[node.name] = scenario_name
        else:
            print(f"Warning: Could not extract scenario name for function {node.name}")

    def _extract_scenario_name(self, decorator: ast.Call) -> Optional[str]:
        """
        Extract the scenario name from a decorator.

        Pre-conditions:
        - decorator is an instance of ast.Call

        Post-conditions:
        - Returns a string if a valid scenario name is found, None otherwise
        """
        assert isinstance(decorator, ast.Call), "Decorator must be a Call"

        if decorator.args:
            if len(decorator.args) >= 2 and isinstance(decorator.args[1], ast.Str):
                return decorator.args[1].s

        for keyword in decorator.keywords:
            if keyword.arg == "scenario_name":
                if isinstance(keyword.value, ast.Str):
                    return keyword.value.s
                elif isinstance(keyword.value, ast.Constant):  # For Python 3.8+
                    return keyword.value.value

        return None

    @staticmethod
    def _get_signature(node: ast.FunctionDef) -> str:
        """
        Get the signature of a function.

        Pre-conditions:
        - node is an instance of ast.FunctionDef

        Post-conditions:
        - Returns a string representation of the function signature
        """
        assert isinstance(node, ast.FunctionDef), "Node must be a FunctionDef"
        args_list = []

        # Handle positional arguments
        for arg in node.args.args:
            args_list.append(arg.arg)

        # Handle *args
        if node.args.vararg:
            args_list.append(f"*{node.args.vararg.arg}")

        # Handle **kwargs
        if node.args.kwarg:
            args_list.append(f"**{node.args.kwarg.arg}")

        args_str = ", ".join(args_list)
        return f"def {node.name}({args_str}):"


class FileScanner:
    """Class to scan the file and extract steps and scenarios."""


    @staticmethod
    def parse_file(filename: str) -> Tuple[List[Dict], Dict[str, str]]:
        logging.debug(f"Entering parse_file for {filename}")
        try:
            with open(filename, "r") as file:
                content = file.read()
            logging.debug("File read successfully")
            tree = ast.parse(content)
            logging.debug("AST parsed successfully")
            visitor = StepVisitor()
            visitor.visit(tree)
            logging.debug("StepVisitor completed")
            return visitor.steps, visitor.scenarios
        except SyntaxError as e:
            logging.error(f"SyntaxError in file {filename}: {str(e)}")
            return [], {}


class FileHandler(ABC):
    @abstractmethod
    def process_file(
        self, input_path: str, output_path: str, repo_root: str
    ) -> None:
        pass


class PythonFileHandler(FileHandler):
    def process_file(
        self, input_path: str, output_path: str, repo_root: str
    ) -> None:
        relative_path = os.path.relpath(input_path, repo_root)
        steps, scenarios = FileScanner.parse_file(input_path)

        if steps or scenarios:
            markdown_content = MarkdownFormatter.generate_markdown(
                relative_path, steps, scenarios
            )
            MarkdownFormatter.write_markdown(markdown_content, output_path)
            print(f"Processed Python file: {relative_path}")
        else:
            print(f"No steps or scenarios found in {relative_path}. Skipping.")


class FeatureFileHandler(FileHandler):
    def process_file(
        self, input_path: str, output_path: str, repo_root: str
    ) -> None:
        relative_path = os.path.relpath(input_path, repo_root)
        try:
            with open(input_path, "r") as feature_file:
                feature_content = feature_file.read()
            markdown_content = MarkdownFormatter.format_feature_file(
                feature_content
            )
            MarkdownFormatter.write_markdown(markdown_content, output_path)
            print(f"Processed feature file: {relative_path}")
        except Exception as e:
            print(f"Error processing feature file {relative_path}: {str(e)}")


class FolderProcessor:
    """Class to process a folder of Python and feature files."""

    def __init__(self):
        self.file_handlers: Dict[str, FileHandler] = {
            ".py": PythonFileHandler(),
            ".feature": FeatureFileHandler(),
        }

    @staticmethod
    def find_repository_root(path: str) -> str:
        """
        Find the root of the repository by looking for .git folder.

        Pre-conditions:
        - path is a valid string representing a file system path

        Post-conditions:
        - Returns a string representing the repository root or the original
          path if no .git folder is found
        """
        current_path = os.path.abspath(path)
        while current_path != "/":
            if os.path.exists(os.path.join(current_path, ".git")):
                return current_path
            current_path = os.path.dirname(current_path)
        return path  # If no .git folder found, return the original path

    def process_folder(self, input_folder: str, output_folder: str) -> None:
        """
        Process all Python and feature files in the given folder.

        Pre-conditions:
        - input_folder is a valid string representing an existing folder
        - output_folder is a valid string representing a writable folder path

        Post-conditions:
        - All eligible files in input_folder are processed and
            corresponding markdown files are created in output_folder
        - An index file is created in the output_folder
        """
        self._ensure_output_folder_exists(output_folder)
        repo_root = self.find_repository_root(input_folder)
        print(f"Repository root: {repo_root}")

        for root, _, files in os.walk(input_folder):
            for filename in files:
                self._process_file(root, filename, output_folder, repo_root)

        PostProcessor.create_index_file(output_folder)

    @staticmethod
    def _ensure_output_folder_exists(output_folder: str) -> None:
        """Ensure the output folder exists, creating it if necessary."""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

    def _process_file(
        self, root: str, filename: str, output_folder: str, repo_root: str
    ) -> None:
        """Process a single file based on its extension."""
        input_path = os.path.join(root, filename)
        file_extension = os.path.splitext(filename)[1]

        if file_extension in self.file_handlers:
            subfolder = "steps" if file_extension == ".py" else "features"
            relative_path = os.path.relpath(input_path, repo_root)
            output_path = os.path.join(
                output_folder,
                subfolder,
                f"{os.path.splitext(relative_path)[0]}.md",
            )
            self.file_handlers[file_extension].process_file(
                input_path, output_path, repo_root
            )


class PostProcessor:
    """Class to post-process generated markdown files and create an index."""

    @staticmethod
    def create_index_file(output_folder: str) -> None:
        feature_files = []
        step_files = []

        for root, _, files in os.walk(output_folder):
            for file in files:
                if file.endswith(".md") and file != "index.md":
                    rel_path = os.path.relpath(os.path.join(root, file), output_folder)
                    if rel_path.startswith("features"):
                        feature_files.append(rel_path)
                    elif rel_path.startswith("steps"):
                        step_files.append(rel_path)

        content = "# Test Documentation Index\n\n"
        content += f"Last updated on: {datetime.now().strftime('%d %B %Y %H:%M:%S')}\n\n"

        if feature_files:
            content += "## Feature Files\n\n"
            for file in sorted(feature_files):
                content += f"- [{os.path.basename(file)}]({file})\n"
            content += "\n"

        if step_files:
            content += "## Step Files\n\n"
            for file in sorted(step_files):
                content += f"- [{os.path.basename(file)}]({file})\n"

        with open(os.path.join(output_folder, "index.md"), "w") as index_file:
            index_file.write(content)

    @staticmethod
    def _generate_nested_list(files: List[str], root_folder: str) -> str:
        """Generate a nested list of files, preserving folder structure."""
        nested_dict = {}
        for file in files:
            parts = file.split(os.sep)
            current_dict = nested_dict
            for part in parts[1:-1]:  # Skip root folder and filename
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
            current_dict[parts[-1]] = file

        return PostProcessor._dict_to_md_list(nested_dict, 0, root_folder)

    @staticmethod
    def _dict_to_md_list(d: Dict, level: int, root_folder: str) -> str:
        """Recursively convert nested dictionary to Markdown list."""
        result = ""
        indent = "  " * level
        for key, value in d.items():
            if isinstance(value, dict):
                result += f"{indent}- {key}/\n"
                result += PostProcessor._dict_to_md_list(
                    value, level + 1, root_folder
                )
            else:
                result += f"{indent}- [{key}]({value})\n"
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate markdown from test steps and feature files in a folder."  # pylint: disable=line-too-long # noqa E501
    )
    parser.add_argument(
        "input_folder",
        help="Path to the input folder containing Python and feature files",
    )
    parser.add_argument(
        "output_folder", help="Path to the output folder for markdown files"
    )
    args = parser.parse_args()

    FolderProcessor().process_folder(args.input_folder, args.output_folder)


if __name__ == "__main__":
    main()
