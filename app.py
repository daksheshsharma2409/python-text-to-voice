import os
import uuid
from flask import Flask, render_template, request, send_file
from TTS.api import TTS
from pydub import AudioSegment

app = Flask(__name__)
tts = TTS(model_name="tts_models/en/vctk/vits")

# Map speaker IDs to human-friendly labels
speaker_labels = {
    "p225": "English Female (US)",
    "p226": "English Male (US)",
    "p227": "English Female",
    "p228": "English Male",
    "p229": "Indian Male (Neutral)",
    "p230": "Indian Female",
    "p231": "British Male",
    "p232": "British Female",
    "p233": "American Male",
    "p234": "American Female",
}

# Reverse map for lookup
label_to_id = {v: k for k, v in speaker_labels.items()}

@app.route("/", methods=["GET", "POST"])
def index():
    audio_file = None

    # Define default values (used in GET and fallback for POST)
    previous_values = {
        "text": "",
        "speaker": list(speaker_labels.values())[0],
        "speed": "1.0",
        "pitch": "0"
    }

    if request.method == "POST":
        text = request.form["text"]
        speaker_label = request.form["speaker"]
        speed = request.form.get("speed", "1.0")
        pitch = request.form.get("pitch", "0")

        previous_values = {
            "text": text,
            "speaker": speaker_label,
            "speed": speed,
            "pitch": pitch
        }

        speaker_id = label_to_id.get(speaker_label, "p233")

        raw_filename = f"{uuid.uuid4().hex}_raw.wav"
        final_filename = f"{uuid.uuid4().hex}_final.wav"

        raw_path = os.path.join("outputs", raw_filename)
        final_path = os.path.join("outputs", final_filename)

        os.makedirs("outputs", exist_ok=True)

        # Generate TTS audio
        tts.tts_to_file(text=text, speaker=speaker_id, file_path=raw_path)

        # Load raw audio
        sound = AudioSegment.from_wav(raw_path)

        # Apply speed
        sound = sound._spawn(sound.raw_data, overrides={
            "frame_rate": int(sound.frame_rate * float(speed))
        }).set_frame_rate(22050)

        # Apply pitch
        octaves = int(pitch) / 12.0
        new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
        sound = sound._spawn(sound.raw_data, overrides={"frame_rate": new_sample_rate})
        sound = sound.set_frame_rate(22050)

        # Export final audio
        sound.export(final_path, format="wav")
        audio_file = os.path.basename(final_path)

    return render_template(
        "index.html",
        speakers=list(speaker_labels.values()),
        audio_file=audio_file,
        values=previous_values
    )

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join("outputs", filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
