from adaharness.cli import main


if __name__ == "__main__":
    raise SystemExit(
        main(["compare", "--model", "example-model", "--taskset", "tasks/eval"])
    )
