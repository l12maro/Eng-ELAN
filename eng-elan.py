import os
import re, sys
from pathlib import Path
import aws, gcs, wh
import xml.etree.ElementTree as ET
import tempfile
from pydub import AudioSegment

# A helper function of create-transcriptions for utterance-level extraction
def utterance_level(output, transcriptions, threshold):
    threshold = (int(float(threshold)))
    # divide utterances based on the space between words
    # except if fragments were already specified in a tier
    i = 0
    utterance = ""
    start_utterance = 0
    for t in transcriptions:
        i += 1
        end = t['end']
        utterance += t['token']
        # compare the lengths of the end of the first word and the beginning of the next,
        # as long as there is a next word
        if i < len(transcriptions):
            next_start = transcriptions[i]['start']
        else:
            output.write(f'<span start="{start_utterance}" end="{end}"><v>{utterance}</v></span>\n')
        if next_start > end + threshold:
            output.write(f'<span start="{start_utterance}" end="{end}"><v>{utterance}</v></span>\n')
            start_utterance = next_start
            utterance = ""
        else:
            utterance += " "


def create_tier(output, transcriptions, level, threshold, tier, service):
    # Open 'output_segments' for writing, and return the new speech
    # segments transcriptions as the contents of <span> elements (see
    # below).
    with open(output, 'w', encoding='utf-8') as output_segs:
        # Write document header.
        output_segs.write('<?xml version="1.0" encoding="UTF-8"?>\n')

        # Write out the adjusted annotations
        output_segs.write(
            '<TIERS xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="file:avatech-tiers.xsd">\n')

        if level == 'Utterance' or level == 'Both':
            output_segs.write(
                '<TIER columns="English-utterances">\n')
            if tier != "":
                # when a tier is already specified, we consider it to be the utterance level.
                for t in transcriptions:
                    utterance = ""
                    start = t['start']
                    end = t['end']
                    if service == "Whisper":
                        print(transcriptions)
                        print(t)
                        utterance = t['transcription'][0]['text']
                    else:
                        i = 0
                        for token in t['transcription']:
                            print(token)
                            utterance += token['token']
                            if i < len(t['transcription']):
                                utterance += " "
                            i += 1
                    output_segs.write(f'<span start="{start}" end="{end}"><v>{utterance}</v></span>\n')
            elif service == 'Whisper':
                for t in transcriptions:
                    output_segs.write(f'<span start="{t["start"]}" '
                                  f'end="{t["end"]}"><v>{t["text"]}</v></span>\n')
            else:
                utterance_level(output_segs, transcriptions, threshold)
            output_segs.write('</TIER>\n')


        if level == 'Word' or level == 'Both':
            # Whisper does not return timestamps at the word-level
            if service != 'Whisper':
                output_segs.write('<TIER columns="English-words">\n')
                if tier == "":
                    for t in transcriptions:
                        start = t['start']
                        end = t['end']
                        token = t['token']
                        output_segs.write(f'<span start="{start}" end="{end}"><v>{token}</v></span>\n')
                else:
                    startw = 0
                    endw = 0
                    for t in transcriptions:
                        start = t['start']
                        end = t['end']
                        i = 0
                        for token in t['transcription']:
                            #add words in their respective timelines respecting the preannotated tiers
                            if i == 0:
                                startw = start
                            else:
                                startw = start + token['start']
                            if i < len(t['transcription']):
                                endw = end
                            else:
                                endw = start + token['end']
                            w = token['token']
                            output_segs.write(f'<span start="{startw}" '
                                              f'end="{endw}"><v>{w}</v></span>\n')
                            i += 1
                output_segs.write('</TIER>\n')
        output_segs.write('</TIERS>\n')


def transcribe(service, source, bucket, project, filename, ou_path):
    if service == 'AWS':
        aws.upload_file(source, bucket, filename)
        uri_path = "s3://" + bucket + "/" + filename
        # transcription now returns the information we need
        return aws.transcribe_file(filename, uri_path, bucket, ou_path)

    elif service == 'GCloud':
        # upload wav file to the chosen service
        gcs.upload_file(bucket, source, filename, project)
        uri_path = "gs://" + bucket + "/" + filename
        # transcription now returns the information we need
        return gcs.transcribe_speech(uri_path)

    else:
        return wh.transcribe_speech(source)


# Split the audio given in smaller chunks
def split_audio(audio, tier, output):
    tree = ET.parse(tier)
    root = tree.getroot()
    timestamps = []
    audio = AudioSegment.from_wav(audio)
    i = 1

    # get transcription timestamps for all split
    for times in root.iter("span"):
        # only split empty tiers
        for t in times:
            if t.text == None:
                # extract times of span
                start_span = times.attrib['start']
                start_span = int(float(start_span) * 1000)
                end_span = times.attrib['end']
                end_span = int(float(end_span) * 1000)
                timestamps.append({"start": start_span, "end": end_span})

    # split audio segments and save in output directory
    for a in timestamps:
        newAudio = audio[a["start"]:a["end"]]
        path = output + str(i) + ".wav"
        newAudio.export(path, format="wav")
        a["path"] = path
        i += 1
    return timestamps


def main():
    # Read in all of the parameters that ELAN passes to this local recognizer on
    # standard input.
    params = {}
    for line in sys.stdin:
        match = re.search(r'<param name="(.*?)".*?>(.*?)</param>', line)
        if match:
            params[match.group(1)] = match.group(2).strip()
            print(params)

    # upload wav file to the chosen service
    filename = params["filename"] + ".wav"
    if params['tier'] != "":
        # get the split audios and timestamps
        audios = split_audio(params["source"], params['tier'], params['output_path'])
        i = 1
        for a in audios:
            # filenames must be unique for service
            jobname = params["filename"] + str(i)
            # create transcriptions for each audio and add to audio info
            a['transcription'] = transcribe(params['transcription_service'], a['path'], params["bucket"],
                                             params["project"], jobname, params["output_path"])
            i += 1
            #remove the audios once the transcriptions are done
            os.remove(a['path'])
        # now we add them to the eaf file within the chosen tier
        create_tier(params['output_segments'], audios,
                    params['level'], params['threshold'], params['tier'], params['transcription_service'])

    else:
        transcriptions = transcribe(params['transcription_service'], params["source"], params["bucket"],
                                   params["project"], filename, params["output_path"])

        # now we add them to the eaf file within the chosen tier
        create_tier(params['output_segments'], transcriptions,
                    params['level'], params['threshold'], params['tier'], params['transcription_service'])

    # Finally, tell ELAN that we're done.
    print('RESULT: DONE.', flush=True)


if __name__ == "__main__":
    main()
