import ffmpeg
import whisper
def transcribe_speech(audio):
    model = whisper.load_model("base")
    result = model.transcribe(audio)
    labels = []
    for segment_info in result['segments']:
        start = int(float(segment_info['start']) * 1000)
        end = int(float(segment_info['end']) * 1000)
        content = segment_info['text']
        labels.append(dict( \
            [('start', start), \
             ('end', end),
             ("text", content)]))
    return labels