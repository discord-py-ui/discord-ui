import setuptools

def get_version():
    """returns the version of the package"""
    with open("./discord_ui/__init__.py", "r", encoding="utf-8") as f:
        return [f for f in f.readlines() if f.startswith("__version__")][0].split('"')[1].split('"')[0]
def get_name():
    """returns the name of the package"""
    with open("./discord_ui/__init__.py", "r", encoding="utf-8") as f:
        return [f for f in f.readlines() if f.startswith("__title__")][0].split('"')[1].split('"')[0]
def get_readme():
    """returns the readme content for the package"""
    with open("./README.md", "r", encoding="utf-8") as f:
        return f.read()
def get_author():
    """returns the name of the authors"""
    with open("./README.md", "r", encoding="utf-8") as f:
        with open("./discord_ui/__init__.py", "r", encoding="utf-8") as f:
            return [f for f in f.readlines() if f.startswith("__author__")][0].split('"')[1].split('"')[0]

setuptools.setup(
    name=get_name(),
    version=get_version(),
    project_urls={
        "Documentation": "https://discord-ui.rtfd.io/en/latest/",
        "Issue tracker": "https://github.com/discord-py-ui/discord-ui/issues",
    },
    author=get_author(),
    author_email="bellou9022@gmail.com, redstoneprofihd@gmail.com",
    description="A disord.py extension for discord's ui/interaction features",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/discord-py-ui/discord-ui/",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ]
)
