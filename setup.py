import os
import setuptools
from setuptools import version


def getVersion():
    with open("./discord_message_components/__init__.py", "r", encoding="utf-8") as f:
        return (
            [f for f in f.readlines() if f.startswith("__version__")][0]
            .split('"')[1]
            .split('"')[0]
        )


def getReadme():
    with open("./README.md", "r", encoding="utf-8") as f:
        return f.read()


setuptools.setup(
    name="discord-message-components",
    version=getVersion(),
    author="404kuso, RedstoneZockt",
    author_email="bellou9022@gmail.com, redstoneprofihd@gmail.com",
    description="A discord message component handler for discord.py",
    long_description=getReadme(),
    long_description_content_type="text/markdown",
    url="https://github.com/KusoRedsto/discord_py_buttons",
    packages=setuptools.find_packages(),
    python_requires=">=3.9" if "READTHEDOCS" not in os.environ else None,
    classifiers=["Programming Language :: Python :: 3"],
)
