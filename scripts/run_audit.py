"""
Script to run comprehensive code audit on the project.
"""

from pathlib import Path

from audit.architecture_analyzer import ArchitectureAnalyzer
from audit.quality_analyzer import QualityAnalyzer
from audit.reporters import AuditReport
from audit.security_analyzer import SecurityAnalyzer


def main():
    """Run all analyzers and generate report."""
    project_root = Path(__file__).parent

    print("Starting code audit...")
    print(f"Project root: {project_root}\n")

    # Create audit report
    report = AuditReport(project_name="WMS")

    # Run architecture analysis
    print("Running architecture analysis...")
    arch_analyzer = ArchitectureAnalyzer(project_root)
    arch_results = arch_analyzer.analyze()
    report.add_findings(arch_results["findings"])
    print(f"  - Found {arch_results['layer_violations']} layer violations")
    print(f"  - Found {arch_results['circular_dependencies']} circular dependencies")
    print(f"  - Found {arch_results['tight_coupling_issues']} tight coupling issues\n")

    # Run quality analysis
    print("Running code quality analysis...")
    quality_analyzer = QualityAnalyzer(project_root)
    quality_results = quality_analyzer.analyze()
    report.add_findings(quality_results["findings"])
    print(f"  - Found {quality_results['complexity_issues']} complexity issues")
    print(f"  - Found {quality_results['long_methods']} long methods")
    print(f"  - Found {quality_results['long_parameter_lists']} long parameter lists")
    print(
        f"  - Found {quality_results['duplicate_code_blocks']} duplicate code blocks\n"
    )

    # Run security analysis
    print("Running security analysis...")
    security_analyzer = SecurityAnalyzer(project_root)
    security_results = security_analyzer.analyze()
    report.add_findings(security_results["findings"])
    print(f"  - Found {security_results['credential_issues']} credential issues")
    print(f"  - Found {security_results['sql_injection_risks']} SQL injection risks")
    print(
        f"  - Found {security_results['input_validation_issues']} input validation issues\n"
    )

    # Generate summary
    summary = report.generate_summary()
    print("=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total findings: {summary['total_findings']}")
    print(f"  Critical: {summary['critical']}")
    print(f"  High:     {summary['high']}")
    print(f"  Medium:   {summary['medium']}")
    print(f"  Low:      {summary['low']}")
    print()

    # Save reports
    output_dir = project_root / "audit_reports"
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / "audit_report.json"
    html_path = output_dir / "audit_report.html"

    report.save_json(str(json_path))
    report.save_html(str(html_path))

    print("Reports saved:")
    print(f"  - JSON: {json_path}")
    print(f"  - HTML: {html_path}")
    print("\nAudit complete!")


if __name__ == "__main__":
    main()
