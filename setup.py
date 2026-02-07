"""
Scrat-Backup - Setup-Konfiguration
Windows Backup-Tool für Privatnutzer
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="scrat-backup",
    version="0.2.1",
    author="Scrat-Backup Contributors",
    author_email="nicoletta@muggelbude.it",
    description="Plattformübergreifendes Backup-Tool mit Verschlüsselung (Windows, Linux, macOS)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nicolettas-muggelbude/scrat-backup",
    project_urls={
        "Bug Tracker": "https://github.com/nicolettas-muggelbude/scrat-backup/issues",
        "Documentation": "https://github.com/nicolettas-muggelbude/scrat-backup/blob/main/claude.md",
        "Source Code": "https://github.com/nicolettas-muggelbude/scrat-backup",
    },
    packages=find_packages(),
    classifiers=[
        # Development Status
        "Development Status :: 2 - Pre-Alpha",

        # Intended Audience
        "Intended Audience :: End Users/Desktop",

        # License
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",

        # OS
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",

        # Programming Language
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",

        # Topics
        "Topic :: System :: Archiving :: Backup",
        "Topic :: Security :: Cryptography",

        # Natural Language
        "Natural Language :: German",
        "Natural Language :: English",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black==26.1.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "isort>=5.13.0",
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
        ],
        "build": [
            "pyinstaller>=6.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scrat-backup=src.main:main",
        ],
        "gui_scripts": [
            "scrat-backup-gui=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.qss", "*.ico", "*.svg", "*.png"],
    },
    zip_safe=False,
    keywords=[
        "backup",
        "encryption",
        "windows",
        "aes-256",
        "privacy",
        "data-protection",
        "incremental-backup",
        "sftp",
        "webdav",
    ],
)
