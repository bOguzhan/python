from setuptools import setup, find_packages

setup(
    name="p2p_network",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "asyncio>=3.4.3",
        "socket>=3.0.0",
        "argparse>=1.4.0",
    ],
    python_requires=">=3.8",
    author="Your Name",
    description="A peer-to-peer networking application with NAT hole punching",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
