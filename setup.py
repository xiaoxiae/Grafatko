from setuptools import setup, find_packages
from os import path

script_location = path.abspath(path.dirname(__file__))

setup(
    # information about the package
    name="Grafatko",
    version="0.1",
    author="Tomáš Sláma",
    author_email="tomas@slama.dev",
    keywords="graph graphs pyqt5 algorithm algorithms",
    url="https://github.com/xiaoxiae/Grafatko",
    description="An app for creating and visualizing graphs and graph-related algorithms.",
    long_description=open(path.join(script_location, "README.md"), "r").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    # where to look for files
    packages=find_packages("src"),
    package_dir={"": "src"},
    data_files=[("", ["LICENSE.txt", "README.md"])],

    # requirements
    install_requires=["pyqt5 >= 5.14.2", "qtmodern >= 0.2.0"],
    python_requires='>=3.8',
)
