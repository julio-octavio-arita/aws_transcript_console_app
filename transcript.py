#!/usr/bin/env python3
import re
import os
import constant


def get_ordered_speakers(filename):
    import json

    ordered_speakers = []
    with open(filename) as f:
        data = json.loads(f.read())
        labels = data['results']['speaker_labels']['segments']

        for label in labels:
            counter = 0
            for ordered_speaker in ordered_speakers:
                if ordered_speaker == label["speaker_label"]:
                    counter += 1
            if counter == 0:
                ordered_speakers.append(label["speaker_label"])

    return ordered_speakers


def parse_json(filename, txtfile, speakers):
    import json

    with open(filename) as f:
        # analysis json result of amazon transribe api and append transcript items to sorted_lines variable.
        data = json.loads(f.read())
        labels = data['results']['speaker_labels']['segments']
        speaker_start_times = {}
        for label in labels:
            for item in label['items']:
                speaker_start_times[item['start_time']] = item['speaker_label']
        items = data['results']['items']
        lines = []
        line = ''
        time = 0
        speaker = 'null'
        i = 0
        for item in items:
            i = i + 1
            content = item['alternatives'][0]['content']
            if item.get('start_time'):
                current_speaker = speaker_start_times[item['start_time']]
            elif item['type'] == 'punctuation':
                line = line + content
            if current_speaker != speaker:
                if speaker:
                    lines.append({'speaker': speaker, 'line': line, 'time': time})
                line = content
                speaker = current_speaker
                time = item['start_time']
            elif item['type'] != 'punctuation':
                line = line + ' ' + content
        lines.append({'speaker': speaker, 'line': line, 'time': time})
        sorted_lines = sorted(lines, key=lambda k: float(k['time']))

        ordered_speakers = get_ordered_speakers(filename)

        with open(txtfile, 'w') as file:
            file.write('<ul class="interview">' + '\n')
            for line_data in sorted_lines:
                if line_data.get('line') != "":
                    # speaker_data = re.split("spk_", line_data.get('speaker'))
                    # original_speaker_id = int(speaker_data[1])
                    for index, ordered_speaker in enumerate(ordered_speakers):
                        if ordered_speaker == line_data.get('speaker'):
                            original_speaker_id = index

                    line = '<li class="interview__item">' \
                           '<p class="interview__name">%s:</p>' \
                           '<p class="interview__response">%s</p>' \
                           '</li>' % (speakers[original_speaker_id], line_data.get('line'))
                    file.write(line + '\n')

            file.write('</ul>')
        file.close()

        return sorted_lines


