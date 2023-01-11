import re, sys
from pathlib import Path
import aws, gcs
import xml.etree.ElementTree as ET

def add_transcriptions(output, tier, transcription):
    output.write(
        '<TIER columns="English-utterances">\n')
    tree = ET.parse(tier)
    root = tree.getroot()
    # match transcription timestamps with previously annotated spans
    for times in root.iter("span"):
        #extract times of span
        start = times.attrib['start']
        start_span = int(float(start) * 1000)
        end = times.attrib['end']
        end_span = int(float(end) * 1000)
        output.write(f'<span start="{start}" end="{end}">')
        #only add transcriptions to empty spans
        for t in times:
            if t.text != None:
                output.write(str(ET.tostring(t))[2:-1])
            else:
                output.write("<v>")
                #get transcription timestamps
                i = 0
                for e in transcription:
                    start = e['start']
                    end = e['end']
                    #include in annotations all timestamps that correspond approximately
                    if start_span < end and end <= end_span:
                        if i > 0:
                            output.write(" " + e['token'])
                        else:
                            output.write(e['token'])
                        i += 1
                output.write('</v>')
        output.write('</span>\n')
    output.write('</TIER>\n')

#A helper function of create-transcriptions for utterance-level extraction
def utterance_level(output, transcriptions, threshold):
    threshold = (int(float(threshold)))
    output.write(
        '<TIER columns="English-utterances">\n')
    # divide utterances based on the space between words
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
    output.write('</TIER>\n')

def create_transcriptions(output, transcriptions, level, threshold, tier):
    # Then open 'output_segments' for writing, and return all of the new speech
    # segments transcriptions as the contents of <span> elements (see
    # below).
    with open(output, 'w', encoding='utf-8') as output_segs:
        # Write document header.
        output_segs.write('<?xml version="1.0" encoding="UTF-8"?>\n')

        # Write out the adjusted annotations
        output_segs.write(
            '<TIERS xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="file:avatech-tiers.xsd">\n')

        if level == 'Utterance' or level == 'Both':
            if tier == "":
                utterance_level(output_segs, transcriptions, threshold)
            else:
                add_transcriptions(output_segs, tier, transcriptions)

        if level == 'Word' or level == 'Both':
            output_segs.write('<TIER columns="English-words">\n')
            for t in transcriptions:
                start = t['start']
                end = t['end']
                token = t['token']
                output_segs.write(f'<span start="{start}" end="{end}"><v>{token}</v></span>\n')

            output_segs.write('</TIER>\n')
        output_segs.write('</TIERS>\n')

def main():
    # Read in all of the parameters that ELAN passes to this local recognizer on
    # standard input.
    params = {}
    for line in sys.stdin:
        match = re.search(r'<param name="(.*?)".*?>(.*?)</param>', line)
        if match:
            params[match.group(1)] = match.group(2).strip()
            print(params)

    #upload wav file to the chosen service
    transcription = None
    filename = params["filename"] + ".wav"
    if params['transcription_service'] == 'AWS':
        aws.upload_file(params["source"], params["bucket"], filename)
        uri_path = "s3://" + params["bucket"] + "/" + filename
        #transcription now returns the information we need
        transcription = aws.transcribe_file(filename, uri_path, params["bucket"], params["output_path"])

    else:
        #upload wav file to the chosen service
        gcs.upload_file(params["bucket"], params["source"], filename, params["project"])
        uri_path = "gs://" + params["bucket"] + "/" + filename
        #transcription now returns the information we need
        transcription = gcs.transcribe_speech(uri_path)

    #now we add them to the eaf file within the chosen tier
    create_transcriptions(params['output_segments'], transcription, params['level'], params['threshold'], params['tier'])

    # Finally, tell ELAN that we're done.
    print('RESULT: DONE.', flush=True)

if __name__ == "__main__":
    main()
