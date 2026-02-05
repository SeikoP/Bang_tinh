"""
Code quality analysis for detecting code smells and complexity issues.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any, Set
from .analyzer import CodeAnalyzer
from .reporters import Finding, RiskLevel

try:
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False


class QualityAnalyzer(CodeAnalyzer):
    """Analyzer for code quality issues."""
    
    def __init__(self, project_root: Path):
        """Initialize quality analyzer."""
        super().__init__(project_root)
        self.complexity_issues: List[Finding] = []
        self.duplicate_code: List[Finding] = []
        self.long_methods: List[Finding] = []
        self.long_params: List[Finding] = []
        
        # Thresholds
        self.max_complexity = 10
        self.max_method_lines = 50
        self.max_parameters = 5
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform code quality analysis.
        
        Returns:
            Dictionary with analysis results
        """
        self.discover_files()
        self._analyze_complexity()
        self._detect_long_methods()
        self._detect_long_parameter_lists()
        self._detect_duplicate_code()
        
        return {
            'total_files': len(self.python_files),
            'complexity_issues': len(self.complexity_issues),
            'long_methods': len(self.long_methods),
            'long_parameter_lists': len(self.long_params),
            'duplicate_code_blocks': len(self.duplicate_code),
            'findings': (self.complexity_issues + self.long_methods + 
                        self.long_params + self.duplicate_code)
        }
    
    def _analyze_complexity(self) -> None:
        """Analyze cyclomatic complexity using radon."""
        if not RADON_AVAILABLE:
            # Fallback to basic AST analysis
            self._analyze_complexity_ast()
            return
        
        for file_path in self.python_files:
            try:
                content = self.get_file_content(file_path)
                results = cc_visit(content)
                
                rel_path = str(file_path.relative_to(self.project_root))
                
                for result in results:
                    if result.complexity > self.max_complexity:
                        risk = self._classify_complexity_risk(result.complexity)
                        
                        finding = Finding(
                            category="Code Quality",
                            description=f"High cyclomatic complexity ({result.complexity}) in {result.name}",
                            risk_level=risk,
                            file_path=rel_path,
                            line_number=result.lineno,
                            recommendation=f"Refactor to reduce complexity below {self.max_complexity}",
                            details={
                                'complexity': result.complexity,
                                'function': result.name,
                                'type': result.classname or 'function'
                            }
                        )
                        self.complexity_issues.append(finding)
            except Exception as e:
                # Skip files that can't be analyzed
                pass
    
    def _analyze_complexity_ast(self) -> None:
        """Fallback complexity analysis using AST."""
        for file_path in self.python_files:
            try:
                content = self.get_file_content(file_path)
                tree = ast.parse(content)
                
                rel_path = str(file_path.relative_to(self.project_root))
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        complexity = self._calculate_complexity(node)
                        
                        if complexity > self.max_complexity:
                            risk = self._classify_complexity_risk(complexity)
                            
                            finding = Finding(
                                category="Code Quality",
                                description=f"High cyclomatic complexity ({complexity}) in {node.name}",
                                risk_level=risk,
                                file_path=rel_path,
                                line_number=node.lineno,
                                recommendation=f"Refactor to reduce complexity below {self.max_complexity}",
                                details={
                                    'complexity': complexity,
                                    'function': node.name
                                }
                            )
                            self.complexity_issues.append(finding)
            except Exception:
                pass
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate basic cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Count decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _classify_complexity_risk(self, complexity: int) -> RiskLevel:
        """Classify risk level based on complexity."""
        if complexity > 20:
            return RiskLevel.CRITICAL
        elif complexity > 15:
            return RiskLevel.HIGH
        elif complexity > 10:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _detect_long_methods(self) -> None:
        """Detect methods exceeding line count threshold."""
        for file_path in self.python_files:
            try:
                content = self.get_file_content(file_path)
                tree = ast.parse(content)
                lines = content.split('\n')
                
                rel_path = str(file_path.relative_to(self.project_root))
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Calculate method length
                        if hasattr(node, 'end_lineno') and node.end_lineno:
                            method_lines = node.end_lineno - node.lineno + 1
                        else:
                            # Fallback for older Python versions
                            method_lines = self._count_method_lines(node, lines)
                        
                        if method_lines > self.max_method_lines:
                            risk = RiskLevel.MEDIUM if method_lines > 100 else RiskLevel.LOW
                            
                            finding = Finding(
                                category="Code Quality",
                                description=f"Long method ({method_lines} lines): {node.name}",
                                risk_level=risk,
                                file_path=rel_path,
                                line_number=node.lineno,
                                recommendation=f"Refactor into smaller methods (target < {self.max_method_lines} lines)",
                                details={
                                    'lines': method_lines,
                                    'name': node.name,
                                    'type': 'class' if isinstance(node, ast.ClassDef) else 'function'
                                }
                            )
                            self.long_methods.append(finding)
            except Exception:
                pass
    
    def _count_method_lines(self, node: ast.AST, lines: List[str]) -> int:
        """Count non-empty lines in a method."""
        start = node.lineno - 1
        # Estimate end by looking for next def or class
        end = len(lines)
        
        count = 0
        for i in range(start, min(end, start + 200)):
            line = lines[i].strip()
            if line and not line.startswith('#'):
                count += 1
        
        return count
    
    def _detect_long_parameter_lists(self) -> None:
        """Detect functions with too many parameters."""
        for file_path in self.python_files:
            try:
                content = self.get_file_content(file_path)
                tree = ast.parse(content)
                
                rel_path = str(file_path.relative_to(self.project_root))
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        param_count = len(node.args.args)
                        
                        # Exclude 'self' and 'cls' from count
                        if param_count > 0:
                            first_param = node.args.args[0].arg
                            if first_param in ('self', 'cls'):
                                param_count -= 1
                        
                        if param_count > self.max_parameters:
                            risk = RiskLevel.MEDIUM if param_count > 8 else RiskLevel.LOW
                            
                            finding = Finding(
                                category="Code Quality",
                                description=f"Long parameter list ({param_count} params) in {node.name}",
                                risk_level=risk,
                                file_path=rel_path,
                                line_number=node.lineno,
                                recommendation=f"Refactor to use parameter object or reduce to < {self.max_parameters} params",
                                details={
                                    'parameter_count': param_count,
                                    'function': node.name
                                }
                            )
                            self.long_params.append(finding)
            except Exception:
                pass
    
    def _detect_duplicate_code(self) -> None:
        """Detect duplicate code blocks."""
        # Simple duplicate detection based on code hashing
        code_blocks: Dict[int, List[tuple]] = {}
        
        for file_path in self.python_files:
            try:
                content = self.get_file_content(file_path)
                lines = content.split('\n')
                
                rel_path = str(file_path.relative_to(self.project_root))
                
                # Look for duplicate blocks of 5+ lines
                block_size = 5
                for i in range(len(lines) - block_size + 1):
                    block = '\n'.join(lines[i:i+block_size])
                    # Normalize whitespace for comparison
                    normalized = ' '.join(block.split())
                    
                    # Skip empty or comment-only blocks
                    if not normalized or normalized.startswith('#'):
                        continue
                    
                    block_hash = hash(normalized)
                    
                    if block_hash not in code_blocks:
                        code_blocks[block_hash] = []
                    
                    code_blocks[block_hash].append((rel_path, i + 1, block))
                
            except Exception:
                pass
        
        # Report duplicates
        for block_hash, occurrences in code_blocks.items():
            if len(occurrences) > 1:
                # Found duplicate
                first_file, first_line, block_content = occurrences[0]
                
                locations = [f"{f}:{l}" for f, l, _ in occurrences]
                
                finding = Finding(
                    category="Code Quality",
                    description=f"Duplicate code block found in {len(occurrences)} locations",
                    risk_level=RiskLevel.LOW,
                    file_path=first_file,
                    line_number=first_line,
                    recommendation="Extract duplicate code into a shared function or method",
                    details={
                        'occurrences': len(occurrences),
                        'locations': locations,
                        'preview': block_content[:100]
                    }
                )
                self.duplicate_code.append(finding)
