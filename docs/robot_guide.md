# Pepper robot guide
## Connecting to the Pepper network
1. Ensure the network router has been plugged in. Ask a teacher or TA if in doubt.
2. Connect your laptop to the `Pepper` WiFi
    - SSID: **Pepper**
    - Password: **60169283**

## Turning on Pepper
1. Ensure the network router has been plugged in. Ask a teacher or TA if in doubt.
2. Press the start button on the stomach behind the tablet once quickly.
3. Light should come on in both eyes and shoulders.

## Getting Pepper IP address
1. Ensure Pepper is on and standing straight up
2. Press the button on the stomach behind the tablet once quickly
3. Pepper should say its IP address out loud.

## Connecting to Pepper
1. Ensure your laptop is connected to the `Pepper` network
2. Use either the [robot/robot_client.py](robot/robot_client.py) or [client.py](client.py) to test the connection. Examples:
    - [robot/robot_client.py](robot/robot_client.py): `python3 robot/robot_client.py INSERT_PEPPER_IP`
    - [client.py](client.py): `java -jar server.jar -g -s 300 -c "python3 client.py robot --ip INSERT_PEPPER_IP" -l levels/MAsimplegoalrecognition.lvl`

**Troubleshooting:**  
- Running into the exception: **Robot's IP not in configuration file, please update the configuration file with the correct robot IP.**
    - It happens that the robots change IP, when this happens, update the IP of your robot in  [robot_config.json](robot/robot_config.json) based on the robots ID.

## Putting Pepper to sleep/hibernate
1. Press the button on the stomach behind the tablet **twice quickly**.
2. Pepper should transition to its safe sleeping pose, cooling the motors and saving power.

## Turning Pepper off
1. Press and hold the the button on the stomach behind the tablet, till Pepper says *"Gnuk Gnuk"*.
2. Pepper should now go into the sleeping position and turn off all lights.

## Localization
You may observe that the robot's navigational accuracy as slightly lacking. It's also very sensitive to its starting position within the cells. These inaccuracies can accumulate and potentially cause frustration. By utilizing the [robot/robot_utils.py::VisionStreamThread](robot/robot_utils.py) class you can obtain data on the nearest apriltag visible to the robot (specifically via the camera located below the mouth). This information can be used to implement a basic controller by completing the `localization_controller(video_thread: VideoStreamThread)` method in the [robot/robot_client.py::RobotClient](robot/robot_client.py) class.  
Remember that `localization_controller(video_thread: VideoStreamThread)` must utilize an active `VisionStreamThread` as a parameter, which you can assign by using the `instantiate_vision_processes` function (refer to the
\_\_main\_\_ script in [robot/robot_client.py](robot/robot_client.py) for further details).  

A solution might be to develop a controller that begins by aligning the robot to the closest apriltag, followed by ensuring the correct orientation through a continual loop (you may need to specify an epsilon for both centering and orientation to help determine completion). Immediately after every $n$ actions in the action plan, you can call the controller to help mitigate the cumulative error. One thing you may discover is that certain actions cause more substantial errors than others. This could be an important factor to consider when deciding the point to activate the controller during the execution of a plan.

## Whisper Speech Recognition
We'll use [OpenAI's Whisper](https://github.com/openai/whisper) for speech recognition because it works well in noisy situations. However the direct Whisper implementation is slow, and memory intensive, their quantized versions are therefor used instead provided through the [faster-whisper](https://github.com/SYSTRAN/faster-whisper) library.
Although Whisper handles noise well, stand near your robot when talking. The first time you use Whisper, loading the base model may take a while. This only happens once per session.   
Here's a code example from the demo that transcribes a temporary `test.wav` file in the `tmp` folder (this is where the robot.listen() function from [robot/robot_client.py](robot/robot_client.py) will save to):
```python
# %% Imports
from faster_whisper import WhisperModel

# %% Loading model
# List of available model names can be found here: 
# https://github.com/SYSTRAN/faster-whisper/blob/c26d609974ef7c36715f23f0fbcdb3f9b5f8a663/faster_whisper/transcribe.py#L625
whisper_model = WhisperModel("distil-small.en", 
    device="cpu", 
    compute_type="int8",
    download_root="tmp/whisper_models" # Ensures model weights are kept between container rebuilds
)

# %% Record audio
robot.listen(5)

# %% Transcribe audio file
audio_file = "tmp/test.wav"
segments, info = whisper_model.transcribe(audio_file, beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
```

## Adding new functionality
If you'd like to try new things and add more features to the robot client, go ahead. You can find the complete NAOqi API proxies here: http://doc.aldebaran.com/2-5/naoqi/index.html.  
You can also include other features not in the API. To do this easily, follow the general procedure in [robot/robot_client.py](robot/robot_client.py).  
If you have interesting ideas, but are unsure if they can work, ask the Robot TA for help.