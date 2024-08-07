# pylint: skip-file
# flake8: noqa

import ast
import logging
from datetime import datetime
from io import StringIO
from unittest.mock import Mock, call, mock_open, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.experiments.document_steps import (
    FeatureFileHandler,
    FileScanner,
    FolderProcessor,
    MarkdownFormatter,
    PostProcessor,
    PythonFileHandler,
    StepVisitor,
)


@pytest.mark.experiments
class TestMarkdownFormatter:
    @pytest.fixture
    def markdown_formatter(self):
        return MarkdownFormatter()

    @pytest.fixture
    def sample_steps(self):
        return [
            {
                "type": "given",
                "name": "the system is in a stable state",
                "function": "given_stable_system",
                "signature": "def given_stable_system():",
                "docstring": "Ensure the system is in a stable state before the test.",
            },
            {
                "type": "when",
                "name": "the user performs action X",
                "function": "when_user_performs_x",
                "signature": "def when_user_performs_x(action):",
                "docstring": "Simulate the user performing action X.",
            },
            {
                "type": "then",
                "name": "the system should respond with Y",
                "function": "then_system_responds_y",
                "signature": "def then_system_responds_y(expected_response):",
                "docstring": "Verify that the system responds with Y.",
            },
        ]

    @pytest.fixture
    def sample_scenarios(self):
        return {
            "test_scenario_1": "User performs action X and system responds",
            "test_scenario_2": "System handles invalid input gracefully",
        }

    @pytest.fixture
    def sample_feature_content(self):
        return """
        Feature: User Authentication

          Scenario: Successful login
            Given the user is on the login page
            When the user enters valid credentials
            Then the user should be logged in successfully

          Scenario Outline: Failed login attempts
            Given the user is on the login page
            When the user enters "<username>" and "<password>"
            Then the login should fail with message "<error_message>"

            Examples:
              | username | password | error_message           |
              | user1    | wrong    | Invalid password        |
              | nonuser  | pass123  | User does not exist     |
        """

    def test_generate_markdown(self, markdown_formatter, sample_steps, sample_scenarios):
        filepath = "test/path/to/file.py"
        markdown = markdown_formatter.generate_markdown(
            filepath, sample_steps, sample_scenarios
        )

        assert_that(markdown).contains(
            "# Test Steps and Scenarios from test/path/to/file.py",
            "Last updated on:",
            "## Scenarios",
            "User performs action X and system responds",
            "System handles invalid input gracefully",
            "## Steps",
            "### Given: the system is in a stable state",
            "### When: the user performs action X",
            "### Then: the system should respond with Y",
            "**Function:** `given_stable_system`",
            "**Signature:**\n```python\ndef given_stable_system():\n```",
            "Ensure the system is in a stable state before the test.",
        )

    def test_write_markdown(self, markdown_formatter):
        content = "# Test Markdown"
        output_file = "/path/to/output.md"

        mock_open_function = mock_open()
        with patch("builtins.open", mock_open_function):
            with patch("os.makedirs") as mock_makedirs:
                markdown_formatter.write_markdown(content, output_file)

        assert_that(mock_makedirs.call_count).is_equal_to(1)
        assert_that(mock_makedirs.call_args[0][0]).is_equal_to("/path/to")
        assert_that(mock_makedirs.call_args[1]).is_equal_to({"exist_ok": True})

        assert_that(mock_open_function.call_count).is_equal_to(1)
        assert_that(mock_open_function.call_args[0][0]).is_equal_to(
            output_file
        )
        assert_that(mock_open_function.call_args[0][1]).is_equal_to("w")

        assert_that(mock_open_function().write.call_count).is_equal_to(1)
        assert_that(mock_open_function().write.call_args[0][0]).is_equal_to(
            content
        )

    def test_format_feature_file(self, markdown_formatter, sample_feature_content):
        markdown = markdown_formatter.format_feature_file(
            sample_feature_content
        )

        assert_that(markdown).contains(
            "## Feature: User Authentication",
            "### Scenario: Successful login",
            "- Given the user is on the login page",
            "- When the user enters valid credentials",
            "- Then the user should be logged in successfully",
            "### Scenario Outline: Failed login attempts",
            "#### Examples:",
            "| username | password | error_message       |",
            "| user1    | wrong    | Invalid password    |",
            "| nonuser  | pass123  | User does not exist |",
        )

    def test__format_example_table(self, markdown_formatter):
        table_lines = [
            "| header1 | header2 | header3 |",
            "| value1  | value2  | value3  |",
            "| a       | b       | c       |",
        ]
        formatted_table = markdown_formatter._format_example_table(table_lines)

        expected_output = (
            "| header1 | header2 | header3 |\n"
            "| ------- | ------- | ------- |\n"
            "| value1  | value2  | value3  |\n"
            "| a       | b       | c       |\n\n"
        )
        assert_that(formatted_table).is_equal_to(expected_output)

    def test__format_example_table_empty(self, markdown_formatter):
        assert_that(markdown_formatter._format_example_table([])).is_empty()
