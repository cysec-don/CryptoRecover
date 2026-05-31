#!/usr/bin/env python3
"""
CryptoRecover - Setup Script
=============================
Cross-platform installer for Windows, Linux, and macOS.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="cryptorecover",
    version="2.0.0",
    author="Cysec Don",
    author_email="cysecdon@gmail.com",
    description="AI-Enhanced Cryptocurrency Wallet Recovery Tool - Advanced bruteforce engine with novel techniques",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cysec-don/CryptoRecover",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(where=".", exclude=["tests*", "docs*"]),
    package_data={
        "cryptorecover_pkg.config": ["*.txt"],
    },
    include_package_data=True,
    install_requires=[
        "setuptools>=68.0",
    ],
    extras_require={
        "crypto": [
            "bip32utils>=0.0.7",
            "hdwallet>=2.1.1",
            "pycryptodome>=3.18.0",
            "cryptography>=41.0.0",
        ],
        "full": [
            "bip32utils>=0.0.7",
            "hdwallet>=2.1.1",
            "pycryptodome>=3.18.0",
            "cryptography>=41.0.0",
            "click>=8.1.0",
            "rich>=13.0.0",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cryptorecover=cryptorecover_pkg.cli.main:main",
        ],
        "gui_scripts": [
            "cryptorecover-gui=cryptorecover_pkg.gui.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Security :: Cryptography",
    ],
    keywords=["crypto", "wallet", "recovery", "seed-phrase", "bip39", "bitcoin"],
)
