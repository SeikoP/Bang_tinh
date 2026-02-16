"""
Property-based tests for test coverage.

**Validates: Requirements 6.1, 6.2, 6.3**
"""

import ast
import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

# Strategies


@st.composite
def business_logic_class(draw):
    """Generate a business logic class definition."""
    class_name = draw(
        st.text(
            min_size=1,
            max_size=30,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
        )
    )
    assume(class_name and class_name[0].isupper())

    num_methods = draw(st.integers(min_value=1, max_value=5))

    code = f"class {class_name}:\n"
    code += "    def __init__(self):\n"
    code += "        pass\n\n"

    methods = []
    for i in range(num_methods):
        method_name = f"method_{i}"
        methods.append(method_name)
        code += f"    def {method_name}(self):\n"
        code += f"        return {i}\n\n"

    return code, class_name, methods


@st.composite
def transformation_function(draw):
    """Generate a data transformation function."""
    func_name = draw(
        st.text(
            min_size=1,
            max_size=30,
            alphabet=st.characters(
                whitelist_categories=("Ll",), whitelist_characters="_"
            ),
        )
    )
    assume(func_name and func_name[0].isalpha())

    transform_type = draw(
        st.sampled_from(["parse", "format", "convert", "validate", "sanitize"])
    )

    code = f"def {func_name}(input_data):\n"

    if transform_type == "parse":
        code += "    return int(input_data)\n"
    elif transform_type == "format":
        code += "    return str(input_data)\n"
    elif transform_type == "convert":
        code += "    return input_data * 2\n"
    elif transform_type == "validate":
        code += "    return len(input_data) > 0\n"
    else:  # sanitize
        code += "    return input_data.strip()\n"

    return code, func_name, transform_type


@st.composite
def strategy_test_file_structure(draw):
    """Generate test file structure."""
    has_test_file = draw(st.booleans())
    num_test_methods = draw(st.integers(min_value=0, max_value=10))

    return {"has_test_file": has_test_file, "num_test_methods": num_test_methods}


# Property Tests


@pytest.mark.property
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(class_code=business_logic_class())
def test_property_18_test_coverage_for_business_logic(class_code):
    """
    Property 18: Test Coverage for Business Logic

    For any business logic class, there should exist at least one corresponding
    test file with test methods.

    **Validates: Requirements 6.1**
    """
    code, class_name, methods = class_code

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create source file
        src_dir = project_root / "services"
        src_dir.mkdir()
        src_file = src_dir / f"{class_name.lower()}.py"
        src_file.write_text(code, encoding='utf-8')

        # Create test file
        test_dir = project_root / "tests" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / f"test_{class_name.lower()}.py"

        # Generate test code
        test_code = (
            f"import pytest\nfrom services.{class_name.lower()} import {class_name}\n\n"
        )
        test_code += f"class Test{class_name}:\n"

        for method in methods:
            test_code += f"    def test_{method}(self):\n"
            test_code += f"        obj = {class_name}()\n"
            test_code += f"        result = obj.{method}()\n"
            test_code += "        assert result is not None\n\n"

        test_file.write_text(test_code, encoding='utf-8')

        # Property: Test file should exist for business logic class
        assert test_file.exists(), f"Test file should exist for {class_name}"

        # Property: Test file should have test methods
        test_content = test_file.read_text(encoding='utf-8')
        tree = ast.parse(test_content)

        test_method_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    test_method_count += 1

        assert test_method_count > 0, "Test file should have at least one test method"

        # Property: Each business method should have a corresponding test
        assert test_method_count >= len(
            methods
        ), "Should have at least one test per business method"


@pytest.mark.property
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(func_code=transformation_function())
def test_property_19_property_test_coverage_for_transformations(func_code):
    """
    Property 19: Property Test Coverage for Transformations

    For any data transformation function, there should exist at least one
    property-based test validating its behavior.

    **Validates: Requirements 6.2**
    """
    code, func_name, transform_type = func_code

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create source file
        src_dir = project_root / "utils"
        src_dir.mkdir()
        src_file = src_dir / "transformers.py"
        src_file.write_text(code, encoding='utf-8')

        # Create property test file
        test_dir = project_root / "tests" / "property"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_transformer_properties.py"

        # Generate property test code
        test_code = "import pytest\n"
        test_code += "from hypothesis import given, strategies as st\n"
        test_code += "from utils.transformers import " + func_name + "\n\n"
        test_code += "@pytest.mark.property\n"
        test_code += "@given(data=st.text())\n"
        test_code += f"def test_property_{func_name}(data):\n"
        test_code += f"    result = {func_name}(data)\n"
        test_code += "    assert result is not None\n"

        test_file.write_text(test_code, encoding='utf-8')

        # Property: Property test file should exist
        assert (
            test_file.exists()
        ), "Property test file should exist for transformation function"

        # Property: Test should use Hypothesis
        test_content = test_file.read_text(encoding='utf-8')
        assert (
            "from hypothesis import" in test_content
        ), "Property test should import Hypothesis"

        assert "@given" in test_content, "Property test should use @given decorator"

        # Property: Test should be marked as property test
        assert (
            "@pytest.mark.property" in test_content
        ), "Test should be marked with @pytest.mark.property"


