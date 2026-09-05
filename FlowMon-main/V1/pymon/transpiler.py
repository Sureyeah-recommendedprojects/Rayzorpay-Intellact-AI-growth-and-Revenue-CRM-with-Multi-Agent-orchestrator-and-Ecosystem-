"""Python to EVM bytecode transpiler for smart contracts."""

import ast
import json
import hashlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from Crypto.Hash import keccak
from rich.console import Console

console = Console()


def keccak256(data: bytes) -> bytes:
    """Calculate keccak256 hash."""
    k = keccak.new(digest_bits=256)
    k.update(data)
    return k.digest()


def function_selector(signature: str) -> bytes:
    """Generate 4-byte function selector from signature."""
    return keccak256(signature.encode('utf-8'))[:4]


class EVMOpcode(Enum):
    """EVM opcodes for bytecode generation."""
    # Stack operations
    PUSH1 = 0x60
    PUSH2 = 0x61
    PUSH4 = 0x63
    PUSH32 = 0x7f
    POP = 0x50
    DUP1 = 0x80
    DUP2 = 0x81
    SWAP1 = 0x90
    
    # Arithmetic and Logic
    ADD = 0x01
    SUB = 0x03
    MUL = 0x02
    DIV = 0x04
    MOD = 0x06
    EQ = 0x14
    LT = 0x10
    GT = 0x11
    AND = 0x16
    SHR = 0x1c
    ISZERO = 0x15
    
    # Storage
    SLOAD = 0x54
    SSTORE = 0x55
    
    # Memory
    MSTORE = 0x52
    MLOAD = 0x51
    
    # Code operations
    CODECOPY = 0x39
    CODESIZE = 0x38
    
    # Calldata operations
    CALLDATASIZE = 0x36
    CALLDATALOAD = 0x35
    CALLDATACOPY = 0x37
    
    # Control flow
    JUMP = 0x56
    JUMPI = 0x57
    JUMPDEST = 0x5b
    STOP = 0x00
    RETURN = 0xf3
    REVERT = 0xfd
    
    # Call operations
    CALL = 0xf1
    CALLVALUE = 0x34
    CALLER = 0x33
    
    # Gas
    GAS = 0x5a


@dataclass
class ContractState:
    """Represents smart contract state variables."""
    variables: Dict[str, int]  # Variable name -> storage slot
    functions: Dict[str, int]  # Function name -> bytecode offset
    events: Dict[str, List[str]]  # Event name -> parameter types
    initial_values: Dict[str, Any]  # Variable initial values
    variable_types: Dict[str, str]  # Variable name -> type (uint256, bytes32)
    next_slot: int = 0


@dataclass
class GasCost:
    """Gas costs for different operations."""
    SLOAD = 200
    SSTORE_SET = 20000
    SSTORE_RESET = 5000
    ARITHMETIC = 3
    MEMORY = 3
    CALL = 700


class PySmartContract:
    """Base class for Python smart contracts."""
    
    def __init__(self):
        self._state = {}
        self._storage_slots = {}
        self._slot_counter = 0
    
    def state_var(self, name: str, initial_value: Any = 0):
        """Decorator for state variables."""
        slot = self._slot_counter
        self._storage_slots[name] = slot
        self._state[name] = initial_value
        self._slot_counter += 1
        return initial_value
    
    def public_function(self, func):
        """Decorator for public functions."""
        func._is_public = True
        return func
    
    def view_function(self, func):
        """Decorator for view functions."""
        func._is_view = True
        return func


