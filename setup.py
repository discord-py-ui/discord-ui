import setuptools
from setuptools import version


def getVersion():
    with open("./discord_py_buttons/__init__.py", "r", encoding="utf-8") as f:
        return (
            [f for f in f.readlines() if f.startswith("__version__")][0]
            .split('"')[1]
            .split('"')[0]
        )


def getReadme():
    with open("./README.md", "r", encoding="utf-8") as f:
        return f.read()


setuptools.setup(
    name="discord-buttons",
    version=getVersion(),
    author="404kuso, RedstoneZockt, ",
    author_email="bellou9022@gmail.com, redstoneprofihd@gmail.com",
    description="A discord button handler for discord.py",
    long_description=getReadme(),
    long_description_content_type="text/markdown",
    url="https://github.com/KusoRedsto/discord_py_buttons",
    packages=setuptools.find_packages(),
    python_requires=">=3.9",
    classifiers=["Programming Language :: Python :: 3"],
)