@pytest.mark.experiments
class TestFileScanner:
    @pytest.fixture
    def valid_python_content(self):
        return """
from pytest_bdd import scenario, given, when, then

@scenario('features/login.feature', 'Successful login')
def test_successful_login():
    pass

@given("the user is on the login page")
def user_on_login_page():
    '''Ensure the user is on the login page'''
    pass

@when("the user enters valid credentials")
def enter_valid_credentials():
    pass

@then("the user should be logged in successfully")
def verify_successful_login():
    '''Check that the user is logged in'''
    pass
"""

    @pytest.fixture
    def syntax_error_content(self):
        return """
def function_with_error(
    print("This will cause a syntax error")
"""

    @pytest.fixture
    def empty_file_content(self):
        return ""

    def test_parse_file_valid_content(self, valid_python_content):
        with patch("builtins.open", mock_open(read_data=valid_python_content)):
            steps, scenarios = FileScanner.parse_file("dummy_file.py")

        assert_that(steps).is_length(3)
        assert_that(scenarios).is_length(1)

        assert_that(steps[0]).contains_entry(
            {
                "type": "given",
            },
            {
                "name": "the user is on the login page",
            },
            {
                "function": "user_on_login_page",
            },
            {
                "docstring": "Ensure the user is on the login page",
            },
        )

        assert_that(steps[1]).contains_entry(
            {
                "type": "when",
            },
            {
                "name": "the user enters valid credentials",
            },
            {
                "function": "enter_valid_credentials",
            },
        )

        assert_that(steps[2]).contains_entry(
            {
                "type": "then",
            },
            {
                "name": "the user should be logged in successfully",
            },
            {
                "function": "verify_successful_login",
            },
            {
                "docstring": "Check that the user is logged in",
            },
        )

        assert_that(scenarios).contains_entry(
            {"test_successful_login": "Successful login"}
        )

    def test_parse_file_syntax_error(self, syntax_error_content):
        with patch("builtins.open", mock_open(read_data=syntax_error_content)):
            steps, scenarios = FileScanner.parse_file(
                "dummy_file_with_error.py"
            )

        assert_that(steps).is_empty()
        assert_that(scenarios).is_empty()

    def test_parse_file_empty(self, empty_file_content):
        with patch("builtins.open", mock_open(read_data=empty_file_content)):
            steps, scenarios = FileScanner.parse_file("empty_file.py")

        assert_that(steps).is_empty()
        assert_that(scenarios).is_empty()
    #
    # @patch("ska_integration_test_harness.experiments.document_steps.StepVisitor")
    # def test_parse_file_correct_extraction(self, mock_step_visitor):
    #     # Setup mock visitor
    #     mock_instance = mock_step_visitor.return_value
    #     mock_instance.steps = [{"type": "given", "name": "a condition"}]
    #     mock_instance.scenarios = {"test_scenario": "Test Scenario"}
    #
    #     with patch("builtins.open", mock_open(read_data="some content")):
    #         steps, scenarios = FileScanner.parse_file("dummy_file.py")
    #
    #     assert_that(steps).is_equal_to(
    #         [{"type": "given", "name": "a condition"}]
    #     )
    #     assert_that(scenarios).is_equal_to({"test_scenario": "Test Scenario"})


