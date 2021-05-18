import sys

from src import event_processor

sys.modules["event_processor"] = event_processor


def run_all():
    # Imports need to be here because we have to add event_processor to sys.modules first
    from examples.database_usage.main import main as database_main

    database_main()


if __name__ == "__main__":
    run_all()
