import os
from setuptools import setup, find_packages

# Meta info
project_root = os.path.dirname(os.path.realpath(__file__))
with open(f"{project_root}/VERSION", "r") as version_file:
    version = version_file.readline().strip()
with open(f"{project_root}/README.md", "r") as readme_file:
    readme = readme_file.read()

setup(
    name="event-processor",
    version=version,
    author="Nicolas Marier",
    author_email="software@nmarier.com",
    url="https://github.com/marier-nico/event-processor",
    project_urls={
        "Documentation": "https://event-processor.readthedocs.io/en/latest/",
        "Source": "https://github.com/marier-nico/event-processor",
        "Tracker": "https://github.com/marier-nico/event-processor/issues"
    },
    description="Pythonic event-processing library based on decorators",
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="event decorators development",

    # Packages and depencies
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[],
    extras_require={},
    package_data={"": ["VERSION"]},

    # Other configurations
    zip_safe=True,
    platforms="any",
)
