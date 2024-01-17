import os
import argparse

from agent import MobileLLMAgent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb_filepath', type=str)

    if os.environ["OPENAI_API_KEY"] is None:
        raise Exception("Please set OPENAI_API_KEY in your environment variables.")

    args = parser.parse_args()
    ai_agent = MobileLLMAgent(args.adb_filepath)
    ai_agent.start_agent()


if __name__ == '__main__':
    main()
