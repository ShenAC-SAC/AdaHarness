from adaharness.models.openai_compatible import openai_compatible_config


if __name__ == "__main__":
    config = openai_compatible_config("example-model", base_url="https://api.example.com/v1")
    print(config)
