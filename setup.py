from setuptools import setup, find_packages

setup(
    name="ai-chip-trading-signals",
    version="0.1.0",
    packages=find_packages(where="backend/src"),
    package_dir={"": "backend/src"},
    install_requires=[
        "pandas>=2.2.0",
        "numpy>=1.26.0",
        "yfinance>=0.2.18",
        "fredapi>=0.5.1",
        "requests>=2.31.0",
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "websockets>=12.0",
        "scikit-learn>=1.3.2",
        "scipy>=1.11.4",
        "sqlalchemy>=2.0.23",
        "schedule>=1.2.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "aiohttp>=3.8.0",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "seaborn>=0.12.0",
        "matplotlib>=3.7.0",
        "httpx>=0.24.0"
    ],
    python_requires=">=3.9"
)
