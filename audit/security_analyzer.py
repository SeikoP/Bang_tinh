"""
Security analysis for detecting vulnerabilities and security issues.
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Any, Pattern
from .analyzer import CodeAnalyzer
from .reporters import Finding, RiskLevel


class SecurityAnalyzer(CodeAnalyzer):
    """Analyzer for security vulnerabilities."""
    
    def __init__(self, project_root: Path):
        """Initialize security analyzer."""
        super().__init__(project_root)
        self.credential_issues: List[Finding] = []
        self.sql_injection_risks: List[Finding] = []
        self.input_validation_issues: List[Finding] = []
        
        # Regex patterns for security issues
        self.credential_patterns = [
            (re.compile(r'password\s*=\s*["\'](?!.*\{.*\})([^"\']{3,})["\']', re.IGNORECASE), 'password'),
            (re.compile(r'api[_-]?key\s*=\s*["\'](?!.*\{.*\})([^"\']{10,})["\']', re.IGNORECASE), 'api_key'),
            (re.compile(r'secret\s*=\s*["\'](?!.*\{.*\})([^"\']{10,})["\']', re.IGNORECASE), 'secret'),
            (re.compile(r'token\s*=\s*["\'](?!.*\{.*\})([^"\']{10,})["\']', re.IGNORECASE), 'token'),
            (re.compile(r'auth[_-]?token\s*=\s*["\'](?!.*\{.*\})([^"\']{10,})["\']', re.IGNORECASE), 'auth_token'),
        ]
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            re.compile(r'execute\s*\(\s*["\'].*%s.*["\'].*%', re.IGNORECASE),
            re.compile(r'execute\s*\(\s*["\'].*\+.*["\']', re.IGNORECASE),
            re.compile(r'execute\s*\(\s*f["\']', re.IGNORECASE),
            re.compile(r'execute\s*\(\s*["\'].*\.format\(', re.IGNORECASE),
        ]
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform security analysis.
        
        Returns:
            Dictionary with analysis results
        """
        self.discover_files()
        self._scan_hardcoded_credentials()
        self._detect_sql_injection()
        self._detect_missing_input_validation()
        
        return {
            'total_files': len(self.python_files),
            'credential_issues': len(self.credential_issues),
            'sql_injection_risks': len(self.sql_injection_risks),
            'input_validation_issues': len(self.input_validation_issues),
            'findings': (self.credential_issues + self.sql_injection_risks + 
                        self.input_validation_issues)
        }
    
    def _scan_hardcoded_credentials(self) -> None:
        """Scan for hardcoded credentials using regex patterns."""
        for file_path in self.python_files:
            try:
                content = self.get_file_content(file_path)
                lines = content.split('\n')
                
                rel_path = str(file_path.relative_to(self.project_root))
                
                for line_num, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith('#'):
                        continue
                    
                    for pattern, cred_type in self.credential_patterns:
                        matches = pattern.finditer(line)
                        for match in matches:
                            # Exclude common false positives
                            value = match.group(1) if match.groups() else match.group(0)
                            
                            if self._is_likely_credential(value):
                                finding = Finding(
                                    category="Security",
                                    description=f"Hardcoded {cred_type} detected",
                                    risk_level=RiskLevel.CRITICAL,
                                    file_path=rel_path,
                                    line_number=line_num,
                                    recommendation="Move credentials to environment variables or secure configuration",
                                    details={
                                        'type': cred_type,
                                        'line': line.strip()
                                    }
                                )
                                self.credential_issues.append(finding)
            except Exception:
                pass
    
    def _is_likely_credential(self, value: str) -> bool:
        """Check if value is likely a real credential."""
        # Exclude common test/placeholder values
        false_positives = [
            'password', 'secret', 'token', 'key', 'test', 'example',
            'your_password', 'your_secret', 'changeme', '123456',
            'admin', 'root', 'user', 'default', 'none', 'null'
        ]
        
        value_lower = value.lower()
        
        # Check if it's a placeholder
        for fp in false_positives:
            if fp in value_lower:
                return False
        
        # Check if it's a variable reference
        if '{' in value or '$' in value:
            return False
        
        # Likely a real credential if it has some complexity
        return len(value) >= 8
    
    def _detect_sql_injection(self) -> None:
        """Detect SQL injection vulnerabilities."""
        for file_path in self.python_files:
            try:
                content = self.get_file_content(file_path)
                lines = content.split('\n')
                
                rel_path = str(file_path.relative_to(self.project_root))
                
                # Check for string concatenation in SQL queries
                for line_num, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith('#'):
                        continue
                    
                    # Check for SQL injection patterns
                    for pattern in self.sql_injection_patterns:
                        if pattern.search(line):
                            finding = Finding(
                                category="Security",
                                description="Potential SQL injection vulnerability",
                                risk_level=RiskLevel.CRITICAL,
                                file_path=rel_path,
                                line_number=line_num,
                                recommendation="Use parameterized queries with ? placeholders",
                                details={
                                    'line': line.strip(),
                                    'issue': 'String concatenation or formatting in SQL query'
                                }
                            )
                            self.sql_injection_risks.append(finding)
                            break
                
                # Also check AST for string concatenation in execute calls
                self._check_sql_injection_ast(file_path, content)
                
            except Exception:
                pass
    
    def _check_sql_injection_ast(self, file_path: Path, content: str) -> None:
        """Check for SQL injection using AST analysis."""
        try:
            tree = ast.parse(content)
            rel_path = str(file_path.relative_to(self.project_root))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if it's a cursor.execute or connection.execute call
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr == 'execute' and len(node.args) > 0:
                            first_arg = node.args[0]
                            
                            # Check if first argument uses string concatenation or f-string
                            if isinstance(first_arg, (ast.BinOp, ast.JoinedStr)):
                                finding = Finding(
                                    category="Security",
                                    description="SQL injection risk: dynamic query construction",
                                    risk_level=RiskLevel.CRITICAL,
                                    file_path=rel_path,
                                    line_number=node.lineno,
                                    recommendation="Use parameterized queries instead of string concatenation",
                                    details={
                                        'issue': 'Dynamic SQL query construction detected'
                                    }
                                )
                                self.sql_injection_risks.append(finding)
        except Exception:
            pass
    
    def _detect_missing_input_validation(self) -> None:
        """Detect missing input validation at entry points."""
        for file_path in self.python_files:
            try:
                content = self.get_file_content(file_path)
                tree = ast.parse(content)
                
                rel_path = str(file_path.relative_to(self.project_root))
                
                # Look for functions that accept user input
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Check if function has parameters
                        if len(node.args.args) > 0:
                            # Check if function body has validation
                            has_validation = self._has_input_validation(node)
                            
                            # Check if this is an entry point (UI handler, API endpoint, etc.)
                            is_entry_point = self._is_entry_point(node, content)
                            
                            if is_entry_point and not has_validation:
                                finding = Finding(
                                    category="Security",
                                    description=f"Missing input validation in entry point: {node.name}",
                                    risk_level=RiskLevel.HIGH,
                                    file_path=rel_path,
                                    line_number=node.lineno,
                                    recommendation="Add input validation before processing user data",
                                    details={
                                        'function': node.name,
                                        'parameters': [arg.arg for arg in node.args.args]
                                    }
                                )
                                self.input_validation_issues.append(finding)
            except Exception:
                pass
    
    def _has_input_validation(self, func_node: ast.FunctionDef) -> bool:
        """Check if function has input validation logic."""
        # Look for validation patterns in function body
        validation_indicators = [
            'validate', 'check', 'verify', 'isinstance', 'assert',
            'raise', 'ValueError', 'TypeError', 'ValidationError'
        ]
        
        for node in ast.walk(func_node):
            # Check for validation function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if any(indicator in node.func.id.lower() for indicator in validation_indicators):
                        return True
                elif isinstance(node, ast.Attribute):
                    if any(indicator in node.func.attr.lower() for indicator in validation_indicators):
                        return True
            
            # Check for isinstance checks
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'isinstance':
                    return True
            
            # Check for if statements that might be validation
            if isinstance(node, ast.If):
                # Simple heuristic: if statement in first few lines might be validation
                return True
        
        return False
    
    def _is_entry_point(self, func_node: ast.FunctionDef, content: str) -> bool:
        """Check if function is likely an entry point."""
        func_name = func_node.name.lower()
        
        # Check for common entry point patterns
        entry_point_patterns = [
            'handle', 'on_', 'process', 'submit', 'save', 'create',
            'update', 'delete', 'post', 'get', 'put', 'patch',
            'clicked', 'pressed', 'changed', 'activated'
        ]
        
        # Check function name
        if any(pattern in func_name for pattern in entry_point_patterns):
            return True
        
        # Check for decorators that indicate entry points
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in ('route', 'app', 'api', 'endpoint'):
                    return True
        
        # Check if function is connected to UI signals (PyQt pattern)
        func_name_pattern = f'{func_node.name}'
        if '.connect(' in content and func_name_pattern in content:
            return True
        
        return False