@pytest.mark.experiments
class TestStepVisitor:
    @pytest.fixture
    def step_visitor(self):
        return StepVisitor()

    def test_visit_FunctionDef_with_various_decorators(self, step_visitor):
        code = """
@given("a condition")
def given_func():
    pass

@when("an action")
def when_func():
    pass

@then("a result")
def then_func():
    pass

@scenario("feature.feature", "Scenario name")
def test_scenario():
    pass

def regular_function():
    pass
        """
        tree = ast.parse(code)
        step_visitor.visit(tree)

        assert_that(step_visitor.steps).is_length(3)
        assert_that(step_visitor.scenarios).is_length(1)
        assert_that(step_visitor.steps[0]["type"]).is_equal_to("given")
        assert_that(step_visitor.steps[1]["type"]).is_equal_to("when")
        assert_that(step_visitor.steps[2]["type"]).is_equal_to("then")
        assert_that(step_visitor.scenarios).contains_key("test_scenario")

    def test__process_step_with_different_types(self, step_visitor):
        for step_type in ["given", "when", "then"]:
            node = ast.FunctionDef(
                name=f"{step_type}_func",
                args=ast.arguments(
                    args=[], vararg=None, kwarg=None, defaults=[]
                ),
                body=[],
                decorator_list=[
                    ast.Call(
                        func=ast.Name(id=step_type, ctx=ast.Load()),
                        args=[ast.Str(s=f"a {step_type} step")],
                        keywords=[],
                    )
                ],
            )
            step_visitor._process_step(node, node.decorator_list[0])

        assert_that(step_visitor.steps).is_length(3)
        for i, step_type in enumerate(["given", "when", "then"]):
            assert_that(step_visitor.steps[i]).contains_entry(
                {
                    "type": step_type,
                },
                {
                    "name": f"a {step_type} step",
                },
                {
                    "function": f"{step_type}_func",
                },
            )

    def test__extract_step_name_with_different_structures(self, step_visitor):
        # Test with simple string argument
        decorator = ast.Call(
            func=ast.Name(id="given", ctx=ast.Load()),
            args=[ast.Str(s="a simple step")],
            keywords=[],
        )
        assert_that(step_visitor._extract_step_name(decorator)).is_equal_to(
            "a simple step"
        )

        # Test with function call (like _)
        decorator = ast.Call(
            func=ast.Name(id="given", ctx=ast.Load()),
            args=[
                ast.Call(
                    func=ast.Name(id="_", ctx=ast.Load()),
                    args=[ast.Str(s="a translated step")],
                    keywords=[],
                )
            ],
            keywords=[],
        )
        assert_that(step_visitor._extract_step_name(decorator)).is_equal_to(
            "a translated step"
        )

        # Test with keyword argument
        decorator = ast.Call(
            func=ast.Name(id="given", ctx=ast.Load()),
            args=[],
            keywords=[
                ast.keyword(arg="text", value=ast.Str(s="a keyword step"))
            ],
        )
        assert_that(step_visitor._extract_step_name(decorator)).is_equal_to(
            "a keyword step"
        )

    def test__process_scenario_with_different_structures(self, step_visitor):
        # Test with positional arguments
        node = ast.FunctionDef(
            name="test_scenario1",
            args=ast.arguments(args=[], vararg=None, kwarg=None, defaults=[]),
            body=[],
            decorator_list=[
                ast.Call(
                    func=ast.Name(id="scenario", ctx=ast.Load()),
                    args=[
                        ast.Str(s="feature.feature"),
                        ast.Str(s="Scenario 1"),
                    ],
                    keywords=[],
                )
            ],
        )
        step_visitor._process_scenario(node, node.decorator_list[0])
        assert_that(step_visitor.scenarios).contains_entry(
            {"test_scenario1": "Scenario 1"}
        )

        # Reset scenarios dictionary
        step_visitor.scenarios = {}

        # Test with keyword arguments
        node = ast.FunctionDef(
            name="test_scenario2",
            args=ast.arguments(args=[], vararg=None, kwarg=None, defaults=[]),
            body=[],
            decorator_list=[
                ast.Call(
                    func=ast.Name(id="scenario", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="feature_name",
                            value=ast.Str(s="feature.feature"),
                        ),
                        ast.keyword(
                            arg="scenario_name", value=ast.Str(s="Scenario 2")
                        ),
                    ],
                )
            ],
        )
        step_visitor._process_scenario(node, node.decorator_list[0])
        assert_that(step_visitor.scenarios).contains_entry(
            {"test_scenario2": "Scenario 2"}
        )

    def test__extract_scenario_name_with_different_structures(
        self, step_visitor
    ):
        # Test with positional arguments
        decorator = ast.Call(
            func=ast.Name(id="scenario", ctx=ast.Load()),
            args=[ast.Str(s="feature.feature"), ast.Str(s="Scenario 1")],
            keywords=[],
        )
        assert_that(
            step_visitor._extract_scenario_name(decorator)
        ).is_equal_to("Scenario 1")

        # Test with keyword arguments
        decorator = ast.Call(
            func=ast.Name(id="scenario", ctx=ast.Load()),
            args=[],
            keywords=[
                ast.keyword(
                    arg="feature_name", value=ast.Str(s="feature.feature")
                ),
                ast.keyword(
                    arg="scenario_name", value=ast.Str(s="Scenario 2")
                ),
            ],
        )
        assert_that(
            step_visitor._extract_scenario_name(decorator)
        ).is_equal_to("Scenario 2")

    def test__get_signature_with_different_arg_structures(self, step_visitor):
        # Test with no arguments
        node = ast.FunctionDef(
            name="func_no_args",
            args=ast.arguments(args=[], vararg=None, kwarg=None, defaults=[]),
            body=[],
        )
        assert_that(step_visitor._get_signature(node)).is_equal_to(
            "def func_no_args():"
        )

        # Test with positional arguments
        node = ast.FunctionDef(
            name="func_with_args",
            args=ast.arguments(
                args=[ast.arg(arg="arg1"), ast.arg(arg="arg2")],
                vararg=None,
                kwarg=None,
                defaults=[],
            ),
            body=[],
        )
        assert_that(step_visitor._get_signature(node)).is_equal_to(
            "def func_with_args(arg1, arg2):"
        )

        # Test with *args and **kwargs
        node = ast.FunctionDef(
            name="func_with_var_args",
            args=ast.arguments(
                args=[],
                vararg=ast.arg(arg="args"),
                kwarg=ast.arg(arg="kwargs"),
                defaults=[],
            ),
            body=[],
        )
        assert_that(step_visitor._get_signature(node)).is_equal_to(
            "def func_with_var_args(*args, **kwargs):"
        )


