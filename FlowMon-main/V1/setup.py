"""Setup configuration for PyMon."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pymon",
    version="2.0.0",
    author="PyMon Team",
    description="Python-powered smart contract deployment tool for Monad blockchain",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pymon",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "web3>=6.0.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "eth-account>=0.10.0",
        "cryptography>=41.0.0",
        "pycryptodome>=3.0.0",
    ],
    extras_require={
        "solidity": ["py-solc-x>=2.0.0"],  # Optional: For Solidity support
    },
    entry_points={
        "console_scripts": [
            "pymon=pymon.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "pymon": ["*.json", "templates/*"],
    },
)
