import os
import argparse

from agent import MobileLLMAgent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--llm_model_name',
        type=str, default='gpt-4-vision-preview',
        help='The name of the LLM model to use'
    )
    parser.add_argument(
        '--adb_filepath',
        type=str, required=True,
        help='Path to the ADB executable'
    )
    parser.add_argument(
        '--target_app_screen_id',
        type=str, default=None,
        help="""
        Optional. The screen ID of the target app in case if the LLM wants to launch the app via ADB, 
        example: 'com.anna.money.app.dev/com.anna.money.app.feature.splash.SplashScreen'
        """
    )

    if os.environ["OPENAI_API_KEY"] is None:
        raise Exception("Please set OPENAI_API_KEY in your environment variables.")

    args = parser.parse_args()
    ai_agent = MobileLLMAgent(
        llm_model_name=args.llm_model_name,
        adb_filepath=args.adb_filepath,
        target_app_screen_id=args.target_app_screen_id
    )
    ai_agent.start_agent()


if __name__ == '__main__':
    main()
