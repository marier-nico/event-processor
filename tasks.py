import os
import requests
from invoke import task

CURRENT_DIR = os.path.dirname(__file__)


@task
def clean(c, docs=True, bytecode=False, tox=False, extra=""):
    patterns = ["build", "dist", ".pytest_cache", "**/*.egg-info", ".mypy_cache"]
    if docs:
        patterns.append("docs/_build")
    if bytecode:
        patterns.append("**/*.pyc")
    if extra:
        patterns.append(extra)
    if tox:
        patterns.append(".tox")
    for pattern in patterns:
        c.run("rm -rf {}".format(pattern))


@task
def build(c, docs=False):
    c.run("python setup.py build")
    if docs:
        c.run("sphinx-build docs docs/_build")


@task
def package(c):
    c.run("python setup.py sdist bdist_wheel")


@task
def check_package(c):
    c.run("twine check --strict dist/*")


@task
def publish(c, token="", pypi_url="https://test.pypi.org/legacy/"):
    os.environ["TWINE_USERNAME"] = "__token__"
    os.environ["TWINE_REPOSITORY_URL"] = pypi_url
    if token:
        os.environ["TWINE_PASSWORD"] = token
    c.run(f"twine upload dist/*")


@task
def get_latest(_c):
    resp = requests.get("https://api.github.com/repos/marier-nico/event-processor/releases/latest").json()
    print(resp["tag_name"], end="")
