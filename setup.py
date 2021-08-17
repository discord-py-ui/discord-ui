import os
import setuptools


def get_version():
    """returns the version of the package"""
    with open("./discord_ui/__init__.py", "r", encoding="utf-8") as f:
        return (
            [f for f in f.readlines() if f.startswith("__version__")][0]
            .split('"')[1]
            .split('"')[0]
        )


def get_readme():
    """returns the readme content for the package"""
    with open("./README.md", "r", encoding="utf-8") as f:
        return f.read()


setuptools.setup(
    name="discord-ui",
    version=get_version(),
    author="404kuso, RedstoneZockt",
    author_email="bellou9022@gmail.com, redstoneprofihd@gmail.com",
    description="A discord user-interface extension for discord.py",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/KusoRedsto/discord-ui",
    packages=setuptools.find_packages(),
    python_requires=">=3.9" if "READTHEDOCS" not in os.environ else None,
    classifiers=["Programming Language :: Python :: 3"],
)
