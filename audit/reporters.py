"""
Audit report generation and formatting.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime
import json


class RiskLevel(Enum):
    """Risk level classification for findings."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class Finding:
    """Represents a single audit finding."""
    category: str
    description: str
    risk_level: RiskLevel
    file_path: str = ""
    line_number: int = 0
    recommendation: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            'category': self.category,
            'description': self.description,
            'risk_level': self.risk_level.value,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'recommendation': self.recommendation,
            'details': self.details
        }


class AuditReport:
    """Structured audit report with findings and recommendations."""
    
    def __init__(self, project_name: str = "Unknown Project"):
        """
        Initialize audit report.
        
        Args:
            project_name: Name of the project being audited
        """
        self.project_name = project_name
        self.timestamp = datetime.now()
        self.findings: List[Finding] = []
        self.summary: Dict[str, Any] = {}
        
    def add_finding(self, finding: Finding) -> None:
        """
        Add a finding to the report.
        
        Args:
            finding: Finding object to add
        """
        self.findings.append(finding)
    
    def add_findings(self, findings: List[Finding]) -> None:
        """
        Add multiple findings to the report.
        
        Args:
            findings: List of Finding objects to add
        """
        self.findings.extend(findings)
    
    def get_findings_by_risk(self, risk_level: RiskLevel) -> List[Finding]:
        """
        Get all findings with specified risk level.
        
        Args:
            risk_level: Risk level to filter by
            
        Returns:
            List of findings with matching risk level
        """
        return [f for f in self.findings if f.risk_level == risk_level]
    
    def get_findings_by_category(self, category: str) -> List[Finding]:
        """
        Get all findings in specified category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of findings in matching category
        """
        return [f for f in self.findings if f.category == category]
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics for the report.
        
        Returns:
            Dictionary with summary statistics
        """
        self.summary = {
            'total_findings': len(self.findings),
            'critical': len(self.get_findings_by_risk(RiskLevel.CRITICAL)),
            'high': len(self.get_findings_by_risk(RiskLevel.HIGH)),
            'medium': len(self.get_findings_by_risk(RiskLevel.MEDIUM)),
            'low': len(self.get_findings_by_risk(RiskLevel.LOW)),
            'categories': self._count_by_category()
        }
        return self.summary
    
    def _count_by_category(self) -> Dict[str, int]:
        """Count findings by category."""
        categories = {}
        for finding in self.findings:
            categories[finding.category] = categories.get(finding.category, 0) + 1
        return categories
    
    def to_json(self) -> str:
        """
        Export report as JSON string.
        
        Returns:
            JSON formatted report
        """
        report_dict = {
            'project_name': self.project_name,
            'timestamp': self.timestamp.isoformat(),
            'summary': self.generate_summary(),
            'findings': [f.to_dict() for f in self.findings]
        }
        return json.dumps(report_dict, indent=2)
    
    def to_html(self) -> str:
        """
        Export report as HTML string.
        
        Returns:
            HTML formatted report
        """
        summary = self.generate_summary()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Audit Report - {self.project_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .finding {{ border-left: 4px solid #ddd; padding: 10px; margin: 10px 0; }}
        .critical {{ border-left-color: #d32f2f; }}
        .high {{ border-left-color: #f57c00; }}
        .medium {{ border-left-color: #fbc02d; }}
        .low {{ border-left-color: #388e3c; }}
        .risk-badge {{ display: inline-block; padding: 3px 8px; border-radius: 3px; 
                      font-size: 12px; font-weight: bold; }}
        .risk-critical {{ background: #d32f2f; color: white; }}
        .risk-high {{ background: #f57c00; color: white; }}
        .risk-medium {{ background: #fbc02d; color: black; }}
        .risk-low {{ background: #388e3c; color: white; }}
    </style>
</head>
<body>
    <h1>Audit Report: {self.project_name}</h1>
    <p>Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Findings: {summary['total_findings']}</p>
        <p>Critical: {summary['critical']} | High: {summary['high']} | 
           Medium: {summary['medium']} | Low: {summary['low']}</p>
    </div>
    
    <h2>Findings</h2>
"""
        
        for finding in self.findings:
            risk_class = finding.risk_level.value.lower()
            html += f"""
    <div class="finding {risk_class}">
        <span class="risk-badge risk-{risk_class}">{finding.risk_level.value}</span>
        <strong>{finding.category}</strong>
        <p>{finding.description}</p>
        <p><em>File: {finding.file_path}</em></p>
        <p><strong>Recommendation:</strong> {finding.recommendation}</p>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html
    
    def save_json(self, output_path: str) -> None:
        """
        Save report as JSON file.
        
        Args:
            output_path: Path to save JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    def save_html(self, output_path: str) -> None:
        """
        Save report as HTML file.
        
        Args:
            output_path: Path to save HTML file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_html())
