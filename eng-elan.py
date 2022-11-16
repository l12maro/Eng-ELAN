import os
from re import findall
import re, sys
import aws, gcs
import xml.etree.ElementTree as ET

#TODO: Adapt for Google Cloud: transcription conversion in aws/gcs files instead on in this code
#TODO: Add each transcription within their timestamps
## To Discuss: Amazon only provides word-level word stamps, while google provides sentence and word-level.
## Use only word-level for both or add sentence-level option when using google?

def add_transcriptions(output, transcriptions):
    # Then open 'output_segments' for writing, and return all of the new speech
    # segments transcriptions as the contents of <span> elements (see
    # below).
    with open(output, 'w', encoding='utf-8') as output_segs:
        # Write document header.
        output_segs.write('<?xml version="1.0" encoding="UTF-8"?>\n')

        # Write out the adjusted annotations
        output_segs.write(
            '<TIER xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="file:avatech-tier.xsd" columns="English">\n')

        #output_segs.write( \
        #            '<span start="%.3f" end="%.3f"><v></v></span>\n' % \
        #            ((a['start'] / 1000.0) + adjust_start_s, \
        #             (a['end'] / 1000.0) + adjust_end_s))
        print(transcriptions['results']['transcripts'][0]['transcript'])
        output_segs.write(
                    '<span start="0" end= "2000"><v>' + transcriptions['results']['transcripts'][0]['transcript'] + '</v></span>\n')
        ##which attribute can be used for text value?

        output_segs.write('</TIER>\n')


    '''
    # Which tier?
    tier_name = tier
    tree = ET.parse(file_[:-3] + "eaf")

    root = tree.getroot()

    #match transcription timestamps with tiers
    i = 1
    x = 0
    for times in root.iter('TIME_SLOT'):
        j = i + 1
        element = root.find('TIME_ORDER')
        e = element.findall('TIME_SLOT')
        s_time = ""
        e_time = ""
        for t in e:
            if t.get('TIME_SLOT_ID') == "ts" + str(i):
                s_time = t.get('TIME_VALUE')

            if t.get('TIME_SLOT_ID') == "ts" + str(j):
                e_time = t.get('TIME_VALUE')
                break
        list_of_items = transcriptions['results']['items']
        while True:
            if x >= len(list_of_items): break
            #convert time format and check where it belongs
            token = list_of_items[x]
            x += 1
            if token['type'] == "punctuation": continue
            token_start = token['start_time']
            token_start = int(float(token_start) * 1000)
            token_end = token['end_time']
            token_end = int(float(token_end) * 1000)
            
            if token_start >= int(s_time) and token_end <= int(e_time):
                #find the tier segment it belongs to
                for tier in root.iter('TIER'):
                    if tier.attrib['TIER_ID'] == tier_name:
                        for anon in tier.iter('ALIGNABLE_ANNOTATION'):
                            #for a in anon:
                            if anon.attrib['ANNOTATION_ID'] == "a" + str(int(j/2)):
                                for annotation in anon.iter('ANNOTATION_VALUE'):
                                    # insert text
                                    source_text = token["alternatives"][0]["content"]
                                
                                    # update the annotation
                                    if annotation.text == None:
                                        annotation.text = str(source_text)
                                    else:
                                        text = " " + str(source_text)
                                        annotation.text += text

                                    # feedback
                                    #print("done")

            
            #go to the next tier when all the words have been inserted
            else:
                if token_end > int(e_time): break
        i += 2

    # Save the file to output dir
    tree.write(tree)
    '''
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
        #transcription now returns the json file with the transcription output
        transcription = aws.transcribe_file(filename, uri_path, params["bucket"], params["output_path"])

    #Google Cloud is used as default service when the specified parameter is not AWS
    else:
        #upload wav file to the chosen service
        gcs.upload_file(params["bucket"], params["source"], filename)
        uri_path = "gs://" + params["bucket"] + "/" + filename
        #get the transcription
        transcription = gcs.transcribe_speech(uri_path)

    #now we add them to the eaf file within the chosen tier
    add_transcriptions(params['output_segments'], transcription)

    # Finally, tell ELAN that we're done.
    print('RESULT: DONE.', flush=True)

if __name__ == "__main__":
    main()
