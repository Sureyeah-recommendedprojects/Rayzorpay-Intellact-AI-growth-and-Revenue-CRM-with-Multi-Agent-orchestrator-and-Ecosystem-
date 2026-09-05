"""
Enhanced Python to EVM Transpiler with Proper ABI Encoding
Fixes critical issues with storage, function returns, and ABI compliance
"""

import ast
import json
import struct
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
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


def calculate_mapping_slot(key: Union[int, bytes], base_slot: int) -> int:
    """
    Calculate storage slot for mapping using Solidity's formula:
    keccak256(h(k) . p) where:
    - k is the key
    - p is the base storage slot
    - h is encoding function based on key type
    - . is concatenation
    """
    if isinstance(key, int):
        # Pad key to 32 bytes
        key_bytes = key.to_bytes(32, 'big')
    else:
        key_bytes = key
    
    # Pad base_slot to 32 bytes
    slot_bytes = base_slot.to_bytes(32, 'big')
    
    # Concatenate: key . slot
    data = key_bytes + slot_bytes
    
    # Hash and convert to int
    hash_result = keccak256(data)
    return int.from_bytes(hash_result, 'big')


class EVMOpcode:
    """EVM Opcodes."""
    STOP = 0x00
    ADD = 0x01
    MUL = 0x02
    SUB = 0x03
    DIV = 0x04
    MOD = 0x06
    EXP = 0x0a
    LT = 0x10
    GT = 0x11
    EQ = 0x14
    ISZERO = 0x15
    AND = 0x16
    OR = 0x17
    XOR = 0x18
    NOT = 0x19
    SHL = 0x1b
    SHR = 0x1c
    SHA3 = 0x20
    ADDRESS = 0x30
    CALLER = 0x33
    CALLVALUE = 0x34
    CALLDATALOAD = 0x35
    CALLDATASIZE = 0x36
    CALLDATACOPY = 0x37
    CODESIZE = 0x38
    CODECOPY = 0x39
    MLOAD = 0x51
    MSTORE = 0x52
    MSTORE8 = 0x53
    SLOAD = 0x54
    SSTORE = 0x55
    JUMP = 0x56
    JUMPI = 0x57
    PC = 0x58
    MSIZE = 0x59
    JUMPDEST = 0x5b
    PUSH1 = 0x60
    PUSH2 = 0x61
    PUSH4 = 0x63
    PUSH32 = 0x7f
    DUP1 = 0x80
    DUP2 = 0x81
    DUP3 = 0x82
    DUP4 = 0x83
    SWAP1 = 0x90
    SWAP2 = 0x91
    RETURN = 0xf3
    REVERT = 0xfd


@dataclass
class ContractState:
    """Contract state with storage mapping."""
    variables: Dict[str, int]
    functions: Dict[str, Any]
    events: Dict[str, List[str]]
    initial_values: Dict[str, Any]
    variable_types: Dict[str, str]