@pytest.mark.experiments
class TestFileHandlers:
    @pytest.fixture
    def python_file_handler(self):
        return PythonFileHandler()

    @pytest.fixture
    def feature_file_handler(self):
        return FeatureFileHandler()

    def test_PythonFileHandler_process_file(self, python_file_handler):
        with patch(
            "ska_integration_test_harness.experiments.document_steps.FileScanner.parse_file"
        ) as mock_parse_file, patch(
            "ska_integration_test_harness.experiments.document_steps.MarkdownFormatter.generate_markdown"
        ) as mock_generate_markdown, patch(
            "ska_integration_test_harness.experiments.document_steps.MarkdownFormatter.write_markdown"
        ) as mock_write_markdown:
            mock_parse_file.return_value = (
                ["step1", "step2"],
                {"scenario1": "Scenario 1"},
            )
            mock_generate_markdown.return_value = "# Markdown Content"

            python_file_handler.process_file(
                "input.py", "output.md", "/repo/root"
            )

            mock_parse_file.assert_called_once_with("input.py")
            mock_generate_markdown.assert_called_once_with(
                "../../home/giorgio/DEV/SKA/ska-integration-test-harness/tests/experiments/input.py",
                ["step1", "step2"],
                {"scenario1": "Scenario 1"},
            )
            mock_write_markdown.assert_called_once_with(
                "# Markdown Content", "output.md"
            )

    def test_FeatureFileHandler_process_file(self, feature_file_handler):
        with patch(
            "builtins.open", mock_open(read_data="Feature: Test")
        ) as mock_file, patch(
            "ska_integration_test_harness.experiments.document_steps.MarkdownFormatter.format_feature_file"
        ) as mock_format_feature, patch(
            "ska_integration_test_harness.experiments.document_steps.MarkdownFormatter.write_markdown"
        ) as mock_write_markdown:
            mock_format_feature.return_value = "# Formatted Feature"

            feature_file_handler.process_file(
                "input.feature", "output.md", "/repo/root"
            )

            mock_file.assert_called_once_with("input.feature", "r")
            mock_format_feature.assert_called_once_with("Feature: Test")
            mock_write_markdown.assert_called_once_with(
                "# Formatted Feature", "output.md"
            )


