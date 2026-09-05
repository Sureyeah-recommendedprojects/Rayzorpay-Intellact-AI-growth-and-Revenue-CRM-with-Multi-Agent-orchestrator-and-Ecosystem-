"""
Smart Contract Security Auditor for PyMon
Analyzes Python smart contracts for vulnerabilities and best practices.
"""

import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


class Severity(Enum):
    """Severity levels for audit findings."""
    CRITICAL = "🔴 Critical"
    HIGH = "🟠 High"
    MEDIUM = "🟡 Medium"
    LOW = "🟢 Low"
    INFO = "🔵 Info"


class VulnerabilityType(Enum):
    """Types of vulnerabilities to check."""
    REENTRANCY = "Reentrancy Attack"
    INTEGER_OVERFLOW = "Integer Overflow/Underflow"
    ACCESS_CONTROL = "Access Control"
    UNCHECKED_CALL = "Unchecked External Call"
    TIMESTAMP_DEPENDENCE = "Timestamp Dependence"
    TX_ORIGIN = "tx.origin Usage"
    UNINITIALIZED_STORAGE = "Uninitialized Storage"
    FLOATING_PRAGMA = "Floating Pragma"
    DENIAL_OF_SERVICE = "Denial of Service"
    FRONT_RUNNING = "Front-Running"
    INSUFFICIENT_GAS = "Insufficient Gas"
    UNSAFE_RANDOM = "Unsafe Randomness"
    MISSING_EVENTS = "Missing Events"
    MISSING_VALIDATION = "Missing Input Validation"
    HARDCODED_VALUES = "Hardcoded Values"


@dataclass
class AuditFinding:
    """Represents a single audit finding."""
    vulnerability_type: VulnerabilityType
    severity: Severity
    location: str
    line_number: Optional[int]
    description: str
    recommendation: str
    code_snippet: Optional[str] = None
    gas_impact: Optional[str] = None


@dataclass
class AuditReport:
    """Complete audit report for a contract."""
    contract_name: str
    findings: List[AuditFinding] = field(default_factory=list)
    gas_optimizations: List[Dict[str, Any]] = field(default_factory=list)
    best_practices: List[Dict[str, Any]] = field(default_factory=list)
    score: int = 100  # Security score out of 100
    passed: bool = True
    summary: Dict[str, int] = field(default_factory=dict)


