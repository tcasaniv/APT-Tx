import json
import os
import datetime

class HistoryManager:
    def __init__(self, history_file):
        self.history_file = history_file
        self.history = []
        self.load_history()

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")
                self.history = []
        else:
            self.history = []

    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_entry(self, source_a, source_b, preprocessed_a, preprocessed_b, apt_image, wav_audio, sdr_script, sdr_freq, sdr_samp_rate, metrics):
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_a": source_a,
            "source_b": source_b,
            "preprocessed_a": preprocessed_a,
            "preprocessed_b": preprocessed_b,
            "apt_image": apt_image,
            "wav_audio": wav_audio,
            "sdr_script": sdr_script,
            "sdr_freq": sdr_freq,
            "sdr_samp_rate": sdr_samp_rate,
            "metrics": metrics
        }
        self.history.append(entry)
        self.save_history()

    def delete_entry(self, index):
        if 0 <= index < len(self.history):
            self.history.pop(index)
            self.save_history()

    def clear_history(self):
        self.history = []
        self.save_history()

    def get_history(self):
        return self.history
