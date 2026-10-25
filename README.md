# English Speaking Game 3.0

A desktop application designed to help English learners improve their speaking confidence through simple, sentence-based practice.

The game displays an English sentence, listens as the player reads it aloud, and uses speech recognition to compare what was heard with the original sentence. Players receive immediate feedback and can track their progress over time.

Created by **Memory[Laine](@128Cores)**.

## Features

- Clean Tkinter desktop interface
- 5,000 English practice sentences
- Custom rounds containing 1–50 sentences
- Microphone-based speech recognition
- Text-to-speech pronunciation examples
- Immediate correct or incorrect feedback
- Displays what the speech recognizer heard
- Custom sentence support
- Automatically saved progress
- Accuracy, score, and personal-best statistics
- Randomized sentences for every round

## How It Works

1. Choose how many sentences you want to practice.
2. Read the displayed sentence aloud.
3. The game records your voice through your microphone.
4. Google Speech Recognition converts your speech into text.
5. The recognized text is compared with the displayed sentence.
6. Your score and statistics are automatically updated.

You can also listen to the correct pronunciation before recording your attempt.

> This game uses speech-to-text matching. It is intended for casual English practice and does not provide detailed phonetic or accent analysis.

## Requirements

- Python 3.13 recommended
- A working microphone
- An internet connection
- Windows, macOS, or Linux

The internet connection is required for Google Speech Recognition and Google Text-to-Speech.

## Installation

Download the project and open a terminal inside its folder.

Install the required packages:

```bash
python -m pip install SpeechRecognition gTTS pygame PyAudio
```

On Windows, you can also use:

```powershell
py -3.13 -m pip install SpeechRecognition gTTS pygame PyAudio
```

Run the game:

```bash
python EnglishSpeakingGame3.0.py
```

Or on Windows:

```powershell
py -3.13 EnglishSpeakingGame3.0.py
```

## Project Files

```text
EnglishSpeakingGame3.0.py
Sentences.txt
SavesData.txt
LICENSE
README.md
```

- `EnglishSpeakingGame3.0.py` contains the game and its interface.
- `Sentences.txt` contains the sentence library.
- `SavesData.txt` stores the player's progress and is created automatically.
- `LICENSE` contains the MIT License.
- `README.md` contains information about the project.

Keep `Sentences.txt` in the same folder as the Python script or executable.

If the sentence file is missing or empty, the game will create a small default sentence list.

## Using the Game

### Practice

Open the **Practice** page and choose the number of sentences you want in the round.

For each sentence:

- Select **Hear sentence** to hear the correct pronunciation.
- Select **Start listening** and read the sentence aloud.
- Review the recognized speech and feedback.
- Select **Next sentence** to continue.

A result screen will appear when the round is complete.

### Sentence Library

The **Sentences** page displays every available practice sentence.

You can add your own sentence using the text box at the bottom of the page. New sentences are saved directly to `Sentences.txt`.

### Statistics

The **Statistics** page tracks:

- Rounds played
- Correct attempts
- Incorrect attempts
- Overall accuracy
- Best score
- Best round accuracy
- Last saved time

Progress can also be reset from this page.

## Custom Sentences

`Sentences.txt` is a normal UTF-8 text file. Each line represents one practice sentence.

```text
Could you speak more slowly?
I would like a glass of water.
Where is the nearest train station?
```

Blank lines are ignored. Sentences should use natural capitalization and punctuation.

## Building a Windows Executable

Install PyInstaller:

```powershell
py -3.13 -m pip install --upgrade pyinstaller
```

Build the application:

```powershell
py -3.13 -m PyInstaller --noconfirm --clean --windowed --onedir --contents-directory "." --name "English Speaking Game 3.0" --add-data "Sentences.txt:." --hidden-import pyaudio "EnglishSpeakingGame3.0.py"
```

The finished application will appear at:

```text
dist\English Speaking Game 3.0\English Speaking Game 3.0.exe
```

Keep and distribute the entire generated folder. The executable may not work correctly if it is separated from its supporting files.

For a test build with visible error messages, remove `--windowed` from the command.

## Troubleshooting

### Packages are installed, but the game cannot find them

The packages may have been installed for a different Python interpreter.

Check which interpreter is running:

```powershell
python -c "import sys; print(sys.executable)"
```

Test the microphone packages:

```powershell
python -c "import speech_recognition, pyaudio; print('Microphone packages are ready.')"
```

In VS Code, open **Python: Select Interpreter** from the Command Palette and select the same Python installation.

### The microphone is not detected

- Check that the microphone works in your system settings.
- Allow desktop applications to access the microphone.
- Close other programs that may be using it.
- Restart the game after connecting a new microphone.

### Speech recognition or pronunciation playback fails

These features require an internet connection. Make sure Python or the compiled application is allowed through your firewall.

## Privacy

Microphone audio is sent to Google's speech-recognition service for transcription. Sentence text is sent to Google Text-to-Speech when a pronunciation example is requested.

The game does not intentionally save microphone recordings. It only saves scores and progress statistics locally in `SavesData.txt`.

## Dependencies

This project uses:

- [SpeechRecognition](https://github.com/Uberi/speech_recognition) for speech transcription
- [gTTS](https://github.com/pndurette/gTTS) for pronunciation audio
- [pygame](https://www.pygame.org/) for audio playback
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) for microphone access
- [Tkinter](https://docs.python.org/3/library/tkinter.html) for the graphical interface

Each dependency remains covered by its own license.

## Contributing

Contributions, bug fixes, interface improvements, and new practice sentences are welcome.

New sentences should be:

- Natural and grammatically correct
- Useful in everyday conversation
- Properly punctuated
- Appropriate for a broad audience
- Free of duplicates

## License

This project is licensed under the [MIT License](LICENSE).

You may use, modify, and distribute the project as long as the original copyright and license notice are included.
