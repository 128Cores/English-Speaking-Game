# English Speaking Game with a Tkinter desktop interface.
# Audio features: py -m pip install SpeechRecognition gTTS pygame PyAudio

import json
import os
import random
import re
import tempfile
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import pygame
except ImportError:
    pygame = None


DEFAULT_SENTENCES = [
    "Hello, how are you today?",
    "The weather is beautiful outside.",
    "I love learning the English language.",
    "Practice makes perfect every day.",
    "Reading books helps improve vocabulary.",
]


class EnglishSpeakingGame:
    """Loads game content, stores progress, and handles text-to-speech audio."""

    def __init__(self):
        self.base_directory = os.path.dirname(os.path.abspath(__file__))
        self.save_path = os.path.join(self.base_directory, "SavesData.txt")
        self.sentences_path = os.path.join(self.base_directory, "Sentences.txt")
        self.data = {
            "SentencesCorrect": 0,
            "SentencesIncorrect": 0,
            "TotalScore": 0,
            "RoundsPlayed": 0,
            "GameVersion": "3.0",
            "LastPlayed": "",
            "BestScore": 0,
            "BestPercentage": 0.0,
        }
        self.sentences = []

        if pygame is not None:
            pygame.init()

        self.load_data()
        self.load_sentences()

    def load_data(self):
        """Load saved progress, while preserving defaults for missing fields."""
        try:
            with open(self.save_path, "r", encoding="utf-8") as file:
                loaded_data = json.load(file)
            if isinstance(loaded_data, dict):
                self.data.update(loaded_data)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

    def save_data(self):
        """Save the current progress beside the program file."""
        self.data["LastPlayed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.save_path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=2)
        except OSError as error:
            print(f"Could not save game data: {error}")

    def load_sentences(self):
        """Load non-empty lines from Sentences.txt, or create a starter file."""
        try:
            with open(self.sentences_path, "r", encoding="utf-8") as file:
                self.sentences = [line.strip() for line in file if line.strip()]
        except OSError:
            self.sentences = []

        if self.sentences:
            return

        self.sentences = DEFAULT_SENTENCES.copy()
        try:
            with open(self.sentences_path, "w", encoding="utf-8") as file:
                file.write("\n".join(self.sentences) + "\n")
        except OSError as error:
            print(f"Could not create Sentences.txt: {error}")

    def play_audio(self, text, filename):
        """Create and play speech audio, then remove its temporary file."""
        if gTTS is None or pygame is None:
            missing = []
            if gTTS is None:
                missing.append("gTTS")
            if pygame is None:
                missing.append("pygame")
            raise RuntimeError(
                "Install the audio packages first: " + ", ".join(missing)
            )

        try:
            gTTS(text=text, lang="en").save(filename)
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(20)
            pygame.mixer.music.stop()
        except Exception as error:
            raise RuntimeError(f"Audio error: {error}") from error
        finally:
            if pygame is not None and pygame.mixer.get_init():
                pygame.mixer.music.stop()
                if hasattr(pygame.mixer.music, "unload"):
                    pygame.mixer.music.unload()
                pygame.mixer.quit()
            try:
                os.remove(filename)
            except OSError:
                pass


class EnglishSpeakingGameUI:
    """Desktop interface layered on top of the original game logic."""

    COLORS = {
        "background": "#F3F6FB",
        "surface": "#FFFFFF",
        "navy": "#14243A",
        "navy_light": "#223A59",
        "blue": "#316BFF",
        "green": "#21A179",
        "red": "#E05263",
        "amber": "#E89A24",
        "cyan": "#3BC4E7",
        "text": "#172033",
        "muted": "#68758A",
        "border": "#DDE4EE",
        "soft_blue": "#EAF0FF",
    }

    def __init__(self, root, game):
        self.root = root
        self.game = game
        self.audio_lock = threading.Lock()
        self.nav_buttons = {}

        self.round_sentences = []
        self.round_index = 0
        self.round_active = False
        self.round_finished = False
        self.current_score = 0
        self.attempted = False
        self.busy = False
        self.last_heard = ""
        self.feedback = "Press Start listening when you are ready."
        self.feedback_color = self.COLORS["muted"]
        self.completed_result = None

        self.root.title("English Speaking Game 3.0")
        self.root.geometry("1080x720")
        self.root.minsize(900, 620)
        self.root.configure(bg=self.COLORS["background"])
        self._configure_styles()
        self._build_shell()
        self.show_home()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Game.Horizontal.TProgressbar",
            troughcolor=self.COLORS["border"],
            background=self.COLORS["blue"],
            bordercolor=self.COLORS["border"],
            thickness=10,
        )

    def _build_shell(self):
        header = tk.Frame(self.root, bg=self.COLORS["navy"], height=78)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.COLORS["navy"])
        brand.pack(side="left", padx=30, pady=15)
        tk.Label(
            brand,
            text="SPEAK",
            font=("Segoe UI", 15, "bold"),
            fg="white",
            bg=self.COLORS["blue"],
            padx=10,
            pady=4,
        ).pack(side="left", padx=(0, 10))
        tk.Label(
            brand,
            text="English Speaking Game",
            font=("Segoe UI", 17, "bold"),
            fg="white",
            bg=self.COLORS["navy"],
        ).pack(side="left")

        navigation = tk.Frame(header, bg=self.COLORS["navy"])
        navigation.pack(side="right", padx=22, pady=17)
        pages = [
            ("home", "Home", self.show_home),
            ("practice", "Practice", self.show_practice),
            ("sentences", "Sentences", self.show_sentences),
            ("stats", "Statistics", self.show_stats),
        ]
        for key, text, command in pages:
            button = tk.Button(
                navigation,
                text=text,
                command=command,
                font=("Segoe UI", 10, "bold"),
                fg="#C7D2E3",
                bg=self.COLORS["navy"],
                activeforeground="white",
                activebackground=self.COLORS["navy_light"],
                bd=0,
                cursor="hand2",
                padx=13,
                pady=10,
            )
            button.pack(side="left", padx=2)
            self.nav_buttons[key] = button

        self.content = tk.Frame(self.root, bg=self.COLORS["background"])
        self.content.pack(fill="both", expand=True)

    def _clear(self, active_page):
        for child in self.content.winfo_children():
            child.destroy()
        for key, button in self.nav_buttons.items():
            button.configure(
                bg=self.COLORS["navy_light"] if key == active_page else self.COLORS["navy"],
                fg="white" if key == active_page else "#C7D2E3",
            )

    def _page(self):
        page = tk.Frame(self.content, bg=self.COLORS["background"])
        page.pack(fill="both", expand=True, padx=38, pady=28)
        return page

    def _card(self, parent):
        return tk.Frame(
            parent,
            bg=self.COLORS["surface"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
        )

    def _primary_button(self, parent, text, command, width=17):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg=self.COLORS["blue"],
            activeforeground="white",
            activebackground="#2456D9",
            disabledforeground="#DDE5F5",
            bd=0,
            cursor="hand2",
            padx=16,
            pady=11,
            width=width,
        )

    def _secondary_button(self, parent, text, command, width=15):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            fg=self.COLORS["text"],
            bg=self.COLORS["surface"],
            activeforeground=self.COLORS["blue"],
            activebackground=self.COLORS["soft_blue"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
            bd=0,
            cursor="hand2",
            padx=14,
            pady=10,
            width=width,
        )

    def _title(self, parent, title, subtitle):
        tk.Label(
            parent,
            text=title,
            font=("Segoe UI", 25, "bold"),
            fg=self.COLORS["text"],
            bg=self.COLORS["background"],
        ).pack(anchor="w")
        tk.Label(
            parent,
            text=subtitle,
            font=("Segoe UI", 11),
            fg=self.COLORS["muted"],
            bg=self.COLORS["background"],
        ).pack(anchor="w", pady=(4, 20))

    def show_home(self):
        self._clear("home")
        page = self._page()

        hero = tk.Frame(page, bg=self.COLORS["navy"])
        hero.pack(fill="x")
        hero_text = tk.Frame(hero, bg=self.COLORS["navy"])
        hero_text.pack(side="left", fill="both", expand=True, padx=36, pady=31)
        tk.Label(
            hero_text,
            text="Speak clearly. Build confidence.",
            font=("Segoe UI", 26, "bold"),
            fg="white",
            bg=self.COLORS["navy"],
        ).pack(anchor="w")
        tk.Label(
            hero_text,
            text="Practice English one sentence at a time and get immediate speech-recognition feedback.",
            font=("Segoe UI", 11),
            fg="#C7D2E3",
            bg=self.COLORS["navy"],
            wraplength=580,
            justify="left",
        ).pack(anchor="w", pady=(10, 20))
        self._primary_button(hero_text, "Start practicing", self.show_practice).pack(anchor="w")
        tk.Label(
            hero,
            text="Aa",
            font=("Georgia", 70, "bold"),
            fg=self.COLORS["cyan"],
            bg=self.COLORS["navy"],
        ).pack(side="right", padx=58)

        stats_frame = tk.Frame(page, bg=self.COLORS["background"])
        stats_frame.pack(fill="both", expand=True, pady=(22, 0))
        for column in range(4):
            stats_frame.columnconfigure(column, weight=1, uniform="home")

        items = [
            ("Rounds", self.game.data["RoundsPlayed"], self.COLORS["blue"]),
            ("Total score", self.game.data["TotalScore"], self.COLORS["green"]),
            ("Accuracy", f"{self._accuracy():.1f}%", self.COLORS["amber"]),
            ("Sentences", len(self.game.sentences), self.COLORS["cyan"]),
        ]
        for column, (label, value, accent) in enumerate(items):
            tile = self._card(stats_frame)
            tile.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 6, 0 if column == 3 else 6),
            )
            tk.Frame(tile, bg=accent, height=5).pack(fill="x")
            tk.Label(
                tile,
                text=str(value),
                font=("Segoe UI", 23, "bold"),
                fg=self.COLORS["text"],
                bg=self.COLORS["surface"],
            ).pack(pady=(18, 2))
            tk.Label(
                tile,
                text=label,
                font=("Segoe UI", 10),
                fg=self.COLORS["muted"],
                bg=self.COLORS["surface"],
            ).pack(pady=(0, 18))

        tk.Label(
            page,
            text="Version 3.0 Created by Dechachot Sangtopo",
            font=("Segoe UI", 9),
            fg=self.COLORS["muted"],
            bg=self.COLORS["background"],
        ).pack(side="bottom", pady=(18, 0))

    def show_practice(self):
        self._clear("practice")
        if self.round_active:
            self._show_active_round()
        elif self.round_finished and self.completed_result:
            self._show_results()
        else:
            self._show_setup()

    def _show_setup(self):
        page = self._page()
        self._title(page, "Practice", "Choose a round length, then read each sentence aloud.")
        card = self._card(page)
        card.pack(fill="x")
        inner = tk.Frame(card, bg=self.COLORS["surface"])
        inner.pack(fill="x", padx=32, pady=30)
        maximum = max(1, min(50, len(self.game.sentences)))
        tk.Label(
            inner,
            text="How many sentences would you like to practice?",
            font=("Segoe UI", 15, "bold"),
            fg=self.COLORS["text"],
            bg=self.COLORS["surface"],
        ).pack(anchor="w")
        tk.Label(
            inner,
            text=f"Choose between 1 and {maximum} sentences.",
            font=("Segoe UI", 10),
            fg=self.COLORS["muted"],
            bg=self.COLORS["surface"],
        ).pack(anchor="w", pady=(5, 18))
        controls = tk.Frame(inner, bg=self.COLORS["surface"])
        controls.pack(anchor="w")
        self.round_count = tk.IntVar(value=min(5, maximum))
        spinner = tk.Spinbox(
            controls,
            from_=1,
            to=maximum,
            textvariable=self.round_count,
            width=6,
            justify="center",
            font=("Segoe UI", 14, "bold"),
            fg=self.COLORS["text"],
            bg="#F8FAFD",
            relief="solid",
            bd=1,
        )
        spinner.pack(side="left", padx=(0, 14), ipady=6)
        self._primary_button(controls, "Begin round", self.begin_round, 14).pack(side="left")

        tip = tk.Frame(page, bg=self.COLORS["soft_blue"])
        tip.pack(fill="x", pady=(20, 0))
        tk.Label(
            tip,
            text="Use a quiet room, allow microphone access, and speak at a natural pace. You can hear each sentence before recording.",
            font=("Segoe UI", 10),
            fg=self.COLORS["text"],
            bg=self.COLORS["soft_blue"],
            wraplength=800,
            justify="left",
        ).pack(anchor="w", padx=22, pady=18)

    def begin_round(self):
        try:
            count = int(self.round_count.get())
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid amount", "Please enter a valid number.")
            return
        maximum = min(50, len(self.game.sentences))
        if not 1 <= count <= maximum:
            messagebox.showerror("Invalid amount", f"Choose a number from 1 to {maximum}.")
            return
        self.round_sentences = random.sample(self.game.sentences, count)
        self.round_index = 0
        self.current_score = 0
        self.round_active = True
        self.round_finished = False
        self.attempted = False
        self.last_heard = ""
        self.feedback = "Press Start listening when you are ready."
        self.feedback_color = self.COLORS["muted"]
        self.completed_result = None
        self.show_practice()

    def _show_active_round(self):
        page = self._page()
        total = len(self.round_sentences)
        number = self.round_index + 1
        top = tk.Frame(page, bg=self.COLORS["background"])
        top.pack(fill="x")
        tk.Label(
            top,
            text=f"Sentence {number} of {total}",
            font=("Segoe UI", 18, "bold"),
            fg=self.COLORS["text"],
            bg=self.COLORS["background"],
        ).pack(side="left")
        self.score_label = tk.Label(
            top,
            text=f"Score  {self.current_score}/{self.round_index}",
            font=("Segoe UI", 11, "bold"),
            fg=self.COLORS["blue"],
            bg=self.COLORS["soft_blue"],
            padx=12,
            pady=7,
        )
        self.score_label.pack(side="right")
        self.round_progress = ttk.Progressbar(
            page,
            style="Game.Horizontal.TProgressbar",
            maximum=total,
            value=self.round_index,
        )
        self.round_progress.pack(fill="x", pady=(13, 22))

        card = self._card(page)
        card.pack(fill="both", expand=True)
        tk.Label(
            card,
            text="READ THIS SENTENCE",
            font=("Segoe UI", 9, "bold"),
            fg=self.COLORS["blue"],
            bg=self.COLORS["surface"],
        ).pack(pady=(30, 13))
        tk.Label(
            card,
            text=self.round_sentences[self.round_index],
            font=("Georgia", 23, "bold"),
            fg=self.COLORS["text"],
            bg=self.COLORS["surface"],
            wraplength=780,
            justify="center",
        ).pack(padx=40, pady=(0, 24))
        self.status_label = tk.Label(
            card,
            text=self.feedback,
            font=("Segoe UI", 11, "bold"),
            fg=self.feedback_color,
            bg=self.COLORS["surface"],
            wraplength=760,
        )
        self.status_label.pack(pady=(0, 7))
        self.heard_label = tk.Label(
            card,
            text=f'We heard: “{self.last_heard}”' if self.last_heard else "",
            font=("Segoe UI", 10),
            fg=self.COLORS["muted"],
            bg=self.COLORS["surface"],
        )
        self.heard_label.pack(pady=(0, 17))
        actions = tk.Frame(card, bg=self.COLORS["surface"])
        actions.pack(pady=(0, 28))
        self.hear_button = self._secondary_button(actions, "Hear sentence", self.hear_sentence)
        self.hear_button.pack(side="left", padx=6)
        self.listen_button = self._primary_button(actions, "Start listening", self.listen, 16)
        self.listen_button.pack(side="left", padx=6)
        next_text = "Finish round" if number == total else "Next sentence"
        self.next_button = self._secondary_button(actions, next_text, self.next_sentence)
        self.next_button.pack(side="left", padx=6)
        self._sync_buttons()
        tk.Button(
            page,
            text="Quit this round",
            command=self.quit_round,
            font=("Segoe UI", 9, "underline"),
            fg=self.COLORS["muted"],
            bg=self.COLORS["background"],
            activeforeground=self.COLORS["red"],
            activebackground=self.COLORS["background"],
            bd=0,
            cursor="hand2",
        ).pack(pady=(12, 0))

    def _sync_buttons(self):
        if not hasattr(self, "listen_button") or not self._widget_exists(self.listen_button):
            return
        self.hear_button.configure(state="disabled" if self.busy else "normal")
        self.listen_button.configure(
            state="disabled" if self.busy or self.attempted else "normal"
        )
        self.next_button.configure(
            state="disabled" if self.busy or not self.attempted else "normal"
        )

    def _set_status(self, text, color=None):
        self.feedback = text
        if color:
            self.feedback_color = color
        if hasattr(self, "status_label") and self._widget_exists(self.status_label):
            self.status_label.configure(text=text, fg=self.feedback_color)

    @staticmethod
    def _widget_exists(widget):
        try:
            return bool(widget.winfo_exists())
        except tk.TclError:
            return False

    def hear_sentence(self):
        if self.busy:
            return
        self.busy = True
        self._sync_buttons()
        self._set_status("Preparing the pronunciation example…", self.COLORS["amber"])
        sentence = self.round_sentences[self.round_index]
        threading.Thread(target=self._audio_worker, args=(sentence,), daemon=True).start()

    def _audio_worker(self, text):
        try:
            self._speak(text)
        except Exception as error:
            message = f"Could not play audio: {error}"
            self.root.after(
                0,
                lambda message=message: self._audio_finished(message, self.COLORS["red"]),
            )
        else:
            self.root.after(0, lambda: self._audio_finished("Example finished. You can record now.", self.COLORS["muted"]))

    def _audio_finished(self, message, color):
        self.busy = False
        self._set_status(message, color)
        self._sync_buttons()

    def _speak(self, text):
        descriptor, filename = tempfile.mkstemp(suffix=".mp3")
        os.close(descriptor)
        try:
            with self.audio_lock:
                self.game.play_audio(text, filename)
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    def listen(self):
        if self.busy or self.attempted:
            return
        if sr is None:
            messagebox.showerror(
                "Speech recognition unavailable",
                "Install the microphone packages first:\n\n"
                "pip install SpeechRecognition PyAudio",
            )
            return
        self.busy = True
        self._sync_buttons()
        self._set_status("Calibrating your microphone…", self.COLORS["amber"])
        expected = self.round_sentences[self.round_index]
        expected_index = self.round_index
        threading.Thread(
            target=self._recognition_worker,
            args=(expected, expected_index),
            daemon=True,
        ).start()

    def _recognition_worker(self, expected, expected_index):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1.5)
                self.root.after(0, lambda: self._set_status("Listening… speak now.", self.COLORS["blue"]))
                audio = recognizer.listen(source, timeout=15, phrase_time_limit=15)
            self.root.after(0, lambda: self._set_status("Checking your pronunciation…", self.COLORS["amber"]))
            recognized = recognizer.recognize_google(audio)
            correct = self._matches(expected, recognized)
            self.root.after(
                0,
                lambda: self._handle_result(expected_index, expected, recognized, correct),
            )
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self._recognition_error("I did not hear anything. Try again."))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self._handle_result(expected_index, expected, "Not recognized", False))
        except sr.RequestError as error:
            message = f"Speech service error: {error}"
            self.root.after(0, lambda message=message: self._recognition_error(message))
        except Exception as error:
            message = f"Microphone error: {error}"
            self.root.after(0, lambda message=message: self._recognition_error(message))

    @staticmethod
    def _matches(expected, recognized):
        clean = lambda text: re.sub(r"[^a-z0-9]", "", text.casefold())
        expected_text = clean(expected)
        recognized_text = clean(recognized)
        return bool(recognized_text) and (
            expected_text in recognized_text or recognized_text in expected_text
        )

    def _handle_result(self, expected_index, expected, recognized, correct):
        if not self.round_active or expected_index != self.round_index or self.attempted:
            self.busy = False
            return
        self.busy = False
        self.attempted = True
        self.last_heard = recognized
        if hasattr(self, "heard_label") and self._widget_exists(self.heard_label):
            self.heard_label.configure(text=f'We heard: “{recognized}”')
        if correct:
            self.current_score += 1
            self.game.data["TotalScore"] += 1
            self.game.data["SentencesCorrect"] += 1
            self._set_status("Correct! Your pronunciation matched.", self.COLORS["green"])
            feedback = "Excellent! You pronounced it correctly."
            correction = None
        else:
            self.game.data["SentencesIncorrect"] += 1
            self._set_status("Not quite. Listen carefully and keep practicing.", self.COLORS["red"])
            feedback = "Let me show you the correct pronunciation."
            correction = expected
        if hasattr(self, "score_label") and self._widget_exists(self.score_label):
            self.score_label.configure(
                text=f"Score  {self.current_score}/{self.round_index + 1}"
            )
        if hasattr(self, "round_progress") and self._widget_exists(self.round_progress):
            self.round_progress.configure(value=self.round_index + 1)
        self.game.save_data()
        self._sync_buttons()
        threading.Thread(
            target=self._feedback_worker,
            args=(feedback, correction),
            daemon=True,
        ).start()

    def _feedback_worker(self, feedback, correction):
        try:
            self._speak(feedback)
            if correction:
                time.sleep(0.4)
                self._speak(correction)
        except Exception:
            pass

    def _recognition_error(self, message):
        self.busy = False
        self._set_status(message, self.COLORS["red"])
        self._sync_buttons()

    def next_sentence(self):
        if self.busy or not self.attempted:
            return
        if self.round_index + 1 >= len(self.round_sentences):
            self.finish_round()
            return
        self.round_index += 1
        self.attempted = False
        self.last_heard = ""
        self.feedback = "Press Start listening when you are ready."
        self.feedback_color = self.COLORS["muted"]
        self.show_practice()

    def finish_round(self):
        total = len(self.round_sentences)
        percentage = self.current_score / total * 100
        self.game.data["RoundsPlayed"] += 1
        self.game.data["BestScore"] = max(self.game.data["BestScore"], self.current_score)
        self.game.data["BestPercentage"] = max(self.game.data["BestPercentage"], percentage)
        self.game.save_data()
        self.completed_result = (self.current_score, total, percentage)
        self.round_active = False
        self.round_finished = True
        self.show_practice()

    def _show_results(self):
        page = self._page()
        score, total, percentage = self.completed_result
        card = self._card(page)
        card.pack(fill="both", expand=True)
        tk.Label(
            card,
            text="ROUND COMPLETE",
            font=("Segoe UI", 10, "bold"),
            fg=self.COLORS["blue"],
            bg=self.COLORS["surface"],
        ).pack(pady=(48, 8))
        tk.Label(
            card,
            text=f"{score}/{total}",
            font=("Segoe UI", 48, "bold"),
            fg=self.COLORS["text"],
            bg=self.COLORS["surface"],
        ).pack()
        tk.Label(
            card,
            text=f"{percentage:.1f}% accuracy",
            font=("Segoe UI", 15, "bold"),
            fg=self.COLORS["green"] if percentage >= 75 else self.COLORS["amber"],
            bg=self.COLORS["surface"],
        ).pack(pady=(0, 14))
        if percentage >= 90:
            result_message = "Outstanding pronunciation!"
        elif percentage >= 75:
            result_message = "Great job. Keep practicing!"
        elif percentage >= 50:
            result_message = "Good effort. You are making progress."
        else:
            result_message = "Keep practicing. Every round helps."
        tk.Label(
            card,
            text=result_message,
            font=("Segoe UI", 12),
            fg=self.COLORS["muted"],
            bg=self.COLORS["surface"],
        ).pack(pady=(0, 26))
        actions = tk.Frame(card, bg=self.COLORS["surface"])
        actions.pack()
        self._primary_button(actions, "Practice again", self.new_round, 15).pack(side="left", padx=6)
        self._secondary_button(actions, "View statistics", self.show_stats, 15).pack(side="left", padx=6)

    def new_round(self):
        self.round_finished = False
        self.completed_result = None
        self.show_practice()

    def quit_round(self):
        if not messagebox.askyesno("Quit round", "Quit this round? The partial score will not count as a round."):
            return
        self.round_active = False
        self.round_finished = False
        self.busy = False
        self.round_sentences = []
        self.show_home()

    def show_sentences(self):
        self._clear("sentences")
        page = self._page()
        self._title(page, "Sentence library", "Review the practice prompts or add one of your own.")
        card = self._card(page)
        card.pack(fill="both", expand=True)
        list_area = tk.Frame(card, bg=self.COLORS["surface"])
        list_area.pack(fill="both", expand=True, padx=24, pady=(22, 12))
        scrollbar = tk.Scrollbar(list_area)
        scrollbar.pack(side="right", fill="y")
        self.sentence_list = tk.Listbox(
            list_area,
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 11),
            fg=self.COLORS["text"],
            bg="#FAFBFD",
            selectforeground="white",
            selectbackground=self.COLORS["blue"],
            relief="flat",
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
            activestyle="none",
        )
        self.sentence_list.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.sentence_list.yview)
        self._refresh_sentences()
        add_area = tk.Frame(card, bg=self.COLORS["surface"])
        add_area.pack(fill="x", padx=24, pady=(0, 22))
        self.new_sentence = tk.StringVar()
        entry = tk.Entry(
            add_area,
            textvariable=self.new_sentence,
            font=("Segoe UI", 11),
            fg=self.COLORS["text"],
            bg="#FAFBFD",
            relief="solid",
            bd=1,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
        entry.bind("<Return>", lambda event: self.add_sentence())
        self._primary_button(add_area, "Add sentence", self.add_sentence, 14).pack(side="right")
        self.sentence_status = tk.Label(
            page,
            text=f"{len(self.game.sentences)} sentences available",
            font=("Segoe UI", 9),
            fg=self.COLORS["muted"],
            bg=self.COLORS["background"],
        )
        self.sentence_status.pack(anchor="w", pady=(8, 0))

    def _refresh_sentences(self):
        self.sentence_list.delete(0, tk.END)
        for number, sentence in enumerate(self.game.sentences, 1):
            self.sentence_list.insert(tk.END, f"  {number}.  {sentence}")

    def add_sentence(self):
        sentence = " ".join(self.new_sentence.get().strip().split())
        if not sentence:
            self.sentence_status.configure(text="Please enter a sentence first.", fg=self.COLORS["red"])
            return
        if sentence.casefold() in {item.casefold() for item in self.game.sentences}:
            self.sentence_status.configure(text="That sentence already exists.", fg=self.COLORS["red"])
            return
        try:
            self.game.sentences.append(sentence)
            with open(self.game.sentences_path, "a", encoding="utf-8") as file:
                file.write(f"\n{sentence}")
        except OSError as error:
            self.game.sentences.pop()
            self.sentence_status.configure(text=f"Could not save: {error}", fg=self.COLORS["red"])
            return
        self.new_sentence.set("")
        self._refresh_sentences()
        self.sentence_status.configure(text="Sentence added successfully.", fg=self.COLORS["green"])

    def show_stats(self):
        self._clear("stats")
        page = self._page()
        self._title(page, "Your statistics", "Track progress across all completed practice rounds.")
        grid = tk.Frame(page, bg=self.COLORS["background"])
        grid.pack(fill="x")
        for column in range(3):
            grid.columnconfigure(column, weight=1, uniform="statistics")
        items = [
            ("Rounds played", self.game.data["RoundsPlayed"], self.COLORS["blue"]),
            ("Correct", self.game.data["SentencesCorrect"], self.COLORS["green"]),
            ("Incorrect", self.game.data["SentencesIncorrect"], self.COLORS["red"]),
            ("Overall accuracy", f"{self._accuracy():.1f}%", self.COLORS["cyan"]),
            ("Best score", self.game.data["BestScore"], self.COLORS["amber"]),
            ("Best accuracy", f"{self.game.data['BestPercentage']:.1f}%", self.COLORS["blue"]),
        ]
        for index, (label, value, color) in enumerate(items):
            row, column = divmod(index, 3)
            tile = self._card(grid)
            tile.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 6, 0 if column == 2 else 6),
                pady=(0 if row == 0 else 6, 6),
            )
            tk.Label(
                tile,
                text=str(value),
                font=("Segoe UI", 22, "bold"),
                fg=color,
                bg=self.COLORS["surface"],
            ).pack(pady=(17, 2))
            tk.Label(
                tile,
                text=label,
                font=("Segoe UI", 10),
                fg=self.COLORS["muted"],
                bg=self.COLORS["surface"],
            ).pack(pady=(0, 17))
        footer = tk.Frame(page, bg=self.COLORS["background"])
        footer.pack(fill="x", pady=(14, 0))
        tk.Label(
            footer,
            text=f"Last saved: {self.game.data.get('LastPlayed') or 'Never'}",
            font=("Segoe UI", 9),
            fg=self.COLORS["muted"],
            bg=self.COLORS["background"],
        ).pack(side="left")
        tk.Button(
            footer,
            text="Reset progress",
            command=self.reset_progress,
            font=("Segoe UI", 9, "bold"),
            fg=self.COLORS["red"],
            bg=self.COLORS["background"],
            activeforeground="#B83648",
            activebackground=self.COLORS["background"],
            bd=0,
            cursor="hand2",
        ).pack(side="right")

    def _accuracy(self):
        total = self.game.data["SentencesCorrect"] + self.game.data["SentencesIncorrect"]
        if total == 0:
            return 0.0
        return self.game.data["SentencesCorrect"] / total * 100

    def reset_progress(self):
        if not messagebox.askyesno("Reset progress", "Erase all score and round statistics?"):
            return
        version = self.game.data["GameVersion"]
        self.game.data.update({
            "SentencesCorrect": 0,
            "SentencesIncorrect": 0,
            "TotalScore": 0,
            "RoundsPlayed": 0,
            "GameVersion": version,
            "LastPlayed": "",
            "BestScore": 0,
            "BestPercentage": 0.0,
        })
        self.game.save_data()
        self.show_stats()

    def close(self):
        self.game.save_data()
        if pygame is not None:
            pygame.quit()
        self.root.destroy()


# Run the graphical version of the game.
if __name__ == "__main__":
    root = tk.Tk()
    game = EnglishSpeakingGame()
    EnglishSpeakingGameUI(root, game)
    root.mainloop()
