#!/usr/bin/env python3
"""Test script to check Solidity support in PyMon."""

from pymon.solidity_support import check_solidity_support, SOLIDITY_AVAILABLE

print("=" * 60)
print("PyMon Solidity Support Check")
print("=" * 60)
print(f"Solidity support available: {check_solidity_support()}")
print(f"SOLIDITY_AVAILABLE flag: {SOLIDITY_AVAILABLE}")

if SOLIDITY_AVAILABLE:
    print("\n✅ py-solc-x is installed")
    print("You can compile Solidity contracts if needed.")
    print("However, PyMon recommends using Python contracts instead!")
else:
    print("\n✅ PyMon is running in Python-native mode")
    print("No Solidity dependencies required!")
    print("Write contracts in Python and compile directly to EVM bytecode.")

print("\n" + "=" * 60)
print("PyMon works perfectly with Python contracts!")
print("=" * 60)
