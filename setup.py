"""Setup configuration for CodeEval-Bench."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="codeeval-bench",
    version="1.0.0",
    author="Harshit Nigam",
    author_email="nigamh708@gmail.com",
    description="LLM Code Generation & Reasoning Evaluation Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/harshitnigam/codeeval-bench",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "pytest>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "codeeval=codeeval.cli:main",
        ],
    },
)
