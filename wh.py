import whisper

model = whisper.load_model("base")

def transcribe_speech(audio):
    result = model.transcribe(audio)
    labels = []
    for segment_info in result:
        start = int(float(result['start']) * 1000)
        end = int(float(result['end']) * 1000)
        content = result['text']
        labels.append(dict( \
            [('start', start), \
             ('end', end),
             ("token", content)]))
    print(result)
    print(labels)
    return labels