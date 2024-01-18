## Mobile LLM Agent

This project is a proof of concept of the LLM agent that can interact with the Android app via ADB tool and achieve the goal defined by the user.

The novelty of the project is that it is possible to achieve significantly better results than other mobile agents due to the fact that the LLM simultaneously sees a screenshot (image object) and the current screen layout (xml object obtained using adb tool).

#### Installation:
1. Export your Open AI KEY 
`export OPENAI_API_KEY=sk-4U7...`
2. Install the requirements
```
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

#### Run Android emulator:
1. Install Android Studio
2. Install ADB tool
3. Download the desired APK file (the agent can work with in any app) or install the app from the Google Play Store
4. Run the app in the emulator and find the path where the ADB is installed

#### Run the agent:
1. Remove the `data` before running the agent if you want to start from scratch (recommended).
2. `python3 anna_mobile_llm_agent/run_agent.py --adb_filepath=platform-tools/adb`
3. The agent will ask you to define the goal for the agent, enter the goal and press enter. Examples of the goals are below:
```
Instagram story creation example.

Please create a new story. 
Since it is the emulator it will have some mock recording of the camera (strange yellow-green image). 
The story should be accessible only for my 'close friends' and it should have a sample camera shot. 
This shot should be edited the following was: add the text "HELLO WORLD" in the middle
```

```
ANNA app. Auto documentation example.

Your goal is to learn the settings of the ANNA application and prepare useful documentation for our team.
Not all of our employees understand the specifics of how our clients interact with the application, since registration requires installing the latest version and passing KYB verification.
We want to fill this gap and prepare a document that can answer our questions about how various functions work in the application.
The expected document will be compiled from the results file.
1. Find the Settings section in the application
2. Improvise, learn and explore all the important screens / buttons / inputs and functions inside the Settings section (open sub-screens, scroll to explore more).
3. The documentation must be detailed (100-400 words per screen, not less). We need screenshots of screens, save them using action <save_screenshot> (do not create duplicate images), create a documentation and save it in the results in the following format: Title, General description of the screen, purpose, actions that the client can do in this screen to achieve a certain use case, the notes about specific points that it will be useful to display in the documentation.
```

```
ANNA app. Invoice creation example.

Go inside the briefcase/app menu (grey briefcase icon in the middle, bottom part of the screen).
Once there find "Invoices" functionality of the app and go there. Once you found it you will need to create a new invoice with some details.
In ANNA you can start invoice creation via chat or via the "Invoices" functionality.
Please start the creation from the "Invoices" functionality, and you will be redirected to the chat eventually.
Details of the invoice are not important, but enter at least 1 detail using the chat input and finish when the invoice is created.
```
4. The agent will start the interaction with the app and will try to achieve the goal and will save logs/goals/results file in the `data` folder

### LLM Agent in action video examples:
#### Instagram. Story creation example
[![Watch the video](https://img.youtube.com/vi/6_5oIGbe1Bc/0.jpg)](https://youtu.be/6_5oIGbe1Bc)

#### ANNA app. Invoice creation example
[![Watch the video](https://img.youtube.com/vi/8X7OSHMQv38/0.jpg)](https://youtu.be/8X7OSHMQv38)
