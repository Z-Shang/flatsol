#!/usr/bin/env python3

VERSION = "0.0.1"

DESCRIPTION = "Yet Another Solidity Flattener"
CLASSIFIERS = [
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Topic :: Software Development",
]


def main():
    try:
        from setuptools import setup
    except ImportError:
        from distutils.core import setup

    with open("README.mkd") as fin:
        desc = fin.read().strip()

    options = {
        "name": "flatsol",
        "version": VERSION,
        "license": "GPLv3",
        "description": DESCRIPTION,
        "long_description": desc,
        "url": "https://github.com/Z-Shang/flatsol",
        "author": "zshang",
        "author_email": "z@gilgamesh.me",
        "classifiers": CLASSIFIERS,
        "packages": [
            "flatsol",
        ],
        "install_requires": ["fppy"],
        "entry_points": {
            "console_scripts": [
                "flatsol=flatsol:main",
            ]
        },
    }
    setup(**options)


if __name__ == "__main__":
    main()
