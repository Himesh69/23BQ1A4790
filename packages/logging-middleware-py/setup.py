from setuptools import setup, find_packages

setup(
    name="logging-middleware",
    version="1.0.0",
    description="Reusable logging middleware for backend applications",
    author="",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.10",
)
