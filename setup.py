import os
import re

from setuptools import Command, find_namespace_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read(nome: str) -> str:
    with open(os.path.join(here, nome), encoding="utf-8") as file_obj:
        return file_obj.read()


def get_version_from_changelog() -> str:
    match = re.search(r"^## (\d+\.\d+\.\d+)\b", read("CHANGELOG.md"), re.MULTILINE)
    if not match:
        raise RuntimeError("Unable to find a release version in CHANGELOG.md.")
    return match.group(1)


version = get_version_from_changelog()


class VersionCommand(Command):
    """Custom command to print the library version."""

    description = "print library version"
    user_options: list = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print(version)


setup(
    author="Rafael Henter",
    author_email="rafael@henter.com.br",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
        "Intended Audience :: Developers",
        "Natural Language :: Portuguese (Brazilian)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    cmdclass={"version": VersionCommand},
    description=(
        "Tabelas fiscais brasileiras (NCM, CEST, CFOP, CST e outras) com espelho local "
        "versionado, busca por descrição e validação."
    ),
    entry_points={"console_scripts": ["brfiscal = brfiscal.__main__:main"]},
    install_requires=[],
    keywords="ncm cest nfe fiscal brasil receita-federal django",
    license="MIT",
    long_description=f"{read('README.md')}\n\n{read('CHANGELOG.md')}",
    long_description_content_type="text/markdown",
    name="brfiscal",
    package_data={"brfiscal": ["dados/*.json.gz", "py.typed"]},
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src", include=["brfiscal", "brfiscal.*"]),
    project_urls={
        "Source": "https://github.com/rhenter/brfiscal",
        "Issues": "https://github.com/rhenter/brfiscal/issues",
    },
    python_requires=">=3.10",
    url="https://github.com/rhenter/brfiscal",
    version=version,
)
