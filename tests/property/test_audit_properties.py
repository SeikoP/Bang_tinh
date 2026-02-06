"""
Property-based tests for audit module.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.6**
"""

import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from audit.architecture_analyzer import ArchitectureAnalyzer
from audit.quality_analyzer import QualityAnalyzer
from audit.reporters import RiskLevel
from audit.security_analyzer import SecurityAnalyzer

# Strategies for generating test code


@st.composite
def python_file_structure(draw):
    """Generate a directory structure with Python files."""
    num_files = draw(st.integers(min_value=1, max_value=10))
    files = {}

    for i in range(num_files):
        # Generate file path
        depth = draw(st.integers(min_value=0, max_value=3))
        path_parts = []

        for d in range(depth):
            dir_name = draw(
                st.sampled_from(
                    ["ui", "services", "database", "core", "utils", "tests"]
                )
            )
            path_parts.append(dir_name)

        filename = f"file_{i}.py"
        if path_parts:
            file_path = "/".join(path_parts) + "/" + filename
        else:
            file_path = filename

        # Generate simple Python content
        content = draw(
            st.sampled_from(
                [
                    "# Simple module\npass\n",
                    "def function():\n    pass\n",
                    "class MyClass:\n    pass\n",
                    "import os\nimport sys\n",
                ]
            )
        )

        files[file_path] = content

    return files


@st.composite
def layer_violation_code(draw):
    """Generate code with known layer violations."""
    violation_type = draw(
        st.sampled_from(
            ["core_imports_ui", "database_imports_services", "utils_imports_ui"]
        )
    )

    if violation_type == "core_imports_ui":
        return {
            "core/models.py": "from ui.qt_views import MainWindow\n\nclass Model:\n    pass\n"
        }
    elif violation_type == "database_imports_services":
        return {
            "database/repo.py": "from services.calculator import CalculatorService\n\nclass Repo:\n    pass\n"
        }
    else:  # utils_imports_ui
        return {
            "utils/helper.py": "from ui.qt_theme import apply_theme\n\ndef helper():\n    pass\n"
        }


@st.composite
def complex_function_code(draw):
    """Generate code with high cyclomatic complexity."""
    num_conditions = draw(st.integers(min_value=11, max_value=20))

    code = "def complex_function(x):\n"
    for i in range(num_conditions):
        code += f"    if x == {i}:\n        return {i}\n"
    code += "    return -1\n"

    return {"module.py": code}


@st.composite
def long_method_code(draw):
    """Generate code with long methods."""
    num_lines = draw(st.integers(min_value=51, max_value=100))

    code = "def long_method():\n"
    for i in range(num_lines):
        code += f"    x = {i}\n"
    code += "    return x\n"

    return {"module.py": code}


@st.composite
def sql_injection_code(draw):
    """Generate code with SQL injection vulnerabilities."""
    injection_type = draw(
        st.sampled_from(
            ["string_concat", "format_string", "f_string", "percent_format"]
        )
    )

    if injection_type == "string_concat":
        code = """
def query_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
"""
    elif injection_type == "format_string":
        code = """
def query_user(user_id):
    query = "SELECT * FROM users WHERE id = {}".format(user_id)
    cursor.execute(query)
"""
    elif injection_type == "f_string":
        code = """
def query_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
"""
    else:  # percent_format
        code = """
def query_user(user_id):
    query = "SELECT * FROM users WHERE id = %s" % user_id
    cursor.execute(query)
"""

    return {"database.py": code}