class ABIEncoder:
    """Handles ABI encoding/decoding for function parameters and return values."""
    
    @staticmethod
    def encode_uint256(value: int) -> bytes:
        """Encode uint256 to 32 bytes."""
        return value.to_bytes(32, 'big')
    
    @staticmethod
    def encode_address(address: Union[int, str]) -> bytes:
        """Encode address to 32 bytes (left-padded)."""
        if isinstance(address, str):
            if address.startswith('0x'):
                address = int(address, 16)
            else:
                address = int(address)
        return address.to_bytes(32, 'big')
    
    @staticmethod
    def encode_bytes32(data: Union[bytes, str]) -> bytes:
        """Encode bytes32 to 32 bytes."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return data.ljust(32, b'\x00')
    
    @staticmethod
    def decode_uint256(data: bytes) -> int:
        """Decode uint256 from 32 bytes."""
        return int.from_bytes(data[:32], 'big')
    
    @staticmethod
    def decode_address(data: bytes) -> int:
        """Decode address from 32 bytes."""
        return int.from_bytes(data[:32], 'big')


class EnhancedBytecodeGenerator:
    """Enhanced bytecode generator with proper ABI encoding."""
    
    def __init__(self):
        self.init_code = bytearray()
        self.runtime_code = bytearray()
        self.current_mode = 'init'
        self.current_state = None
        self.gas_used = 0
        self.memory_offset = 0  # Track memory usage
        
    def emit(self, opcode: int):
        """Emit single opcode."""
        if self.current_mode == 'init':
            self.init_code.append(opcode)
        else:
            self.runtime_code.append(opcode)
    
    def emit_push(self, value: Union[int, bytes], size: Optional[int] = None):
        """Emit PUSH with automatic size detection."""
        if isinstance(value, int):
            if size is None:
                size = max(1, (value.bit_length() + 7) // 8)
            value_bytes = value.to_bytes(size, 'big')
        else:
            value_bytes = value
            size = len(value_bytes)
        
        size = min(size, 32)  # Max PUSH32
        push_opcode = EVMOpcode.PUSH1 + size - 1
        
        if self.current_mode == 'init':
            self.init_code.append(push_opcode)
            self.init_code.extend(value_bytes[-size:])
        else:
            self.runtime_code.append(push_opcode)
            self.runtime_code.extend(value_bytes[-size:])
        
        self.gas_used += 3
    
    def get_offset(self) -> int:
        """Get current bytecode offset."""
        return len(self.runtime_code) if self.current_mode == 'runtime' else len(self.init_code)
    
    def set_mode(self, mode: str):
        """Set bytecode generation mode."""
        self.current_mode = mode
    
    def generate_abi_encoded_return(self, value_type: str = 'uint256'):
        """
        Generate proper ABI-encoded return value.
        Stack: [value]
        Result: Returns ABI-encoded value
        """
        # Store value at memory position 0
        self.emit_push(0)  # Memory offset
        self.emit(EVMOpcode.MSTORE)  # MSTORE pops offset and value
        
        # Return 32 bytes from memory position 0
        self.emit_push(32)  # Size
        self.emit_push(0)   # Offset
        self.emit(EVMOpcode.RETURN)
    
    def generate_function_dispatcher(self, functions: Dict[str, Any]) -> Dict[str, int]:
        """
        Generate optimized function dispatcher with proper selector matching.
        Returns dict of function_name -> bytecode_offset
        """
        console.print("[blue]Generating function dispatcher...[/blue]")
        
        # Check if we have enough calldata
        self.emit_push(4)
        self.emit(EVMOpcode.CALLDATASIZE)
        self.emit(EVMOpcode.LT)
        
        # If calldatasize < 4, revert
        revert_offset = self.get_offset() + 3
        self.emit_push(0xFFFF, 2)  # Placeholder
        self.emit(EVMOpcode.JUMPI)
        
        # Load function selector
        self.emit_push(0)
        self.emit(EVMOpcode.CALLDATALOAD)
        self.emit_push(224)  # Shift right by 224 bits (256-32=224)
        self.emit(EVMOpcode.SHR)
        
        # Generate selector checks
        function_offsets = {}
        placeholders = {}
        
        for func_name, func_info in functions.items():
            if not (func_info.get('is_public') or func_info.get('is_view')):
                continue
            
            param_types = func_info.get('param_types', [])
            signature = f"{func_name}({','.join(param_types)})"
            selector = function_selector(signature)
            selector_int = int.from_bytes(selector, 'big')
            
            console.print(f"[yellow]{signature} -> 0x{selector.hex()}[/yellow]")
            
            # DUP1 (duplicate selector on stack)
            self.emit(EVMOpcode.DUP1)
            # PUSH4 expected_selector
            self.emit_push(selector_int, 4)
            # EQ
            self.emit(EVMOpcode.EQ)
            
            # Store placeholder location
            placeholder_offset = self.get_offset() + 1
            placeholders[func_name] = placeholder_offset
            
            # PUSH2 jump_target (placeholder)
            self.emit_push(0xDEAD, 2)
            # JUMPI
            self.emit(EVMOpcode.JUMPI)
        
        # No function matched - revert
        revert_start = self.get_offset()
        self.emit(EVMOpcode.JUMPDEST)
        self.emit_push(0)
        self.emit_push(0)
        self.emit(EVMOpcode.REVERT)
        
        # Backpatch initial revert jump
        self._backpatch(revert_offset, revert_start, 2)
        
        return placeholders
    
    def generate_function_body(self, func_name: str, func_info: Dict, state: ContractState):
        """Generate function body with proper ABI encoding."""
        is_view = func_info.get('is_view', False)
        has_return = func_info.get('has_return', False)
        args = func_info.get('args', [])
        param_types = func_info.get('param_types', [])
        
        # Create arg map for calldata loading
        arg_map = {arg: i for i, arg in enumerate(args)}
        
        # Compile function body
        for stmt in func_info.get('body', []):
            self._compile_statement(stmt, arg_map, state)
        
        # If view function or has_return, ensure proper return
        if is_view or has_return:
            # Check if last statement is return
            body = func_info.get('body', [])
            if not body or not isinstance(body[-1], ast.Return):
                # Add default return of 0
                self.emit_push(0)
                self.generate_abi_encoded_return(func_info.get('return_type', 'uint256'))
        else:
            # Non-view function without return - return empty
            self.emit_push(0)
            self.emit_push(0)
            self.emit(EVMOpcode.RETURN)
    
    def _compile_statement(self, stmt: ast.AST, arg_map: Dict, state: ContractState):
        """Compile a Python statement to EVM bytecode."""
        if isinstance(stmt, ast.Return):
            if stmt.value:
                # Compile return expression
                self._compile_expression(stmt.value, arg_map, state)
                # Generate ABI-encoded return
                self.generate_abi_encoded_return()
            else:
                # Empty return
                self.emit_push(0)
                self.emit_push(0)
                self.emit(EVMOpcode.RETURN)
        
        elif isinstance(stmt, ast.Assign):
            # Handle assignment
            if len(stmt.targets) == 1:
                target = stmt.targets[0]
                
                if isinstance(target, ast.Attribute):
                    # self.var = value
                    if isinstance(target.value, ast.Name) and target.value.id == 'self':
                        var_name = target.attr
                        if var_name in state.variables:
                            # Compile value
                            self._compile_expression(stmt.value, arg_map, state)
                            # Store in storage
                            slot = state.variables[var_name]
                            self.emit_push(slot)
                            self.emit(EVMOpcode.SSTORE)
                
                elif isinstance(target, ast.Subscript):
                    # self.mapping[key] = value
                    if (isinstance(target.value, ast.Attribute) and
                        isinstance(target.value.value, ast.Name) and
                        target.value.value.id == 'self'):
                        mapping_name = target.value.attr
                        if mapping_name in state.variables:
                            # Compile value
                            self._compile_expression(stmt.value, arg_map, state)
                            
                            # Calculate mapping slot using keccak256
                            self._compile_mapping_slot(target.slice, state.variables[mapping_name], arg_map, state)
                            
                            # SSTORE
                            self.emit(EVMOpcode.SSTORE)
        
        elif isinstance(stmt, ast.If):
            # Compile if statement
            self._compile_if_statement(stmt, arg_map, state)
        
        elif isinstance(stmt, ast.Expr):
            # Expression statement (like self.event())
            # For now, ignore events in bytecode
            pass
    
    def _compile_expression(self, expr: ast.AST, arg_map: Dict, state: ContractState):
        """Compile Python expression to EVM bytecode."""
        if isinstance(expr, ast.Constant):
            self.emit_push(expr.value if isinstance(expr.value, int) else 0)
        
        elif isinstance(expr, ast.Num):
            self.emit_push(expr.n)
        
        elif isinstance(expr, ast.Name):
            # Variable reference
            if expr.id in arg_map:
                # Function argument - load from calldata
                arg_index = arg_map[expr.id]
                offset = 4 + arg_index * 32
                self.emit_push(offset)
                self.emit(EVMOpcode.CALLDATALOAD)
            else:
                self.emit_push(0)  # Unknown variable
        
        elif isinstance(expr, ast.Attribute):
            # self.var access
            if isinstance(expr.value, ast.Name) and expr.value.id == 'self':
                if expr.attr in state.variables:
                    slot = state.variables[expr.attr]
                    self.emit_push(slot)
                    self.emit(EVMOpcode.SLOAD)
                else:
                    self.emit_push(0)
            else:
                self.emit_push(0)
        
        elif isinstance(expr, ast.Subscript):
            # self.mapping[key] access
            if (isinstance(expr.value, ast.Attribute) and
                isinstance(expr.value.value, ast.Name) and
                expr.value.value.id == 'self'):
                mapping_name = expr.value.attr
                if mapping_name in state.variables:
                    # Calculate mapping slot
                    self._compile_mapping_slot(expr.slice, state.variables[mapping_name], arg_map, state)
                    # SLOAD
                    self.emit(EVMOpcode.SLOAD)
                else:
                    self.emit_push(0)
            else:
                self.emit_push(0)
        
        elif isinstance(expr, ast.BinOp):
            # Binary operation
            self._compile_expression(expr.left, arg_map, state)
            self._compile_expression(expr.right, arg_map, state)
            
            if isinstance(expr.op, ast.Add):
                self.emit(EVMOpcode.ADD)
            elif isinstance(expr.op, ast.Sub):
                self.emit(EVMOpcode.SUB)
            elif isinstance(expr.op, ast.Mult):
                self.emit(EVMOpcode.MUL)
            elif isinstance(expr.op, ast.Div):
                self.emit(EVMOpcode.DIV)
            elif isinstance(expr.op, ast.Mod):
                self.emit(EVMOpcode.MOD)
        
        elif isinstance(expr, ast.Compare):
            # Comparison
            self._compile_expression(expr.left, arg_map, state)
            if expr.comparators:
                self._compile_expression(expr.comparators[0], arg_map, state)
                
                if isinstance(expr.ops[0], ast.Eq):
                    self.emit(EVMOpcode.EQ)
                elif isinstance(expr.ops[0], ast.Lt):
                    self.emit(EVMOpcode.SWAP1)
                    self.emit(EVMOpcode.LT)
                elif isinstance(expr.ops[0], ast.Gt):
                    self.emit(EVMOpcode.SWAP1)
                    self.emit(EVMOpcode.GT)
                elif isinstance(expr.ops[0], ast.LtE):
                    self.emit(EVMOpcode.SWAP1)
                    self.emit(EVMOpcode.GT)
                    self.emit(EVMOpcode.ISZERO)
                elif isinstance(expr.ops[0], ast.GtE):
                    self.emit(EVMOpcode.SWAP1)
                    self.emit(EVMOpcode.LT)
                    self.emit(EVMOpcode.ISZERO)
        else:
            self.emit_push(0)
    
    def _compile_mapping_slot(self, key_expr: ast.AST, base_slot: int, arg_map: Dict, state: ContractState):
        """
        Compile mapping slot calculation using keccak256.
        Stack result: [calculated_slot]
        """
        # For proper Solidity-compatible mapping:
        # slot = keccak256(key . base_slot)
        
        # Compile key expression
        self._compile_expression(key_expr, arg_map, state)
        
        # Store key at memory position 0
        self.emit_push(0)
        self.emit(EVMOpcode.MSTORE)
        
        # Store base_slot at memory position 32
        self.emit_push(base_slot)
        self.emit_push(32)
        self.emit(EVMOpcode.MSTORE)
        
        # Calculate keccak256 of 64 bytes starting at position 0
        self.emit_push(64)  # Length
        self.emit_push(0)   # Offset
        self.emit(EVMOpcode.SHA3)  # keccak256
        
        # Result: calculated slot is now on stack
    
    def _compile_if_statement(self, stmt: ast.If, arg_map: Dict, state: ContractState):
        """Compile if statement with proper jump handling."""
        # Compile condition
        self._compile_expression(stmt.test, arg_map, state)
        
        # ISZERO (invert for JUMPI)
        self.emit(EVMOpcode.ISZERO)
        
        # JUMPI to else/end
        else_placeholder = self.get_offset() + 1
        self.emit_push(0xDEAD, 2)
        self.emit(EVMOpcode.JUMPI)
        
        # Compile if body
        for s in stmt.body:
            self._compile_statement(s, arg_map, state)
        
        # Jump to end
        end_placeholder = self.get_offset() + 1
        self.emit_push(0xBEEF, 2)
        self.emit(EVMOpcode.JUMP)
        
        # Else block
        else_offset = self.get_offset()
        self.emit(EVMOpcode.JUMPDEST)
        
        # Compile else body
        for s in stmt.orelse:
            self._compile_statement(s, arg_map, state)
        
        # End
        end_offset = self.get_offset()
        self.emit(EVMOpcode.JUMPDEST)
        
        # Backpatch jumps
        self._backpatch(else_placeholder, else_offset, 2)
        self._backpatch(end_placeholder, end_offset, 2)
    
    def _backpatch(self, offset: int, target: int, size: int):
        """Backpatch a jump target."""
        target_bytes = target.to_bytes(size, 'big')
        if self.current_mode == 'init':
            self.init_code[offset:offset+size] = target_bytes
        else:
            self.runtime_code[offset:offset+size] = target_bytes
    
    def generate_constructor(self, state: ContractState, runtime_size: int):
        """Generate constructor bytecode."""
        console.print("[blue]Generating constructor...[/blue]")
        
        # Initialize state variables
        for var_name, slot in state.variables.items():
            initial_value = state.initial_values.get(var_name, 0)
            if isinstance(initial_value, int):
                self.emit_push(initial_value)
                self.emit_push(slot)
                self.emit(EVMOpcode.SSTORE)
        
        # Copy runtime code to memory and return
        runtime_offset = len(self.init_code) + 13
        
        self.emit_push(runtime_size, 2)
        self.emit_push(runtime_offset, 2)
        self.emit(EVMOpcode.DUP2)
        self.emit_push(0)
        self.emit(EVMOpcode.CODECOPY)
        self.emit_push(0)
        self.emit(EVMOpcode.RETURN)


# Integration with existing transpiler
from pymon.transpiler import (
    PythonASTAnalyzer, 
    PythonContractTranspiler as OriginalTranspiler
)

class EnhancedTranspiler(OriginalTranspiler):
    """Enhanced transpiler with fixed bytecode generation."""
    
    def __init__(self):
        super().__init__()
        self.generator = EnhancedBytecodeGenerator()
    
    def transpile(self, source_code: str) -> Dict[str, Any]:
        """Transpile with enhanced bytecode generation."""
        console.print("[bold blue]Starting enhanced transpilation...[/bold blue]")
        
        # Analyze (use existing analyzer)
        console.print("[yellow]Step 1: Analyzing AST...[/yellow]")
        contract_state = self.analyzer.analyze_contract(source_code)
        
        # Generate bytecode with enhanced generator
        console.print("[yellow]Step 2: Generating enhanced bytecode...[/yellow]")
        bytecode = self._generate_enhanced_bytecode(contract_state)
        
        # Generate ABI
        console.print("[yellow]Step 3: Generating ABI...[/yellow]")
        abi = self._generate_abi(contract_state)
        
        result = {
            "bytecode": "0x" + bytecode.hex(),
            "abi": abi,
            "metadata": {
                "compiler": "pymon-enhanced",
                "version": "2.0.0",
                "gas_estimate": self.generator.gas_used,
                "improvements": [
                    "Proper ABI encoding",
                    "Fixed storage layout",
                    "Keccak256 mapping slots",
                    "Correct return values"
                ]
            }
        }
        
        console.print(f"[green]✓ Enhanced transpilation complete![/green]")
        console.print(f"[blue]Bytecode size: {len(bytecode)} bytes[/blue]")
        
        return result
    
    def _generate_enhanced_bytecode(self, state: ContractState) -> bytes:
        """Generate complete bytecode with enhanced generator."""
        gen = self.generator
        
        # Generate runtime first
        gen.set_mode('runtime')
        
        # Function dispatcher
        placeholders = gen.generate_function_dispatcher(state.functions)
        
        # Generate function bodies
        for func_name, func_info in state.functions.items():
            if not (func_info.get('is_public') or func_info.get('is_view')):
                continue
            
            # Mark function start
            func_start = gen.get_offset()
            gen.emit(EVMOpcode.JUMPDEST)
            
            # Generate function body
            gen.current_state = state
            gen.generate_function_body(func_name, func_info, state)
            
            # Backpatch jump target
            if func_name in placeholders:
                gen._backpatch(placeholders[func_name], func_start, 2)
        
        runtime_bytecode = bytes(gen.runtime_code)
        
        # Generate constructor
        gen.set_mode('init')
        gen.generate_constructor(state, len(runtime_bytecode))
        
        # Combine
        return bytes(gen.init_code + gen.runtime_code)


def transpile_python_contract_enhanced(source_code: str) -> Dict[str, Any]:
    """Enhanced transpilation with proper ABI encoding."""
    transpiler = EnhancedTranspiler()
    return transpiler.transpile(source_code)


if __name__ == "__main__":
    # Test
    test_contract = '''
class TestContract(PySmartContract):
    def __init__(self):
        self.count = 0
        self.owner = 0
    
    @public_function
    def increment(self):
        self.count = self.count + 1
    
    @view_function
    def get_count(self):
        return self.count
'''
    
    result = transpile_python_contract_enhanced(test_contract)
    print(f"Bytecode: {result['bytecode'][:100]}...")
    print(f"Functions: {result['metadata']['improvements']}")
