"""
Architecture analysis for detecting layer violations and coupling issues.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from .analyzer import CodeAnalyzer
from .reporters import Finding, RiskLevel


class ArchitectureAnalyzer(CodeAnalyzer):
    """Analyzer for detecting architectural issues."""
    
    def __init__(self, project_root: Path):
        """Initialize architecture analyzer."""
        super().__init__(project_root)
        self.imports_map: Dict[str, List[str]] = {}
        self.layer_violations: List[Finding] = []
        self.circular_deps: List[Finding] = []
        self.tight_coupling: List[Finding] = []
        
        # Define layer hierarchy (lower layers should not import from higher layers)
        self.layers = {
            'ui': 3,  # Highest layer
            'services': 2,
            'database': 1,
            'core': 0,  # Lowest layer
            'utils': 0
        }
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform architecture analysis.
        
        Returns:
            Dictionary with analysis results
        """
        self.discover_files()
        self._build_import_map()
        self._detect_layer_violations()
        self._detect_circular_dependencies()
        self._detect_tight_coupling()
        
        return {
            'total_files': len(self.python_files),
            'layer_violations': len(self.layer_violations),
            'circular_dependencies': len(self.circular_deps),
            'tight_coupling_issues': len(self.tight_coupling),
            'findings': self.layer_violations + self.circular_deps + self.tight_coupling
        }
    
    def _build_import_map(self) -> None:
        """Build a map of imports for each file."""
        for file_path in self.python_files:
            try:
                content = self.get_file_content(file_path)
                tree = ast.parse(content)
                imports = self._extract_imports(tree)
                
                # Store relative path as key
                rel_path = str(file_path.relative_to(self.project_root))
                self.imports_map[rel_path] = imports
            except Exception as e:
                # Skip files that can't be parsed
                pass
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    
    def _get_layer(self, file_path: str) -> str:
        """Determine which layer a file belongs to."""
        path_lower = file_path.lower()
        
        if 'ui/' in path_lower or 'qt_views/' in path_lower:
            return 'ui'
        elif 'services/' in path_lower:
            return 'services'
        elif 'database/' in path_lower:
            return 'database'
        elif 'core/' in path_lower:
            return 'core'
        elif 'utils/' in path_lower:
            return 'utils'
        else:
            return 'unknown'
    
    def _detect_layer_violations(self) -> None:
        """Detect violations of layer dependency rules."""
        for file_path, imports in self.imports_map.items():
            source_layer = self._get_layer(file_path)
            
            if source_layer == 'unknown':
                continue
            
            for import_name in imports:
                # Determine target layer from import
                target_layer = self._get_layer_from_import(import_name)
                
                if target_layer == 'unknown':
                    continue
                
                # Check if this violates layer rules
                if self._is_layer_violation(source_layer, target_layer):
                    finding = Finding(
                        category="Architecture",
                        description=f"Layer violation: {source_layer} layer importing from {target_layer} layer",
                        risk_level=RiskLevel.HIGH,
                        file_path=file_path,
                        recommendation=f"Refactor to use dependency injection or move code to appropriate layer",
                        details={
                            'source_layer': source_layer,
                            'target_layer': target_layer,
                            'import': import_name
                        }
                    )
                    self.layer_violations.append(finding)
    
    def _get_layer_from_import(self, import_name: str) -> str:
        """Determine layer from import statement."""
        if import_name.startswith('ui.') or import_name.startswith('qt_views'):
            return 'ui'
        elif import_name.startswith('services.'):
            return 'services'
        elif import_name.startswith('database.'):
            return 'database'
        elif import_name.startswith('core.'):
            return 'core'
        elif import_name.startswith('utils.'):
            return 'utils'
        else:
            return 'unknown'
    
    def _is_layer_violation(self, source: str, target: str) -> bool:
        """Check if importing from target to source violates layer rules."""
        if source not in self.layers or target not in self.layers:
            return False
        
        # Lower layers should not import from higher layers
        # UI (3) can import from services (2), database (1), core (0)
        # Services (2) can import from database (1), core (0)
        # Database (1) can import from core (0)
        # Core (0) should not import from any other layer
        
        source_level = self.layers[source]
        target_level = self.layers[target]
        
        # Violation if lower layer imports from higher layer
        return source_level < target_level
    
    def _detect_circular_dependencies(self) -> None:
        """Detect circular dependencies between modules."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(file_path: str, path: List[str]) -> bool:
            """DFS to detect cycles."""
            visited.add(file_path)
            rec_stack.add(file_path)
            path.append(file_path)
            
            if file_path in self.imports_map:
                for import_name in self.imports_map[file_path]:
                    # Find corresponding file
                    imported_file = self._find_file_for_import(import_name)
                    
                    if imported_file:
                        if imported_file not in visited:
                            if has_cycle(imported_file, path.copy()):
                                return True
                        elif imported_file in rec_stack:
                            # Found cycle
                            if imported_file in path:
                                cycle_start = path.index(imported_file)
                                cycle = path[cycle_start:] + [imported_file]
                                self._add_circular_dependency_finding(cycle)
                            return True
            
            rec_stack.remove(file_path)
            return False
        
        for file_path in self.imports_map.keys():
            if file_path not in visited:
                has_cycle(file_path, [])
    
    def _find_file_for_import(self, import_name: str) -> str:
        """Find file path corresponding to an import."""
        # Convert import to file path
        parts = import_name.split('.')
        
        for file_path in self.imports_map.keys():
            file_parts = file_path.replace('\\', '/').replace('.py', '').split('/')
            
            # Check if import matches file path
            if all(part in file_parts for part in parts):
                return file_path
        
        return None
    
    def _add_circular_dependency_finding(self, cycle: List[str]) -> None:
        """Add finding for circular dependency."""
        finding = Finding(
            category="Architecture",
            description=f"Circular dependency detected: {' -> '.join(cycle)}",
            risk_level=RiskLevel.MEDIUM,
            file_path=cycle[0],
            recommendation="Refactor to break circular dependency using interfaces or dependency injection",
            details={'cycle': cycle}
        )
        self.circular_deps.append(finding)
    
    def _detect_tight_coupling(self) -> None:
        """Detect tight coupling between UI and business logic."""
        for file_path, imports in self.imports_map.items():
            layer = self._get_layer(file_path)
            
            # Check if UI layer directly imports from database layer
            if layer == 'ui':
                for import_name in imports:
                    target_layer = self._get_layer_from_import(import_name)
                    
                    if target_layer == 'database':
                        finding = Finding(
                            category="Architecture",
                            description=f"Tight coupling: UI directly accessing database layer",
                            risk_level=RiskLevel.HIGH,
                            file_path=file_path,
                            recommendation="Use service layer or repository pattern to decouple UI from database",
                            details={
                                'import': import_name,
                                'violation_type': 'UI-Database coupling'
                            }
                        )
                        self.tight_coupling.append(finding)
            
            # Check for direct database calls in UI (looking for specific patterns)
            if layer == 'ui':
                try:
                    content = self.get_file_content(self.project_root / file_path)
                    
                    # Look for direct SQL or database connection patterns
                    if 'sqlite3.connect' in content or 'cursor.execute' in content:
                        finding = Finding(
                            category="Architecture",
                            description=f"Direct database access in UI layer",
                            risk_level=RiskLevel.CRITICAL,
                            file_path=file_path,
                            recommendation="Move database access to repository layer",
                            details={'violation_type': 'Direct SQL in UI'}
                        )
                        self.tight_coupling.append(finding)
                except Exception:
                    pass
