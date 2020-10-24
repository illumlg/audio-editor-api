import time, random, sox, re, os
from flask import Flask, send_from_directory, abort
from flask import request
from config import *

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_SIZE


def get_format(file):
    return '.' + re.split('\.', file.filename)[-1].lower()


def is_valid_format(format):
    return format.lower() in VALID_FORMATS


def save_file(file):
    format = get_format(file)
    if is_valid_format(format):
        try:
            filename = str(round(time.time() * 1000)) + str(random.randint(1, 10000))
            file.save(INPUT_DIRECTORY + filename + format)
        except Exception as e:
            return False,str(e)
        return True, filename
    return False, ''


@app.route("/convert/<string:new_format>", methods=['POST'])
def convert(new_format):
    try:
        file = request.files['file']
        format = get_format(file)
    except Exception as e:
        print(e)
        return abort(400, e)
    if is_valid_format(format) and is_valid_format(new_format):
        is_success, filename = save_file(file)
        if is_success:
            try:
                sox.Transformer().build_file(INPUT_DIRECTORY + filename + format,
                                             OUTPUT_DIRECTORY + filename + new_format)
            except Exception as e:
                print(e)
                return abort(500, e)
            return send_from_directory(OUTPUT_DIRECTORY, filename + new_format)
        return abort(500, 'File can\'t be save')
    return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))


if __name__ == "__main__":
    app.run(debug=True)