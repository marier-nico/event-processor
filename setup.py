import os
from setuptools import setup, find_packages

# Meta info
project_root = os.path.dirname(os.path.realpath(__file__))
with open(f"{project_root}/VERSION", "r") as version_file:
    version = version_file.readline().strip()
with open(f"{project_root}/README.rst", "r") as readme_file:
    readme = readme_file.read()

setup(
    name="event-processor",
    version=version,
    author="Nicolas Marier",
    author_email="software@nmarier.com",
    url="https://github.com/marier-nico/event-processor",
    description="Process input events",
    long_description=readme,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
    ],

    # Packages and depencies
    package_dir={"": "src"},
    packages=find_packages("event_processor"),
    install_requires=[],
    extras_require={},
    package_data={"": ["VERSION"]},

    # Other configurations
    zip_safe=True,
    platforms="any",
)
