import os

from invoke import task

from examples.run_examples import run_all as run_all_examples

CURRENT_DIR = os.path.dirname(__file__)


@task
def clean(c, docs=True, bytecode=False, tox=False, extra=""):
    patterns = ["build", "dist", ".pytest_cache", "**/*.egg-info", ".mypy_cache", "htmlcov"]
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
def test(c):
    print(f"[{'=' * 10} Running Pytest {'=' * 10}]")
    c.run("pytest -v --cov=src/event_processor/ --cov-fail-under=100 --cov-report html src/tests")

    print(f"\n\n[{'=' * 10} Running Doctests {'=' * 10}]")
    c.run("cd docs && make doctest && cd ..")

    print(f"\n\n[{'=' * 10} Running Examples {'=' * 10}]")
    run_all_examples()


@task
def package(c):
    c.run("python setup.py sdist bdist_wheel")


@task
def check_package(c):
    c.run("twine check --strict dist/*")


@task
def all_checks(c):
    c.run("inv clean build -d test package check-package")


@task
def publish(c, token="", pypi_url="https://test.pypi.org/legacy/"):
    os.environ["TWINE_USERNAME"] = "__token__"
    os.environ["TWINE_REPOSITORY_URL"] = pypi_url
    if token:
        os.environ["TWINE_PASSWORD"] = token
    c.run(f"twine upload dist/*")


@task
def get_latest(_c):
    import requests

    resp = requests.get("https://api.github.com/repos/marier-nico/event-processor/releases/latest").json()
    print(resp["tag_name"], end="")