class ContractAuditor(ast.NodeVisitor):
    """Analyzes Python smart contracts for security vulnerabilities."""
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.findings = []
        self.current_function = None
        self.state_variables = {}
        self.functions = {}
        self.has_access_control = False
        self.has_events = False
        self.external_calls = []
        self.state_changes = []
        self.loops = []
        self.math_operations = []
        
    def audit(self) -> AuditReport:
        """Perform comprehensive security audit."""
        tree = ast.parse(self.source_code)
        contract_name = self._get_contract_name(tree)
        
        # Visit AST to collect information
        self.visit(tree)
        
        # Perform security checks
        self._check_reentrancy()
        self._check_access_control()
        self._check_integer_overflow()
        self._check_input_validation()
        self._check_gas_optimization()
        self._check_best_practices()
        self._check_dos_vulnerabilities()
        self._check_randomness()
        self._check_events()
        
        # Generate report
        report = self._generate_report(contract_name)
        
        return report
    
    def _get_contract_name(self, tree: ast.AST) -> str:
        """Extract contract name from AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                return node.name
        return "Unknown"
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        self.current_function = node.name
        
        # Check for access control decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if 'only' in decorator.id.lower() or 'require' in decorator.id.lower():
                    self.has_access_control = True
        
        # Store function info
        self.functions[node.name] = {
            'node': node,
            'has_validation': False,
            'has_events': False,
            'modifies_state': False,
            'makes_external_calls': False
        }
        
        self.generic_visit(node)
        self.current_function = None
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment to track state changes."""
        # Track state variable modifications
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == 'self':
                    self.state_changes.append({
                        'variable': target.attr,
                        'function': self.current_function,
                        'line': node.lineno
                    })
                    if self.current_function:
                        self.functions[self.current_function]['modifies_state'] = True
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit function calls to detect external calls and events."""
        # Check for external calls
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            
            # Check for event emissions
            if func_name == 'event' or func_name == 'emit':
                self.has_events = True
                if self.current_function:
                    self.functions[self.current_function]['has_events'] = True
            
            # Check for external calls (transfer, send, call, etc.)
            if func_name in ['transfer', 'send', 'call', 'delegatecall', 'staticcall']:
                self.external_calls.append({
                    'type': func_name,
                    'function': self.current_function,
                    'line': node.lineno
                })
                if self.current_function:
                    self.functions[self.current_function]['makes_external_calls'] = True
        
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For):
        """Visit for loops to check for gas issues."""
        self.loops.append({
            'function': self.current_function,
            'line': node.lineno,
            'type': 'for'
        })
        self.generic_visit(node)
    
    def visit_While(self, node: ast.While):
        """Visit while loops to check for gas issues."""
        self.loops.append({
            'function': self.current_function,
            'line': node.lineno,
            'type': 'while'
        })
        self.generic_visit(node)
    
    def visit_BinOp(self, node: ast.BinOp):
        """Visit binary operations to check for overflow."""
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            self.math_operations.append({
                'operation': type(node.op).__name__,
                'function': self.current_function,
                'line': node.lineno
            })
        self.generic_visit(node)
    
    def visit_If(self, node: ast.If):
        """Visit if statements to check for validation."""
        # Check if this is input validation
        if self._is_validation_check(node.test):
            if self.current_function:
                self.functions[self.current_function]['has_validation'] = True
        
        self.generic_visit(node)
    
    def _is_validation_check(self, node: ast.AST) -> bool:
        """Check if an expression is likely input validation."""
        if isinstance(node, ast.Compare):
            # Check for common validation patterns
            for op in node.ops:
                if isinstance(op, (ast.Eq, ast.NotEq, ast.Lt, ast.Gt, ast.LtE, ast.GtE)):
                    return True
        return False
    
    def _check_reentrancy(self):
        """Check for reentrancy vulnerabilities."""
        for call in self.external_calls:
            func_name = call['function']
            if func_name in self.functions:
                # Check if state is modified after external call
                state_changes_after = [
                    s for s in self.state_changes 
                    if s['function'] == func_name and s['line'] > call['line']
                ]
                
                if state_changes_after:
                    self.findings.append(AuditFinding(
                        vulnerability_type=VulnerabilityType.REENTRANCY,
                        severity=Severity.CRITICAL,
                        location=f"Function: {func_name}",
                        line_number=call['line'],
                        description="State is modified after an external call, making the contract vulnerable to reentrancy attacks.",
                        recommendation="Follow the Checks-Effects-Interactions pattern. Update state before making external calls.",
                        code_snippet=self._get_code_snippet(call['line'])
                    ))
    
    def _check_access_control(self):
        """Check for access control issues."""
        critical_functions = ['withdraw', 'transfer', 'mint', 'burn', 'pause', 'unpause', 
                             'set_owner', 'set_admin', 'destroy', 'selfdestruct']
        
        for func_name, func_info in self.functions.items():
            # Check if function name suggests it needs access control
            is_critical = any(critical in func_name.lower() for critical in critical_functions)
            
            if is_critical and not func_info.get('has_validation', False):
                self.findings.append(AuditFinding(
                    vulnerability_type=VulnerabilityType.ACCESS_CONTROL,
                    severity=Severity.HIGH,
                    location=f"Function: {func_name}",
                    line_number=func_info['node'].lineno,
                    description=f"Critical function '{func_name}' lacks access control.",
                    recommendation="Add access control modifiers like 'only_owner' or validate msg.sender.",
                    code_snippet=self._get_code_snippet(func_info['node'].lineno)
                ))
    
    def _check_integer_overflow(self):
        """Check for integer overflow/underflow vulnerabilities."""
        for op in self.math_operations:
            if op['operation'] in ['Add', 'Sub', 'Mult', 'Pow']:
                # Check if SafeMath or overflow checks are used
                func_name = op['function']
                if func_name and not self._has_overflow_protection(func_name):
                    self.findings.append(AuditFinding(
                        vulnerability_type=VulnerabilityType.INTEGER_OVERFLOW,
                        severity=Severity.MEDIUM,
                        location=f"Function: {func_name}",
                        line_number=op['line'],
                        description=f"Arithmetic operation without overflow protection.",
                        recommendation="Use SafeMath library or add overflow checks for arithmetic operations.",
                        code_snippet=self._get_code_snippet(op['line'])
                    ))
    
    def _check_input_validation(self):
        """Check for missing input validation."""
        for func_name, func_info in self.functions.items():
            if func_name.startswith('_'):
                continue  # Skip private functions
            
            node = func_info['node']
            has_params = len(node.args.args) > 1  # More than just 'self'
            
            if has_params and not func_info.get('has_validation', False):
                self.findings.append(AuditFinding(
                    vulnerability_type=VulnerabilityType.MISSING_VALIDATION,
                    severity=Severity.LOW,
                    location=f"Function: {func_name}",
                    line_number=node.lineno,
                    description="Function accepts parameters but lacks input validation.",
                    recommendation="Validate all input parameters at the beginning of the function.",
                    code_snippet=self._get_code_snippet(node.lineno)
                ))
    
    def _check_gas_optimization(self):
        """Check for gas optimization opportunities."""
        # Check for loops that could cause gas issues
        for loop in self.loops:
            if loop['type'] == 'while':
                self.findings.append(AuditFinding(
                    vulnerability_type=VulnerabilityType.INSUFFICIENT_GAS,
                    severity=Severity.MEDIUM,
                    location=f"Function: {loop['function']}",
                    line_number=loop['line'],
                    description="Unbounded loop could cause out-of-gas errors.",
                    recommendation="Consider using a for loop with a fixed upper bound or implement pagination.",
                    code_snippet=self._get_code_snippet(loop['line']),
                    gas_impact="High - unbounded loops can consume all gas"
                ))
        
        # Check for multiple storage reads/writes
        for func_name, func_info in self.functions.items():
            state_mods = [s for s in self.state_changes if s['function'] == func_name]
            if len(state_mods) > 3:
                self.findings.append(AuditFinding(
                    vulnerability_type=VulnerabilityType.INSUFFICIENT_GAS,
                    severity=Severity.LOW,
                    location=f"Function: {func_name}",
                    line_number=func_info['node'].lineno,
                    description=f"Function makes {len(state_mods)} state modifications.",
                    recommendation="Consider batching storage operations or using memory variables.",
                    gas_impact=f"Each SSTORE costs ~20,000 gas"
                ))
    
    def _check_best_practices(self):
        """Check for best practices."""
        # Check for events
        if not self.has_events:
            self.findings.append(AuditFinding(
                vulnerability_type=VulnerabilityType.MISSING_EVENTS,
                severity=Severity.INFO,
                location="Contract",
                line_number=None,
                description="Contract doesn't emit events for state changes.",
                recommendation="Emit events for all significant state changes to enable off-chain monitoring."
            ))
        
        # Check for hardcoded values
        self._check_hardcoded_values()
    
    def _check_dos_vulnerabilities(self):
        """Check for Denial of Service vulnerabilities."""
        # Check for external calls in loops
        for call in self.external_calls:
            for loop in self.loops:
                if call['function'] == loop['function'] and call['line'] > loop['line']:
                    self.findings.append(AuditFinding(
                        vulnerability_type=VulnerabilityType.DENIAL_OF_SERVICE,
                        severity=Severity.HIGH,
                        location=f"Function: {call['function']}",
                        line_number=call['line'],
                        description="External call inside a loop can lead to DoS attacks.",
                        recommendation="Avoid external calls in loops. Use pull payment pattern instead.",
                        code_snippet=self._get_code_snippet(call['line'])
                    ))
    
    def _check_randomness(self):
        """Check for unsafe randomness generation."""
        unsafe_random_patterns = ['timestamp', 'block.timestamp', 'now', 'blockhash']
        
        for line_no, line in enumerate(self.source_lines, 1):
            for pattern in unsafe_random_patterns:
                if pattern in line.lower() and 'random' in line.lower():
                    self.findings.append(AuditFinding(
                        vulnerability_type=VulnerabilityType.UNSAFE_RANDOM,
                        severity=Severity.MEDIUM,
                        location=f"Line {line_no}",
                        line_number=line_no,
                        description="Using block properties for randomness is predictable.",
                        recommendation="Use Chainlink VRF or commit-reveal scheme for secure randomness.",
                        code_snippet=line.strip()
                    ))
    
    def _check_events(self):
        """Check if important functions emit events."""
        for func_name, func_info in self.functions.items():
            if func_info['modifies_state'] and not func_info['has_events']:
                if not func_name.startswith('_'):  # Public functions only
                    self.findings.append(AuditFinding(
                        vulnerability_type=VulnerabilityType.MISSING_EVENTS,
                        severity=Severity.INFO,
                        location=f"Function: {func_name}",
                        line_number=func_info['node'].lineno,
                        description="State-changing function doesn't emit events.",
                        recommendation="Emit events for state changes to enable monitoring and indexing."
                    ))
    
    def _check_hardcoded_values(self):
        """Check for hardcoded addresses and values."""
        address_pattern = re.compile(r'0x[a-fA-F0-9]{40}')
        
        for line_no, line in enumerate(self.source_lines, 1):
            if address_pattern.search(line):
                self.findings.append(AuditFinding(
                    vulnerability_type=VulnerabilityType.HARDCODED_VALUES,
                    severity=Severity.LOW,
                    location=f"Line {line_no}",
                    line_number=line_no,
                    description="Hardcoded address found.",
                    recommendation="Use constructor parameters or configuration contracts for addresses.",
                    code_snippet=line.strip()
                ))
    
    def _has_overflow_protection(self, func_name: str) -> bool:
        """Check if function has overflow protection."""
        # Simple heuristic - check if SafeMath or require statements are used
        if func_name in self.functions:
            return self.functions[func_name].get('has_validation', False)
        return False
    
    def _get_code_snippet(self, line_number: int) -> str:
        """Get code snippet around a line number."""
        if line_number and 0 < line_number <= len(self.source_lines):
            start = max(0, line_number - 2)
            end = min(len(self.source_lines), line_number + 2)
            return '\n'.join(self.source_lines[start:end])
        return ""
    
    def _generate_report(self, contract_name: str) -> AuditReport:
        """Generate the final audit report."""
        report = AuditReport(contract_name=contract_name)
        report.findings = self.findings
        
        # Calculate summary
        summary = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for finding in self.findings:
            if finding.severity == Severity.CRITICAL:
                summary['critical'] += 1
                report.score -= 25
            elif finding.severity == Severity.HIGH:
                summary['high'] += 1
                report.score -= 15
            elif finding.severity == Severity.MEDIUM:
                summary['medium'] += 1
                report.score -= 10
            elif finding.severity == Severity.LOW:
                summary['low'] += 1
                report.score -= 5
            else:
                summary['info'] += 1
                report.score -= 2
        
        report.summary = summary
        report.score = max(0, report.score)
        report.passed = summary['critical'] == 0 and summary['high'] <= 1
        
        return report


def audit_contract(source_code: str) -> AuditReport:
    """Main function to audit a smart contract."""
    auditor = ContractAuditor(source_code)
    return auditor.audit()


def display_audit_report(report: AuditReport):
    """Display audit report in a formatted way."""
    # Header
    console.print(Panel.fit(
        f"[bold cyan]Security Audit Report[/bold cyan]\n"
        f"Contract: {report.contract_name}\n"
        f"Score: {report.score}/100 {'✅' if report.passed else '❌'}",
        title="🔍 Audit Results"
    ))
    
    # Summary table
    summary_table = Table(title="Findings Summary")
    summary_table.add_column("Severity", style="cyan")
    summary_table.add_column("Count", style="yellow")
    
    summary_table.add_row("🔴 Critical", str(report.summary.get('critical', 0)))
    summary_table.add_row("🟠 High", str(report.summary.get('high', 0)))
    summary_table.add_row("🟡 Medium", str(report.summary.get('medium', 0)))
    summary_table.add_row("🟢 Low", str(report.summary.get('low', 0)))
    summary_table.add_row("🔵 Info", str(report.summary.get('info', 0)))
    
    console.print(summary_table)
    
    # Detailed findings
    if report.findings:
        console.print("\n[bold]Detailed Findings:[/bold]\n")
        
        for i, finding in enumerate(report.findings, 1):
            console.print(f"[bold]{i}. {finding.vulnerability_type.value}[/bold]")
            console.print(f"   {finding.severity.value} | {finding.location}")
            console.print(f"   [yellow]Issue:[/yellow] {finding.description}")
            console.print(f"   [green]Fix:[/green] {finding.recommendation}")
            
            if finding.code_snippet:
                console.print(f"   [dim]Code:[/dim]")
                syntax = Syntax(finding.code_snippet, "python", theme="monokai", line_numbers=True)
                console.print(syntax)
            
            if finding.gas_impact:
                console.print(f"   [blue]Gas Impact:[/blue] {finding.gas_impact}")
            
            console.print()
    
    # Recommendations
    if not report.passed:
        console.print(Panel(
            "[red]⚠️ Contract failed security audit![/red]\n"
            "Please fix critical and high severity issues before deployment.",
            title="Action Required",
            style="red"
        ))
    else:
        console.print(Panel(
            "[green]✅ Contract passed basic security checks![/green]\n"
            "Consider fixing medium and low severity issues for better security.",
            title="Audit Passed",
            style="green"
        ))


# Integration with PyMon CLI
def audit_contract_file(file_path: str) -> AuditReport:
    """Audit a contract from file."""
    with open(file_path, 'r') as f:
        source_code = f.read()
    
    return audit_contract(source_code)


if __name__ == "__main__":
    # Example usage
    example_contract = '''
class VulnerableContract(PySmartContract):
    def __init__(self):
        self.owner = msg.sender
        self.balance = 0
    
    def withdraw(self, amount):
        # Vulnerable to reentrancy
        if self.balance >= amount:
            msg.sender.transfer(amount)
            self.balance -= amount
    
    def deposit(self):
        self.balance += msg.value
    '''
    
    report = audit_contract(example_contract)
    display_audit_report(report)