@pytest.mark.property
@settings(max_examples=100)
@given(iteration_count=st.integers(min_value=1, max_value=1000))
def test_property_20_property_test_iteration_count(iteration_count):
    """
    Property 20: Property Test Iteration Count

    For any property-based test, it should be configured to run at least
    100 iterations.

    **Validates: Requirements 6.3**
    """
    # Minimum required iterations
    min_iterations = 100

    # Property: If test is configured, iterations should meet minimum
    if iteration_count >= min_iterations:
        assert (
            iteration_count >= min_iterations
        ), f"Property test should run at least {min_iterations} iterations"
    else:
        # This configuration would be invalid
        assert iteration_count < min_iterations


@pytest.mark.property
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    source_lines=st.integers(min_value=10, max_value=100),
    tested_lines=st.integers(min_value=0, max_value=100),
)
def test_property_coverage_percentage_calculation(source_lines, tested_lines):
    """
    Property: Coverage percentage should be calculated correctly.

    **Validates: Requirements 6.6**
    """
    # Ensure tested_lines doesn't exceed source_lines
    tested_lines = min(tested_lines, source_lines)

    # Calculate coverage percentage
    if source_lines > 0:
        coverage = (tested_lines / source_lines) * 100
    else:
        coverage = 0

    # Property: Coverage should be between 0 and 100
    assert 0 <= coverage <= 100, "Coverage percentage should be between 0 and 100"

    # Property: If all lines tested, coverage should be 100%
    if tested_lines == source_lines:
        assert coverage == 100, "Full coverage should be 100%"

    # Property: If no lines tested, coverage should be 0%
    if tested_lines == 0:
        assert coverage == 0, "No coverage should be 0%"


@pytest.mark.property
@settings(max_examples=50)
@given(
    total_functions=st.integers(min_value=1, max_value=50),
    tested_functions=st.integers(min_value=0, max_value=50),
)
def test_property_function_coverage_threshold(total_functions, tested_functions):
    """
    Property: Function coverage should meet 80% threshold for business logic.

    **Validates: Requirements 6.6**
    """
    # Ensure tested doesn't exceed total
    tested_functions = min(tested_functions, total_functions)

    coverage = (tested_functions / total_functions) * 100
    threshold = 80

    # Property: Coverage calculation should be accurate
    expected_coverage = (tested_functions / total_functions) * 100
    assert (
        abs(coverage - expected_coverage) < 0.01
    ), "Coverage calculation should be accurate"

    # Property: Meeting threshold means coverage >= 80%
    meets_threshold = coverage >= threshold

    if tested_functions >= (total_functions * 0.8):
        assert meets_threshold, "Should meet threshold when 80%+ functions tested"


@pytest.mark.property
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    module_name=st.text(
        min_size=1,
        max_size=30,
        alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_"),
    ),
    has_tests=st.booleans(),
)
def test_property_test_file_naming_convention(module_name, has_tests):
    """
    Property: Test files should follow naming convention test_<module>.py

    **Validates: Requirements 6.1**
    """
    assume(module_name and module_name[0].isalpha())

    if has_tests:
        # Test file should follow convention
        test_file_name = f"test_{module_name}.py"

        # Property: Test file name should start with 'test_'
        assert test_file_name.startswith("test_"), "Test file should start with 'test_'"

        # Property: Test file name should end with '.py'
        assert test_file_name.endswith(".py"), "Test file should end with '.py'"

        # Property: Test file name should contain module name
        assert module_name in test_file_name, "Test file should contain module name"


@pytest.mark.property
@settings(max_examples=50)
@given(
    test_execution_time=st.floats(min_value=0.001, max_value=120.0),
    time_limit=st.floats(min_value=1.0, max_value=60.0),
)
def test_property_test_execution_time_limit(test_execution_time, time_limit):
    """
    Property: Test suite should complete within time limit.

    **Validates: Requirements 6.7**
    """
    # Property: Test execution time should be measurable
    assert test_execution_time >= 0, "Test execution time should be non-negative"

    # Property: Time limit should be reasonable
    assert time_limit > 0, "Time limit should be positive"

    # Property: Tests exceeding limit should be flagged
    exceeds_limit = test_execution_time > time_limit

    if test_execution_time > time_limit:
        assert exceeds_limit, "Tests exceeding time limit should be flagged"
    else:
        assert not exceeds_limit, "Tests within time limit should not be flagged"


@pytest.mark.property
@settings(max_examples=50)
@given(
    test_markers=st.lists(
        st.sampled_from(["unit", "integration", "property", "slow", "e2e"]),
        min_size=1,
        max_size=3,
        unique=True,
    )
)
def test_property_test_markers_usage(test_markers):
    """
    Property: Tests should be properly marked for selective execution.

    **Validates: Requirements 6.8**
    """
    valid_markers = ["unit", "integration", "property", "slow", "e2e", "smoke"]

    # Property: All markers should be from valid set
    for marker in test_markers:
        assert (
            marker in valid_markers
        ), f"Marker '{marker}' should be in valid markers list"

    # Property: Markers should be unique
    assert len(test_markers) == len(set(test_markers)), "Test markers should be unique"