class PythonASTAnalyzer(ast.NodeVisitor):
    """Analyzes Python AST to extract smart contract components."""
    
    def __init__(self):
        self.state_vars = {}
        self.initial_values = {}  # Track initial values from __init__
        self.variable_types = {}  # Track variable types (uint256, bytes32, address, mapping)
        self.functions = {}
        self.events = {}
        self.mappings = {}  # Track mapping variables: name -> {key_type, value_type}
        self.current_function = None
        self.next_slot = 0  # For unique slot allocation
        self.bytecode_chunks = []
    
    def analyze_contract(self, source_code: str) -> ContractState:
        """Analyze Python smart contract source code."""
        tree = ast.parse(source_code)
        self.visit(tree)
        
        return ContractState(
            variables=self.state_vars,
            functions=self.functions,
            events=self.events,
            initial_values=self.initial_values,
            variable_types=self.variable_types
        )
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition (smart contract)."""
        console.print(f"[blue]Analyzing contract class: {node.name}[/blue]")
        
        # Check if inherits from PySmartContract
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "PySmartContract":
                self.generic_visit(node)
                break
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        # Special handling for __init__ to capture state variable initialization
        if node.name == '__init__':
            self.current_function = node.name
            console.print(f"[green]Found constructor: {node.name}[/green]")
            # Visit __init__ body to collect state variable assignments
            self.generic_visit(node)
            self.current_function = None
            return
        
        if node.name.startswith('_'):
            return  # Skip other private functions
            
        self.current_function = node.name
        console.print(f"[green]Found function: {node.name}[/green]")
        
        # Analyze function decorators
        is_public = any(
            isinstance(d, ast.Name) and d.id == 'public_function' 
            for d in node.decorator_list
        )
        
        is_view = any(
            isinstance(d, ast.Name) and d.id == 'view_function'
            for d in node.decorator_list
        )
        
        # Enhanced parameter type analysis
        param_types = []
        for arg in node.args.args:
            if arg.arg == 'self':
                continue
            
            # Check for type annotations
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    if arg.annotation.id == 'str':
                        param_types.append('address')  # Treat str as address in DeFi context
                    elif arg.annotation.id == 'int':
                        param_types.append('uint256')
                    else:
                        param_types.append('uint256')  # Default
                else:
                    param_types.append('uint256')  # Default
            else:
                param_types.append('uint256')  # Default when no annotation
        
        # Check if function returns a value and analyze return type
        has_return = any(isinstance(stmt, ast.Return) and stmt.value is not None for stmt in node.body)
        return_type = 'uint256'  # Default return type
        
        # Enhanced return type analysis
        for stmt in node.body:
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                if isinstance(stmt.value, ast.Attribute):
                    # Returning self.variable - check variable type
                    if (isinstance(stmt.value.value, ast.Name) and 
                        stmt.value.value.id == 'self'):
                        var_name = stmt.value.attr
                        if var_name in self.variable_types:
                            return_type = self.variable_types[var_name]
                elif isinstance(stmt.value, ast.Subscript):
                    # Returning mapping value like self.balances[user]
                    if (isinstance(stmt.value.value, ast.Attribute) and
                        isinstance(stmt.value.value.value, ast.Name) and
                        stmt.value.value.value.id == 'self'):
                        mapping_name = stmt.value.value.attr
                        if mapping_name in self.mappings:
                            return_type = self.mappings[mapping_name]['value_type']
        
        self.functions[node.name] = {
            'is_public': is_public,
            'is_view': is_view,
            'args': [arg.arg for arg in node.args.args if arg.arg != 'self'],
            'param_types': param_types,
            'body': node.body,
            'has_return': has_return,
            'return_type': return_type
        }
        
        self.generic_visit(node)
        self.current_function = None
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment operations."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Attribute):
            attr = node.targets[0]
            if isinstance(attr.value, ast.Name) and attr.value.id == 'self':
                # State variable assignment
                var_name = attr.attr
                
                # Always assign slot, even if variable already exists (for proper initialization)
                if var_name not in self.state_vars:
                    self.state_vars[var_name] = self.next_slot
                    self.next_slot += 1
                    console.print(f"[yellow]State variable: {var_name}[/yellow]")
                
                # Enhanced type detection and mapping support
                if isinstance(node.value, ast.Dict):
                    # Dictionary assignment - treat as mapping
                    self.initial_values[var_name] = {}
                    self.variable_types[var_name] = 'mapping'
                    self.mappings[var_name] = {
                        'key_type': 'address',  # Default for DeFi (user addresses)
                        'value_type': 'uint256',  # Default for balances/amounts
                        'base_slot': self.state_vars[var_name]
                    }
                elif isinstance(node.value, ast.Call):
                    # Function call assignment like self.msg_sender()
                    if (isinstance(node.value.func, ast.Attribute) and
                        isinstance(node.value.func.value, ast.Name) and
                        node.value.func.value.id == 'self' and
                        node.value.func.attr == 'msg_sender'):
                        self.initial_values[var_name] = 0  # Placeholder for msg.sender
                        self.variable_types[var_name] = 'address'
                    else:
                        self.initial_values[var_name] = 0
                        self.variable_types[var_name] = 'uint256'
                elif isinstance(node.value, ast.Constant):
                    # Handle different types of constants (including strings)
                    if isinstance(node.value.value, str):
                        # Check if it looks like an address or should be treated as bytes32
                        if len(node.value.value) == 42 and node.value.value.startswith('0x'):
                            # Ethereum address format
                            self.initial_values[var_name] = int(node.value.value, 16)
                            self.variable_types[var_name] = 'address'
                        else:
                            # Convert string to bytes32 for EVM storage
                            str_bytes = node.value.value.encode('utf-8')[:32]
                            self.initial_values[var_name] = int.from_bytes(str_bytes.ljust(32, b'\x00'), 'big')
                            self.variable_types[var_name] = 'bytes32'
                    else:
                        # Handle numeric and other constant types
                        self.initial_values[var_name] = node.value.value
                        self.variable_types[var_name] = 'uint256'
                elif isinstance(node.value, ast.Num):  # Python < 3.8 compatibility
                    self.initial_values[var_name] = node.value.n
                    self.variable_types[var_name] = 'uint256'
                elif isinstance(node.value, ast.Str):  # String literals (Python < 3.8 compatibility)
                    # Check if it looks like an address
                    if len(node.value.s) == 42 and node.value.s.startswith('0x'):
                        self.initial_values[var_name] = int(node.value.s, 16)
                        self.variable_types[var_name] = 'address'
                    else:
                        # Convert string to bytes32 for EVM storage
                        str_bytes = node.value.s.encode('utf-8')[:32]
                        self.initial_values[var_name] = int.from_bytes(str_bytes.ljust(32, b'\x00'), 'big')
                        self.variable_types[var_name] = 'bytes32'
                else:
                    # Default fallback
                    self.initial_values[var_name] = 0
                    self.variable_types[var_name] = 'uint256'
                
                if self.current_function == '__init__':
                    console.print(f"[cyan]Constructor initializes {var_name} = {self.initial_values.get(var_name, 0)}[/cyan]")
        
        self.generic_visit(node)


class EVMBytecodeGenerator:
    """Generates EVM bytecode from analyzed contract."""
    
    def __init__(self):
        self.init_code = bytearray()
        self.runtime_code = bytearray()
        self.gas_used = 0
        self.jump_table = {}
        self.function_offsets = {}
        self.current_mode = 'init'  # 'init' or 'runtime'
        self.current_state = None  # Current ContractState for compilation
        self.current_function_args = []  # Current function arguments
    
    def emit_opcode(self, opcode: EVMOpcode, gas_cost: int = 0):
        """Emit an EVM opcode to current bytecode."""
        if self.current_mode == 'init':
            self.init_code.append(opcode.value)
        else:
            self.runtime_code.append(opcode.value)
        self.gas_used += gas_cost
    
    def emit_push(self, value: Union[int, bytes, str], size: int = None):
        """Emit PUSH operation with value."""
        if isinstance(value, int):
            if size is None:
                # Determine minimum size needed
                if value == 0:
                    size = 1
                else:
                    size = (value.bit_length() + 7) // 8
            
            value_bytes = value.to_bytes(size, 'big')
        elif isinstance(value, str):
            # Handle string values by converting to bytes32 for EVM storage
            str_bytes = value.encode('utf-8')[:32]  # Truncate to 32 bytes if needed
            value_bytes = str_bytes.ljust(32, b'\x00')  # Pad to 32 bytes
            size = 32
        else:
            value_bytes = value
            size = len(value_bytes)
        
        # Emit PUSH opcode (PUSH1 to PUSH32)
        push_opcode = EVMOpcode.PUSH1.value + size - 1
        if self.current_mode == 'init':
            self.init_code.append(push_opcode)
            self.init_code.extend(value_bytes)
        else:
            self.runtime_code.append(push_opcode)
            self.runtime_code.extend(value_bytes)
        self.gas_used += GasCost.ARITHMETIC
    
    def emit_bytes(self, data: bytes):
        """Emit raw bytes to current bytecode."""
        if self.current_mode == 'init':
            self.init_code.extend(data)
        else:
            self.runtime_code.extend(data)
    
    def get_current_offset(self) -> int:
        """Get current offset in active bytecode."""
        if self.current_mode == 'init':
            return len(self.init_code)
        else:
            return len(self.runtime_code)
    
    def set_mode(self, mode: str):
        """Set bytecode generation mode."""
        self.current_mode = mode
    
    def compile_expr(self, node: ast.AST, arg_map: Dict[str, int] = None) -> None:
        """Compile Python expression to EVM bytecode."""
        if arg_map is None:
            arg_map = {}
            
        if isinstance(node, ast.Constant):
            # Literal value
            self.emit_push(node.value)
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            self.emit_push(node.n)
        elif isinstance(node, ast.Name):
            # Variable or argument reference
            if node.id in arg_map:
                # Function argument - load from calldata
                arg_index = arg_map[node.id]
                offset = 4 + arg_index * 32  # Skip selector + arg_index * 32
                self.emit_push(offset)
                self.emit_opcode(EVMOpcode.CALLDATALOAD)
            else:
                # Unknown variable - treat as 0 for now
                self.emit_push(0)
        elif isinstance(node, ast.Attribute):
            # State variable access (self.var_name)
            if (isinstance(node.value, ast.Name) and node.value.id == 'self' and 
                self.current_state and node.attr in self.current_state.variables):
                slot = self.current_state.variables[node.attr]
                self.emit_push(slot)
                self.emit_opcode(EVMOpcode.SLOAD)
            else:
                # Unknown attribute - treat as 0
                self.emit_push(0)
        elif isinstance(node, ast.Subscript):
            # Mapping access like self.balances[user]
            if (isinstance(node.value, ast.Attribute) and
                isinstance(node.value.value, ast.Name) and
                node.value.value.id == 'self' and
                self.current_state):
                mapping_name = node.value.attr
                if mapping_name in self.current_state.variables:
                    # Generate mapping storage slot: keccak256(key . base_slot)
                    base_slot = self.current_state.variables[mapping_name]
                    
                    # Compile the key (index)
                    self.compile_expr(node.slice, arg_map)
                    
                    # Push base slot
                    self.emit_push(base_slot)
                    
                    # Calculate keccak256(key . base_slot) for mapping storage
                    # For now, use simplified mapping: base_slot + key
                    self.emit_opcode(EVMOpcode.ADD)
                    self.emit_opcode(EVMOpcode.SLOAD)
                else:
                    self.emit_push(0)
            else:
                self.emit_push(0)
        elif isinstance(node, ast.BinOp):
            # Binary operation
            self.compile_expr(node.left, arg_map)
            self.compile_expr(node.right, arg_map)
            
            if isinstance(node.op, ast.Add):
                self.emit_opcode(EVMOpcode.ADD)
            elif isinstance(node.op, ast.Sub):
                self.emit_opcode(EVMOpcode.SUB)
            elif isinstance(node.op, ast.Mult):
                self.emit_opcode(EVMOpcode.MUL)
            elif isinstance(node.op, ast.Div):
                self.emit_opcode(EVMOpcode.DIV)
            elif isinstance(node.op, ast.Mod):
                self.emit_opcode(EVMOpcode.MOD)
        elif isinstance(node, ast.Compare):
            # Comparison operation
            self.compile_expr(node.left, arg_map)
            
            if len(node.ops) == 1 and len(node.comparators) == 1:
                self.compile_expr(node.comparators[0], arg_map)
                
                if isinstance(node.ops[0], ast.Eq):
                    self.emit_opcode(EVMOpcode.EQ)
                elif isinstance(node.ops[0], ast.Lt):
                    # Fixed: Stack is [left, right], we want left < right
                    # EVM LT computes second_to_top < top, so we need SWAP1
                    self.emit_opcode(EVMOpcode.SWAP1)
                    self.emit_opcode(EVMOpcode.LT)
                elif isinstance(node.ops[0], ast.Gt):
                    # Fixed: Stack is [left, right], we want left > right  
                    # EVM GT computes second_to_top > top, so we need SWAP1
                    self.emit_opcode(EVMOpcode.SWAP1)
                    self.emit_opcode(EVMOpcode.GT)
                elif isinstance(node.ops[0], ast.LtE):
                    # a <= b: Stack after compiling: [a, b] (b on top)
                    # We want: a <= b which is equivalent to NOT(a > b)
                    # Fixed: Add SWAP1 for correct operand order
                    self.emit_opcode(EVMOpcode.SWAP1)
                    self.emit_opcode(EVMOpcode.GT)  # a > b
                    self.emit_opcode(EVMOpcode.ISZERO)  # NOT(a > b) = a <= b
                elif isinstance(node.ops[0], ast.GtE):
                    # a >= b: Stack after compiling: [a, b] (b on top)
                    # We want: a >= b which is equivalent to NOT(a < b)
                    # Fixed: Add SWAP1 for correct operand order
                    self.emit_opcode(EVMOpcode.SWAP1)
                    self.emit_opcode(EVMOpcode.LT)  # a < b
                    self.emit_opcode(EVMOpcode.ISZERO)  # NOT(a < b) = a >= b
        else:
            # Unknown expression - emit 0
            self.emit_push(0)
    
    def compile_stmt(self, node: ast.AST, arg_map: Dict[str, int] = None) -> None:
        """Compile Python statement to EVM bytecode."""
        if arg_map is None:
            arg_map = {}
            
        if isinstance(node, ast.Assign):
            # Assignment statement
            if len(node.targets) == 1:
                target = node.targets[0]
                
                if (isinstance(target, ast.Attribute) and
                    isinstance(target.value, ast.Name) and target.value.id == 'self'):
                    # State variable assignment: self.var = expr
                    var_name = target.attr
                    if self.current_state and var_name in self.current_state.variables:
                        slot = self.current_state.variables[var_name]
                        # Compile expression and store result
                        self.compile_expr(node.value, arg_map)
                        self.emit_push(slot)
                        self.emit_opcode(EVMOpcode.SSTORE)
                        
                elif isinstance(target, ast.Subscript):
                    # Mapping assignment: self.balances[user] = value
                    if (isinstance(target.value, ast.Attribute) and
                        isinstance(target.value.value, ast.Name) and
                        target.value.value.id == 'self' and
                        self.current_state):
                        mapping_name = target.value.attr
                        if mapping_name in self.current_state.variables:
                            base_slot = self.current_state.variables[mapping_name]
                            
                            # Compile the value to store
                            self.compile_expr(node.value, arg_map)
                            
                            # Calculate storage slot: base_slot + key (simplified)
                            self.compile_expr(target.slice, arg_map)  # Key
                            self.emit_push(base_slot)  # Base slot
                            self.emit_opcode(EVMOpcode.ADD)  # Slot = base + key
                            
                            # Store value at calculated slot
                            self.emit_opcode(EVMOpcode.SSTORE)
        elif isinstance(node, ast.Return):
            # Return statement
            if node.value is not None:
                # Return a value
                self.compile_expr(node.value, arg_map)
                self.emit_push(0)  # Memory offset
                self.emit_opcode(EVMOpcode.MSTORE)
                self.emit_push(32)  # Return 32 bytes
                self.emit_push(0)   # Memory offset
                self.emit_opcode(EVMOpcode.RETURN)
            else:
                # Return empty
                self.emit_push(0)
                self.emit_push(0)
                self.emit_opcode(EVMOpcode.RETURN)
        elif isinstance(node, ast.If):
            # If statement with JUMPI
            # Compile condition
            self.compile_expr(node.test, arg_map)
            
            # Invert condition with ISZERO so JUMPI goes to else when original condition is FALSE
            self.emit_opcode(EVMOpcode.ISZERO)
            
            # JUMPI to else block when condition is FALSE (after ISZERO inversion)
            else_placeholder = self.get_current_offset()
            self.emit_push(0xFFFE, 2)  # Placeholder for else jump
            self.emit_opcode(EVMOpcode.JUMPI)
            
            # Compile if body
            for stmt in node.body:
                self.compile_stmt(stmt, arg_map)
            
            # Jump to end
            end_placeholder = self.get_current_offset()
            self.emit_push(0xFFFD, 2)  # Placeholder for end jump
            self.emit_opcode(EVMOpcode.JUMP)
            
            # Else block starts here
            else_target = self.get_current_offset()
            self.emit_opcode(EVMOpcode.JUMPDEST)
            
            # Compile else body
            for stmt in node.orelse:
                self.compile_stmt(stmt, arg_map)
            
            # End of if-else
            end_target = self.get_current_offset()
            self.emit_opcode(EVMOpcode.JUMPDEST)
            
            # Backpatch jump targets
            self._backpatch_jump_target(else_placeholder + 1, else_target, 2)
            self._backpatch_jump_target(end_placeholder + 1, end_target, 2)
        # Add more statement types as needed
    
    def _backpatch_jump_target(self, offset: int, target: int, size: int):
        """Backpatch a jump target in the bytecode."""
        target_bytes = target.to_bytes(size, 'big')
        if self.current_mode == 'init':
            self.init_code[offset:offset+size] = target_bytes
        else:
            self.runtime_code[offset:offset+size] = target_bytes
    
    def generate_complete_bytecode(self, state: ContractState) -> bytes:
        """Generate complete contract bytecode (init + runtime)."""
        console.print("[blue]Generating complete contract bytecode...[/blue]")
        
        # First generate runtime code
        self.set_mode('runtime')
        runtime_bytecode = self.generate_runtime_bytecode(state)
        
        # Then generate init code
        self.set_mode('init')
        self.generate_init_code(state, len(runtime_bytecode))
        
        # Combine init + runtime
        return bytes(self.init_code + self.runtime_code)
    
    def generate_init_code(self, state: ContractState, runtime_size: int):
        """Generate initialization bytecode."""
        console.print("[blue]Generating initialization code...[/blue]")
        
        # Initialize state variables with their initial values
        for var_name, slot in state.variables.items():
            initial_value = state.initial_values.get(var_name, 0)
            self.emit_push(initial_value)  # Initial value
            self.emit_push(slot)  # Storage slot
            self.emit_opcode(EVMOpcode.SSTORE, GasCost.SSTORE_SET)
        
        # Calculate exact runtime offset after all init code
        # This will be backpatched
        init_placeholder_start = len(self.init_code)
        
        # Placeholder for CODECOPY - will be backpatched
        self.emit_push(runtime_size)     # Size of runtime code
        self.emit_push(0xDEAD, 2)       # Placeholder for runtime offset
        self.emit_push(0)               # Memory destination
        self.emit_opcode(EVMOpcode.CODECOPY)
        
        self.emit_push(runtime_size)     # Size to return
        self.emit_push(0)               # Memory offset
        self.emit_opcode(EVMOpcode.RETURN)
        
        # Calculate actual runtime offset and backpatch
        actual_runtime_offset = len(self.init_code)
        
        # Find and replace the placeholder 0xDEAD
        for i in range(init_placeholder_start, len(self.init_code) - 1):
            if (self.init_code[i] == EVMOpcode.PUSH2.value and
                self.init_code[i+1] == 0xDE and self.init_code[i+2] == 0xAD):
                self.init_code[i+1:i+3] = actual_runtime_offset.to_bytes(2, 'big')
                break
    
    def generate_runtime_bytecode(self, state: ContractState) -> bytes:
        """Generate runtime bytecode with function dispatcher."""
        console.print("[blue]Generating runtime bytecode with function dispatcher...[/blue]")
        self.current_state = state  # Store for expression compilation
        
        # Runtime entry point
        # Check if we have calldata (function call)
        # Fixed: Corrected operand order for CALLDATASIZE < 4 check
        self.emit_push(4)
        self.emit_opcode(EVMOpcode.CALLDATASIZE)
        self.emit_opcode(EVMOpcode.LT)
        
        # If calldata < 4 bytes, use placeholder and backpatch later
        revert_placeholder_offset = self.get_current_offset() + 1
        self.emit_push(0xDEAF, 2)  # Placeholder for revert jump
        self.emit_opcode(EVMOpcode.JUMPI)
        
        # Load function selector (first 4 bytes of calldata)
        self.emit_push(0)
        self.emit_opcode(EVMOpcode.CALLDATALOAD)
        self.emit_push(224)  # 256 - 32 = 224 (shift right to get first 4 bytes)
        self.emit_opcode(EVMOpcode.SHR)
        
        # Generate function dispatcher with proper backpatching
        function_jump_table = {}
        placeholder_offsets = {}  # Track each function's placeholder position
        
        for func_name, func_info in state.functions.items():
            if func_info.get('is_public', False) or func_info.get('is_view', False):
                # Use enhanced parameter types from analysis
                param_types = func_info.get('param_types', [])
                if not param_types:
                    # Fallback to uint256 for all parameters
                    param_types = ['uint256'] * len(func_info.get('args', []))
                
                func_signature = f"{func_name}({','.join(param_types)})"
                selector = function_selector(func_signature)
                selector_int = int.from_bytes(selector, 'big')
                
                console.print(f"[yellow]Function {func_name}: {func_signature} -> 0x{selector.hex()}[/yellow]")
                
                # DUP1 (duplicate selector on stack)
                self.emit_opcode(EVMOpcode.DUP1)
                # PUSH4 selector
                self.emit_push(selector_int, 4)
                # EQ
                self.emit_opcode(EVMOpcode.EQ)
                
                # Store placeholder offset for this specific function
                placeholder_offsets[func_name] = self.get_current_offset() + 1
                
                # PUSH2 jump_target (unique placeholder for this function)
                self.emit_push(0xF000 + len(placeholder_offsets), 2)  # Unique placeholder
                # JUMPI
                self.emit_opcode(EVMOpcode.JUMPI)
        
        # If no function matches, revert
        revert_target = self.get_current_offset()
        self.emit_opcode(EVMOpcode.JUMPDEST)  # Revert target
        self.emit_push(0)
        self.emit_push(0)
        self.emit_opcode(EVMOpcode.REVERT)
        
        # Backpatch the initial revert jump
        self._backpatch_jump_target(revert_placeholder_offset, revert_target, 2)
        
        # Generate function implementations using actual Python logic
        for func_name, func_info in state.functions.items():
            if func_info.get('is_public', False) or func_info.get('is_view', False):
                function_jump_table[func_name] = self.get_current_offset()
                self.emit_opcode(EVMOpcode.JUMPDEST)
                
                # Create argument mapping for calldata loading
                args = func_info.get('args', [])
                arg_map = {arg: i for i, arg in enumerate(args)}
                
                # Compile actual Python function body
                function_body = func_info.get('body', [])
                
                # Check if function has explicit return, if not add default
                has_explicit_return = any(isinstance(stmt, ast.Return) for stmt in function_body)
                
                for stmt in function_body:
                    self.compile_stmt(stmt, arg_map)
                
                # If no explicit return and not a view function, add default empty return
                if not has_explicit_return:
                    if func_info.get('is_view', False):
                        # View function should return 0 if no explicit return
                        self.emit_push(0)
                        self.emit_push(0)
                        self.emit_opcode(EVMOpcode.MSTORE)
                        self.emit_push(32)
                        self.emit_push(0)
                        self.emit_opcode(EVMOpcode.RETURN)
                    else:
                        # Non-view function returns empty
                        self.emit_push(0)
                        self.emit_push(0)
                        self.emit_opcode(EVMOpcode.RETURN)
        
        # Backpatch all function jump targets
        for func_name, target_offset in function_jump_table.items():
            if func_name in placeholder_offsets:
                placeholder_offset = placeholder_offsets[func_name]
                self._backpatch_jump_target(placeholder_offset, target_offset, 2)
        
        return bytes(self.runtime_code)
    


class PythonContractTranspiler:
    """Main transpiler class that coordinates the compilation process."""
    
    def __init__(self):
        self.analyzer = PythonASTAnalyzer()
        self.generator = EVMBytecodeGenerator()
    
    def transpile(self, source_code: str) -> Dict[str, Any]:
        """
        Transpile Python smart contract to EVM bytecode.
        
        Args:
            source_code: Python smart contract source code
            
        Returns:
            Dictionary containing bytecode, ABI, and metadata
        """
        console.print("[bold blue]Starting Python to EVM transpilation...[/bold blue]")
        
        try:
            # Step 1: Analyze Python AST
            console.print("[yellow]Step 1: Analyzing Python AST...[/yellow]")
            contract_state = self.analyzer.analyze_contract(source_code)
            
            # Step 2: Generate EVM bytecode
            console.print("[yellow]Step 2: Generating EVM bytecode...[/yellow]")
            
            # Generate complete bytecode (init + runtime)
            full_bytecode = self.generator.generate_complete_bytecode(contract_state)
            
            # Step 3: Generate ABI
            console.print("[yellow]Step 3: Generating ABI...[/yellow]")
            abi = self._generate_abi(contract_state)
            
            # Step 4: Calculate gas estimate
            gas_estimate = self.generator.gas_used
            
            result = {
                "bytecode": "0x" + full_bytecode.hex(),
                "abi": abi,
                "metadata": {
                    "compiler": "python-evm-transpiler",
                    "version": "0.1.0",
                    "gas_estimate": gas_estimate,
                    "state_variables": contract_state.variables,
                    "functions": list(contract_state.functions.keys())
                }
            }
            
            console.print("[green]✓ Transpilation completed successfully![/green]")
            console.print(f"[blue]Bytecode size: {len(full_bytecode)} bytes[/blue]")
            console.print(f"[blue]Estimated gas: {gas_estimate}[/blue]")
            
            return result
            
        except Exception as e:
            console.print(f"[red]Transpilation failed: {str(e)}[/red]")
            raise
    
    def _generate_abi(self, state: ContractState) -> List[Dict]:
        """Generate ABI from contract state."""
        abi = []
        
        # Constructor
        abi.append({
            "type": "constructor",
            "inputs": [],
            "stateMutability": "nonpayable"
        })
        
        # Functions
        for func_name, func_info in state.functions.items():
            if func_info.get('is_public', False) or func_info.get('is_view', False):
                # Determine outputs based on return detection and type analysis
                outputs = []
                if func_info.get('has_return', False) or func_info.get('is_view', False):
                    return_type = func_info.get('return_type', 'uint256')
                    outputs = [{"name": "", "type": return_type}]
                
                # Use enhanced parameter types in ABI
                param_types = func_info.get('param_types', [])
                args = func_info.get('args', [])
                
                inputs = []
                for i, arg in enumerate(args):
                    param_type = param_types[i] if i < len(param_types) else 'uint256'
                    inputs.append({"name": arg, "type": param_type})
                
                abi.append({
                    "type": "function",
                    "name": func_name,
                    "inputs": inputs,
                    "outputs": outputs,
                    "stateMutability": "view" if func_info.get('is_view') else "nonpayable"
                })
        
        # Events (placeholder)
        for event_name, params in state.events.items():
            abi.append({
                "type": "event",
                "name": event_name,
                "inputs": [
                    {"name": f"param{i}", "type": "uint256", "indexed": False}
                    for i in range(len(params))
                ]
            })
        
        return abi


def transpile_python_contract(source_code: str) -> Dict[str, Any]:
    """
    Convenience function to transpile Python smart contract.
    
    Args:
        source_code: Python smart contract source code
        
    Returns:
        Transpilation result with bytecode and ABI
    """
    transpiler = PythonContractTranspiler()
    return transpiler.transpile(source_code)