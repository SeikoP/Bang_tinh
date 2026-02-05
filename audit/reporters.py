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
        Export report as HTML string with enhanced styling and interactivity.
        
        Returns:
            HTML formatted report
        """
        summary = self.generate_summary()
        
        # Group findings by category and risk level
        findings_by_category = {}
        for finding in self.findings:
            if finding.category not in findings_by_category:
                findings_by_category[finding.category] = []
            findings_by_category[finding.category].append(finding)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audit Report - {self.project_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .header .meta {{
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            text-align: center;
        }}
        
        .summary-card .number {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .summary-card .label {{
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .summary-card.total .number {{ color: #667eea; }}
        .summary-card.critical .number {{ color: #d32f2f; }}
        .summary-card.high .number {{ color: #f57c00; }}
        .summary-card.medium .number {{ color: #fbc02d; }}
        .summary-card.low .number {{ color: #388e3c; }}
        
        .filters {{
            padding: 20px 30px;
            background: white;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .filters label {{
            font-weight: 600;
            margin-right: 10px;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: 2px solid #e0e0e0;
            background: white;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }}
        
        .filter-btn:hover {{
            border-color: #667eea;
            color: #667eea;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .category-section {{
            margin-bottom: 40px;
        }}
        
        .category-header {{
            font-size: 24px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        .finding {{
            background: white;
            border-left: 4px solid #ddd;
            padding: 20px;
            margin: 15px 0;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .finding:hover {{
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        .finding.critical {{ border-left-color: #d32f2f; }}
        .finding.high {{ border-left-color: #f57c00; }}
        .finding.medium {{ border-left-color: #fbc02d; }}
        .finding.low {{ border-left-color: #388e3c; }}
        
        .finding-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .risk-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .risk-critical {{
            background: #d32f2f;
            color: white;
        }}
        
        .risk-high {{
            background: #f57c00;
            color: white;
        }}
        
        .risk-medium {{
            background: #fbc02d;
            color: #333;
        }}
        
        .risk-low {{
            background: #388e3c;
            color: white;
        }}
        
        .finding-description {{
            font-size: 16px;
            color: #333;
            margin-bottom: 10px;
            font-weight: 500;
        }}
        
        .finding-location {{
            color: #666;
            font-size: 14px;
            margin-bottom: 12px;
            font-family: 'Courier New', monospace;
        }}
        
        .finding-recommendation {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 4px;
            margin-top: 12px;
            border-left: 3px solid #667eea;
        }}
        
        .finding-recommendation strong {{
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }}
        
        .finding-details {{
            margin-top: 12px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 13px;
            color: #666;
        }}
        
        .no-findings {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-style: italic;
        }}
        
        @media (max-width: 768px) {{
            .summary {{
                grid-template-columns: 1fr;
            }}
            
            .filters {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .filter-btn {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Code Audit Report</h1>
            <div class="meta">
                <strong>Project:</strong> {self.project_name}<br>
                <strong>Generated:</strong> {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <div class="number">{summary['total_findings']}</div>
                <div class="label">Total Findings</div>
            </div>
            <div class="summary-card critical">
                <div class="number">{summary['critical']}</div>
                <div class="label">Critical</div>
            </div>
            <div class="summary-card high">
                <div class="number">{summary['high']}</div>
                <div class="label">High</div>
            </div>
            <div class="summary-card medium">
                <div class="number">{summary['medium']}</div>
                <div class="label">Medium</div>
            </div>
            <div class="summary-card low">
                <div class="number">{summary['low']}</div>
                <div class="label">Low</div>
            </div>
        </div>
        
        <div class="filters">
            <label>Filter by Risk:</label>
            <button class="filter-btn active" onclick="filterFindings('all')">All</button>
            <button class="filter-btn" onclick="filterFindings('critical')">Critical</button>
            <button class="filter-btn" onclick="filterFindings('high')">High</button>
            <button class="filter-btn" onclick="filterFindings('medium')">Medium</button>
            <button class="filter-btn" onclick="filterFindings('low')">Low</button>
        </div>
        
        <div class="content">
"""
        
        # Generate findings by category
        for category, category_findings in sorted(findings_by_category.items()):
            html += f"""
            <div class="category-section">
                <h2 class="category-header">{category} ({len(category_findings)} findings)</h2>
"""
            
            # Sort findings by risk level (Critical > High > Medium > Low)
            risk_order = {RiskLevel.CRITICAL: 0, RiskLevel.HIGH: 1, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 3}
            sorted_findings = sorted(category_findings, key=lambda f: risk_order[f.risk_level])
            
            for finding in sorted_findings:
                risk_class = finding.risk_level.value.lower()
                location = f"{finding.file_path}"
                if finding.line_number > 0:
                    location += f":{finding.line_number}"
                
                details_html = ""
                if finding.details:
                    details_items = []
                    for key, value in finding.details.items():
                        if isinstance(value, (list, dict)):
                            continue  # Skip complex structures for display
                        details_items.append(f"<strong>{key}:</strong> {value}")
                    if details_items:
                        details_html = f"""
                <div class="finding-details">
                    {' | '.join(details_items)}
                </div>
"""
                
                html += f"""
                <div class="finding {risk_class}" data-risk="{risk_class}">
                    <div class="finding-header">
                        <span class="risk-badge risk-{risk_class}">{finding.risk_level.value}</span>
                    </div>
                    <div class="finding-description">{finding.description}</div>
                    <div class="finding-location">📁 {location}</div>
                    {details_html}
                    <div class="finding-recommendation">
                        <strong>💡 Recommendation:</strong>
                        {finding.recommendation}
                    </div>
                </div>
"""
            
            html += """
            </div>
"""
        
        if not self.findings:
            html += """
            <div class="no-findings">
                ✅ No findings detected. Great job!
            </div>
"""
        
        html += """
        </div>
    </div>
    
    <script>
        function filterFindings(risk) {
            // Update active button
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Filter findings
            const findings = document.querySelectorAll('.finding');
            findings.forEach(finding => {
                if (risk === 'all' || finding.dataset.risk === risk) {
                    finding.style.display = 'block';
                } else {
                    finding.style.display = 'none';
                }
            });
            
            // Update category sections visibility
            document.querySelectorAll('.category-section').forEach(section => {
                const visibleFindings = section.querySelectorAll('.finding[style="display: block;"], .finding:not([style])');
                const hasVisible = risk === 'all' || Array.from(visibleFindings).some(f => 
                    f.dataset.risk === risk || f.style.display !== 'none'
                );
                section.style.display = hasVisible ? 'block' : 'none';
            });
        }
    </script>
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
