"""
TruthCert v3.1.0-FINAL - Setup Script

Meta-Analysis Verification Protocol
"""

from setuptools import setup, find_packages

setup(
    name="truthcert",
    version="3.1.0",
    description="TruthCert - Meta-Analysis Verification Protocol",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="TruthCert Team",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "truthcert=truthcert.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
