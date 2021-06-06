import setuptools
from setuptools import version


def getVersion():
    with open("discord_py_buttons/__init__.py") as f:
        return (
            [f for f in f.readlines() if f.startswith("__version__")][0]
            .split('"')[1]
            .split('"')[0]
        )


setuptools.setup(
    name="discord-py-buttons",
    version=getVersion(),
    author="RedstoneZockt, 404kuso",
    author_email="info@redstonezockt.de, bellou9022@gmail.com",
    description="A simple discord button handler for discord.py",
    long_description="",
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    classifiers=["Programming Language :: Python :: 3"],
)
