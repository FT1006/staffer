from setuptools import setup, find_packages

setup(
    name="staffer",
    version="0.2.0",
    description="AI coding agent that works in any directory",
    author="Staffer Team",
    packages=find_packages(),
    install_requires=[
        "google-genai==1.12.1",
        "python-dotenv==1.1.0",
    ],
    entry_points={
        "console_scripts": [
            "staffer=staffer.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)