@pytest.mark.experiments
class TestFolderProcessor:
    @pytest.fixture
    def folder_processor(self):
        return FolderProcessor()

    def test_find_repository_root(self, folder_processor):
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = [False, False, True]
            root = folder_processor.find_repository_root("/path/to/folder")
            assert_that(root).is_equal_to("/path")

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            root = folder_processor.find_repository_root("/path/to/folder")
            assert_that(root).is_equal_to("/path/to/folder")

    def test_process_folder(self, folder_processor):
        with patch("os.walk") as mock_walk, patch(
            "ska_integration_test_harness.experiments.document_steps.FolderProcessor._process_file"
        ) as mock_process_file, patch(
            "ska_integration_test_harness.experiments.document_steps.PostProcessor.create_index_file"
        ) as mock_create_index:
            mock_walk.return_value = [
                ("/root", ["dir1"], ["file1.py", "file2.feature"]),
                ("/root/dir1", [], ["file3.py"]),
            ]

            folder_processor.process_folder("/input", "/tmp/xx")

            assert_that(mock_process_file.call_count).is_equal_to(3)
            mock_create_index.assert_called_once_with()

    def test__ensure_output_folder_exists(self, folder_processor):
        with patch("os.path.exists") as mock_exists, patch(
            "os.makedirs"
        ) as mock_makedirs:
            mock_exists.return_value = False
            folder_processor._ensure_output_folder_exists("//tmp/xx")
            mock_makedirs.assert_called_once_with("//tmp/xx")

            mock_exists.return_value = True
            folder_processor._ensure_output_folder_exists("//tmp/xx")
            assert_that(mock_makedirs.call_count).is_equal_to(
                1
            )  # No additional call

    def test__process_file(self, folder_processor):
        mock_handler = Mock()
        folder_processor.file_handlers = {".py": mock_handler}

        folder_processor._process_file(
            "/root", "file.py", "/output", "/repo/root"
        )
        mock_handler.process_file.assert_called_once_with(
            "/root/file.py", "/output/steps/../../root/file.md", "/repo/root"
        )

        mock_handler.reset_mock()
        folder_processor._process_file(
            "/root", "file.txt", "/output", "/repo/root"
        )
        assert_that(mock_handler.process_file.called).is_false()


@pytest.mark.experiments
class TestPostProcessor:
    @pytest.fixture
    def post_processor(self):
        return PostProcessor("/")

    def test_create_index_file(self):
        mock_date = datetime(2023, 1, 1, 0, 0, 0)
        with patch("os.walk") as mock_walk, \
             patch("builtins.open", mock_open()) as mock_file:


            mock_walk.return_value = [
                ("/output", ["features", "steps"], []),
                ("/output/features", [], ["feature1.md", "feature2.md"]),
                ("/output/steps", [], ["step1.md", "step2.md"]),
            ]

            PostProcessor("/output").create_index_file()

            # Check if the file was opened correctly
            mock_file.assert_called_once_with("/output/index.md", "w")

            # Get the file handle
            handle = mock_file()

            # Check that write was called once
            assert_that(handle.write.call_count).is_equal_to(1)

            # Check the content of the write call
            expected_content_prefix = (
                "# Test Documentation Index\n\n")
            expected_content_suffix = ( # let's skip the date
                "## Feature Files\n\n"
                "- features/\n"
                "  - [feature1.md](features/feature1.md)\n"
                "  - [feature2.md](features/feature2.md)\n\n"
                "## Step Files\n\n"
                "- steps/\n"
                "  - [step1.md](steps/step1.md)\n"
                "  - [step2.md](steps/step2.md)\n"
            )
            # assert_that(handle.write.call_args[0][0]).is_equal_to(expected_content)
            assert_that(handle.write.call_args[0][0]).contains(expected_content_prefix).contains(expected_content_suffix)

    def test__generate_nested_list(self, post_processor):
        files = [
            "features/scenario1.md",
            "features/subfolder/scenario2.md",
            "steps/step1.md",
            "steps/subfolder/step2.md",
        ]
        result = PostProcessor("/")._generate_nested_list(files, "root")
        assert_that(result).contains(
            "- [scenario1.md](features/scenario1.md)", "- subfolder/", "  - [scenario2.md](features/subfolder/scenario2.md)"
        )

    def test__dict_to_md_list(self, post_processor):
        nested_dict = {
            "folder1": {
                "file1.md": "path/to/file1.md",
                "subfolder": {"file2.md": "path/to/subfolder/file2.md"},
            },
            "file3.md": "path/to/file3.md",
        }
        result = PostProcessor("/")._dict_to_md_list(nested_dict, 0, "root")
        assert_that(result).contains(
            "- folder1/",
            "  - [file1.md](path/to/file1.md)",
            "  - subfolder/",
            "    - [file2.md](path/to/subfolder/file2.md)",
            "- [file3.md](path/to/file3.md)",
        )