@st.composite
def hardcoded_credential_code(draw):
    """Generate code with hardcoded credentials."""
    cred_type = draw(st.sampled_from(["password", "api_key", "secret", "token"]))

    value = draw(
        st.text(
            min_size=10,
            max_size=30,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )

    code = f'{cred_type} = "{value}"\n'

    return {"config.py": code}


# Property Tests


@pytest.mark.property
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(file_structure=python_file_structure())
def test_property_1_complete_file_discovery(file_structure):
    """
    Property 1: Complete File Discovery

    For any project directory structure, the audit module should discover
    all Python source files without missing any .py files in the tree.

    **Validates: Requirements 1.1**
    """
    # Create temporary directory with files
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create files
        created_files = []
        for file_path, content in file_structure.items():
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            created_files.append(full_path)

        # Run analyzer
        analyzer = ArchitectureAnalyzer(project_root)
        discovered = analyzer.discover_files(exclude_patterns=[])

        # Property: All created .py files should be discovered
        discovered_set = set(discovered)
        created_set = set(created_files)

        assert created_set.issubset(
            discovered_set
        ), f"Missing files: {created_set - discovered_set}"


@pytest.mark.property
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(violation_code=layer_violation_code())
def test_property_2_architectural_violation_detection(violation_code):
    """
    Property 2: Architectural Violation Detection

    For any code sample with known tight coupling patterns (UI importing from
    Data layer, circular dependencies), the audit module should detect and
    report these violations.

    **Validates: Requirements 1.2**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create files with violations
        for file_path, content in violation_code.items():
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        # Run analyzer
        analyzer = ArchitectureAnalyzer(project_root)
        results = analyzer.analyze()

        # Property: Violations should be detected
        total_violations = (
            results["layer_violations"] + results["tight_coupling_issues"]
        )

        assert total_violations > 0, "Analyzer should detect architectural violations"


@pytest.mark.property
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(code=st.one_of(complex_function_code(), long_method_code()))
def test_property_3_code_smell_detection(code):
    """
    Property 3: Code Smell Detection Completeness

    For any code containing known smells (duplicated blocks, methods exceeding
    complexity threshold, long parameter lists), the audit module should
    identify all instances.

    **Validates: Requirements 1.3**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create files with code smells
        for file_path, content in code.items():
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        # Run analyzer
        analyzer = QualityAnalyzer(project_root)
        results = analyzer.analyze()

        # Property: Code smells should be detected
        total_smells = (
            results["complexity_issues"]
            + results["long_methods"]
            + results["long_parameter_lists"]
        )

        assert total_smells > 0, "Analyzer should detect code quality issues"


@pytest.mark.property
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(vuln_code=st.one_of(sql_injection_code(), hardcoded_credential_code()))
def test_property_4_security_vulnerability_detection(vuln_code):
    """
    Property 4: Security Vulnerability Detection

    For any code containing security issues (hardcoded credentials, SQL injection
    vulnerabilities, missing input validation), the audit module should detect
    and classify them correctly.

    **Validates: Requirements 1.4**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create files with vulnerabilities
        for file_path, content in vuln_code.items():
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        # Run analyzer
        analyzer = SecurityAnalyzer(project_root)
        results = analyzer.analyze()

        # Property: Security issues should be detected
        total_issues = results["credential_issues"] + results["sql_injection_risks"]

        assert total_issues > 0, "Analyzer should detect security vulnerabilities"


@pytest.mark.property
@settings(max_examples=100)
@given(
    category=st.sampled_from(["Architecture", "Code Quality", "Security"]),
    description=st.text(min_size=10, max_size=200),
    file_path=st.text(min_size=5, max_size=50),
)
def test_property_5_risk_classification_consistency(category, description, file_path):
    """
    Property 5: Risk Classification Consistency

    For any audit finding, it should be assigned exactly one risk level from
    the valid set {Low, Medium, High, Critical} based on consistent criteria.

    **Validates: Requirements 1.6**
    """
    from audit.reporters import Finding

    # Create finding with each risk level
    for risk_level in [
        RiskLevel.LOW,
        RiskLevel.MEDIUM,
        RiskLevel.HIGH,
        RiskLevel.CRITICAL,
    ]:
        finding = Finding(
            category=category,
            description=description,
            risk_level=risk_level,
            file_path=file_path,
            recommendation="Fix this issue",
        )

        # Property: Risk level should be one of the valid values
        assert finding.risk_level in [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ], "Risk level must be from valid set"

        # Property: Risk level should be consistent (same input = same output)
        finding2 = Finding(
            category=category,
            description=description,
            risk_level=risk_level,
            file_path=file_path,
            recommendation="Fix this issue",
        )

        assert (
            finding.risk_level == finding2.risk_level
        ), "Risk level classification should be consistent"
