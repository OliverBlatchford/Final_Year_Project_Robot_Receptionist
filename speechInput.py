import whisper
import sounddevice as sd
import scipy.io.wavfile as wav

#whisper model from OpenAI. Medium chose cause it understands enough while loading quickly enough. Decided through trial and error.
model = whisper.load_model('medium')
AUDIO_FILE = 'recording.wav'
SAMPLE_RATE = 16000
DURATION = 5

#records audio for a fixed duration then saves it
def record_until_silence():
    print("Listening... speak now!")
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16',
        device=1
    )
    sd.wait()
    wav.write(AUDIO_FILE, SAMPLE_RATE, audio)
    print("Recording saved.")
    return True

#common hallucinations to ignore
WHISPER_HALLUCINATIONS = {
    "thank you", "thanks", "thanks for watching", "thanks for listening",
    "you", "bye", "bye bye", "bye.", "thank you.", "thanks.", "."
}
#transcirbes whats said
def transcribe():
    print('Transcribing...')
    result = model.transcribe(AUDIO_FILE, language="en", initial_prompt="University reception. Room numbers like MB705, MB225, NW, SW. Library, student union, IT support, student services, zen zone, check in.")
    text = result['text'].strip()

    #if mostly silence discard it
    segments = result.get('segments', [])
    if segments and all(s.get('no_speech_prob', 0) > 0.6 for s in segments):
        print("Silence detected, discarding transcript.")
        return ""

    #discard known whisper hallucinations
    if text.lower().rstrip('.').strip() in WHISPER_HALLUCINATIONS:
        print("Hallucination detected ({}), discarding.".format(text))
        return ""

    return text

if __name__ == '__main__':
    record_until_silence()
    text = transcribe()
    print(f'You said: {text}')