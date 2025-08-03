#!/usr/bin/env python3
"""
Setup script for GitHub Organization Backup System
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "GitHub Organization Backup System"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="github-org-backup",
    version="1.0.0",
    description="Automated backup system for GitHub organization repositories to multiple Git hosting services",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Your Organization",
    author_email="admin@your-org.com",
    url="https://github.com/your-org/github-backup",
    packages=find_packages(),
    py_modules=[
        'backup_organization',
        'github_backup',
        'backup_targets',
        'notification_manager',
        'utils'
    ],
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'github-backup=backup_organization:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.8",
    keywords="github backup gitlab gitea bitbucket mirror repository",
    project_urls={
        "Bug Reports": "https://github.com/your-org/github-backup/issues",
        "Source": "https://github.com/your-org/github-backup",
        "Documentation": "https://github.com/your-org/github-backup/blob/main/README.md",
    },
) 