def convert_html(json_file, filename, sorted_data, speakers):
    import shutil

    # Copy original html and paste into tmp/temp.html
    shutil.copy(
        constant.DATA_STORAGE + '/' + filename + '/Original/HTML/' + filename + '.html',
        'tmp/temp.html'
    )

    i = 0
    offset = 0
    for line_data in sorted_data:
        if line_data.get('line') != "":
            ordered_speakers = get_ordered_speakers(json_file)
            for index, ordered_speaker in enumerate(ordered_speakers):
                if ordered_speaker == line_data.get('speaker'):
                    original_speaker_id = index

            # ask if user will edit transcript result
            if int(int(float(line_data.get('time'))) / 60) > 9:
                hour = str(int(int(float(line_data.get('time'))) / 60))
            else:
                hour = "0" + str(int(int(float(line_data.get('time'))) / 60))

            if int(int(float(line_data.get('time'))) % 60) > 9:
                time = str(int(int(float(line_data.get('time'))) % 60))
            else:
                time = "0" + str(int(int(float(line_data.get('time'))) % 60))

            print("%d - %s(%s)" % (
                original_speaker_id + 1,
                speakers[original_speaker_id],
                hour + ":" + time)
                 + ": "
                 + line_data.get('line') + "\n")

            # check sentence is correct.
            is_correct = input("Is This Correct? ")
            print("\n")

            # if not correct,
            if is_correct.lower() == "no" or is_correct.lower() == "n":
                correct_text = input("Enter Corrected Text: ")
                split_list = re.split(r"\[\d+\](.*?)\[\/\d+\]", correct_text)

                count_element = 0
                for idx, item in enumerate(split_list):
                    if item != "":
                        count_element += 1

                line = ""
                append_index = 0
                for j, item in enumerate(split_list):
                    if item != "":
                        exist_prefix = re.search(r"\[\d+\]" + item, correct_text)

                        if exist_prefix is not None:
                            prefix_pos = exist_prefix.start()
                            item_pos = correct_text.find(item)
                            prefix = correct_text[prefix_pos:item_pos]

                            # get prefix speaker_id from tag
                            speaker_id = prefix[1:(len(prefix) - 1)]

                            # get suffix speaker_id from tag
                            suffix = correct_text[
                                     (item_pos + len(item)):(item_pos + len(item) + len(prefix) + 1)]
                            suffix_speaker_id = suffix[2:(len(suffix) - 1)]

                            if speaker_id == suffix_speaker_id:
                                for index, ordered_speaker in enumerate(ordered_speakers):
                                    if ordered_speaker == ("spk_" + str(int(speaker_id) - 1)):
                                        original_speaker_id = index

                                line = '<li class="interview__item">' \
                                    '<p class="interview__name">%s:</p>' \
                                    '<p class="interview__response">%s</p>' \
                                    '</li>' % (speakers[int(speaker_id)-1], item)

                                append_index += 1
                                update_html(filename, i, line, offset,
                                            True if append_index < count_element else False)
                                offset += 1
                        else:
                            line = '<li class="interview__item">' \
                                '<p class="interview__name">%s:</p>' \
                                '<p class="interview__response">%s</p>' \
                                '</li>' % (speakers[original_speaker_id], item)

                            append_index += 1
                            update_html(filename, i, line, offset,
                                        True if append_index < count_element else False)
                            offset += 1
                offset -= 1
            else:
                line = '<li class="interview__item">' \
                       '<p class="interview__name">%s:</p>' \
                       '<p class="interview__response">%s</p>' \
                       '</li>' % (speakers[original_speaker_id], line_data.get('line'))
                update_html(filename, i, line, offset, False)

            print("\n")

        i += 1


def update_html(txtfile, update_index, update_txt, offset, offsetflag=False):
    import shutil

    with open('tmp/temp.html', 'r') as r:
        lines = r.readlines()

        with open('tmp/temp.txt', 'a') as tw:
            for j, line in enumerate(lines):
                if (update_index + offset) == j:
                    if offsetflag:
                        line = update_txt + "\n" + line
                    else:
                        line = update_txt + "\n"
                tw.write(line)
        tw.close()
    r.close()

    os.remove('tmp/temp.html')

    with open('tmp/temp.html', 'w') as w:
        with open('tmp/temp.txt', 'r') as tr:
            tlines = tr.readlines()
            for tline in tlines:
                w.write(tline)
        tr.close()
    w.close()

    os.remove("tmp/temp.txt")

    if not offsetflag:
        edit_html_dir = constant.DATA_STORAGE + '/' + txtfile + '/Edits/HTML'
        if not os.path.exists(edit_html_dir):
            os.makedirs(edit_html_dir)

        shutil.copy(
            'tmp/temp.html',
            edit_html_dir + '/' + txtfile + '_' + str(update_index) + '.html'
        )

        edit_json_dir = constant.DATA_STORAGE + '/' + txtfile + '/Edits/JSON'
        if not os.path.exists(edit_json_dir):
            os.makedirs(edit_json_dir)

        shutil.copy(
            constant.DATA_STORAGE + '/' + txtfile + '/Original/JSON/' + txtfile + '.json',
            edit_json_dir + '/' + txtfile + '_' + str(update_index) + '.json'
        )
