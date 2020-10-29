import time, random, sox, re, os
from flask import Flask, send_from_directory, abort, g
from flask import request
from sox.core import is_number

from config import *

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_SIZE


def get_format(file):
    return '.' + re.split('\.', file.filename)[-1].lower()


def is_valid_format(format):
    return format.lower() in VALID_FORMATS


def generate_filename():
    return str(round(time.time() * 1000)) + str(random.randint(1, 10000))


def save_file(file):
    format = get_format(file)
    if is_valid_format(format):
        try:
            filename = generate_filename()
            g.path_to_files.append(INPUT_DIRECTORY + filename + format)
            g.path_to_files.append(OUTPUT_DIRECTORY + filename + format)
            file.save(INPUT_DIRECTORY + filename + format)
        except Exception as e:
            return False, str(e)
        return True, filename
    return False, ''


@app.before_request
def before_request():
    g.path_to_files = []
    total_size = sum([os.path.getsize(INPUT_DIRECTORY + file) for file in os.listdir(INPUT_DIRECTORY)]) + \
                 sum([os.path.getsize(OUTPUT_DIRECTORY + file) for file in os.listdir(OUTPUT_DIRECTORY)])
    g.access = total_size < STORAGE_LIMIT


@app.teardown_request
def clear(error=None):
    for path_to_file in g.path_to_files:
        if os.path.exists(path_to_file):
            os.remove(path_to_file)


@app.route("/trim/<int:start_time>/<int:end_time>", methods=['POST'])
def trim(start_time, end_time):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
        except Exception as e:
            print(e)
            return abort(400, e)
        if start_time >= end_time or start_time < 0 or end_time > get_info(file)['duration']:
            return abort(400, 'Please specify correct trimming bounds')
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.trim(start_time, end_time)
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                return send_from_directory(OUTPUT_DIRECTORY, filename + format)
            return abort(500, 'File can\'t be saved')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/treble/<int:gain>", methods=['POST'])
def treble(gain):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
        except Exception as e:
            print(e)
            return abort(400, e)
        if gain > 20 or gain < -20:
            return abort(400, 'Wrong gain value, valid values are from -20 to +20 ')
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.treble(gain_db=gain)
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                return send_from_directory(OUTPUT_DIRECTORY, filename + format)
            return abort(500, 'File can\'t be saved')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/reverse", methods=['POST'])
def reverse():
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
        except Exception as e:
            print(e)
            return abort(400, e)
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.reverse()
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be save')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/concatenate", methods=['POST'])
def concatenate():
    if g.access:
        dict_files = dict(request.files)
        path_to_files = []
        for item in dict_files:
            if not is_valid_format(get_format(dict_files[item])):
                return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
            is_success, filename = save_file(dict_files[item])
            print(filename)
            path_to_files.append(INPUT_DIRECTORY + filename + get_format(dict_files[item]))
            if not is_success:
                return abort(500, 'File can\'t be saved')
        try:
            tr = sox.Combiner()
            output_filename = generate_filename()
            g.path_to_files.append(OUTPUT_DIRECTORY + output_filename + '.ogg')
            tr.build(path_to_files, OUTPUT_DIRECTORY + output_filename + '.ogg', 'concatenate')
            with open(OUTPUT_DIRECTORY + output_filename + '.ogg', 'rb') as file:
                bytes = file.read()
            return app.make_response(bytes)
        except Exception as e:
            print(e)
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/mix", methods=['POST'])
def mix():
    if g.access:
        dict_files = dict(request.files)
        path_to_files = []
        for item in dict_files:
            if not is_valid_format(get_format(dict_files[item])):
                return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
            is_success, filename = save_file(dict_files[item])
            print(filename)
            path_to_files.append(INPUT_DIRECTORY + filename + get_format(dict_files[item]))
            if not is_success:
                return abort(500, 'File can\'t be save')
        try:
            tr = sox.Combiner()
            output_filename = generate_filename()
            g.path_to_files.append(OUTPUT_DIRECTORY + output_filename + '.ogg')
            tr.build(path_to_files, OUTPUT_DIRECTORY + output_filename + '.ogg', 'mix')
            with open(OUTPUT_DIRECTORY + output_filename + '.ogg', 'rb') as file:
                bytes = file.read()
            return app.make_response(bytes)
        except Exception as e:
            print(e)
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/attenuation_effect/<float:fade_start>/<float:fade_end>", methods=['POST'])
def attenuation_effect(fade_start, fade_end):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
        except Exception as e:
            print(e)
            return abort(400, e)
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.fade(fade_start, fade_end)
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be save')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/flanger/<string:effect>", methods=['POST'])
def flanger(effect):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
        except Exception as e:
            print(e)
            return abort(400, e)
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    if effect == 'low':
                        tr.flanger()
                    elif effect == 'medium':
                        tr.flanger(5, 4, speed=2, shape='triangle')
                    elif effect == 'high':
                        tr.flanger(20, 8, speed=5, shape='triangle')
                    else:
                        return abort(400, 'Choose one of them: low, medium, high')
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be save')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/tremolo", methods=['POST'], defaults={'speed': 6, 'depth': 50})
@app.route("/tremolo/<int:speed>/<int:depth>", methods=['POST'])
def tremolo(speed, depth):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
        except Exception as e:
            print(e)
            return abort(400, e)
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.tremolo(speed, depth)
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be save')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/volume/<string:new_volume>", methods=['POST'])
def volume(new_volume):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            new_volume = int(new_volume)
        except Exception as e:
            print(e)
            return abort(400, e)
        if not MIN_VOLUME <= new_volume <= MAX_VOLUME:
            return abort(400, 'Change volume, '
                              'max value = {}, min value = {} '.format(MAX_VOLUME, MIN_VOLUME))
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.vol(new_volume, 'db')
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be save')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


def get_info(file):
    return {'channels': sox.file_info.channels(file),
            'sample_rate': sox.file_info.sample_rate(file),
            'encoding': sox.file_info.encoding(file),
            'duration': sox.file_info.duration(file),
            'size': os.stat(file).st_size}


@app.route("/chorus/<int:number_of_voices>", methods=['POST'])
def chorus(number_of_voices):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
        except Exception as e:
            print(e)
            return abort(400, e)
        if number_of_voices > MAX_VOICES:
            return abort(400, 'Too many voices, limit ' + str(MAX_VOICES))
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.chorus(n_voices=number_of_voices)
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be saved')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/echo", methods=['POST'])
def echo():
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)

            gain_in = request.form.get('gain_in')
            gain_out = request.form.get('gain_out')
            n_echos = request.form.get('n_echos')
            delays = request.form.get('delays')
            decays = request.form.get('decays')
        except Exception as e:
            print(e)
            return abort(400, e)

        # validate input params
        if 1 < gain_in <= 0:
            return abort(400, 'gain_in must be a number between 0 and 1.')
        if 1 < gain_out <= 0:
            return abort(400, 'gain_out must be a number between 0 and 1. ')
        if n_echos <= 0:
            return abort(400, 'n_echos must be a positive integer.')

        # validate delays
        if not isinstance(delays, list):
            return abort(400, "delays must be a list")
        if len(delays) != n_echos:
            return abort(400, "the length of delays must equal n_echos")
        if any((not is_number(p) or p <= 0) for p in delays):
            return abort(400, "the elements of delays must be numbers > 0")

        # validate decays
        if not isinstance(decays, list):
            return abort(400, "decays must be a list")
        if len(decays) != n_echos:
            return abort(400, "the length of decays must equal n_echos")
        if any((not is_number(p) or p <= 0 or p > 1) for p in decays):
            return abort(400, "the elements of decays must be between 0 and 1")

        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.echo(gain_in, gain_out, n_echos, delays, decays)
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be saved')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/bass", methods=['POST'])
def bass():
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)

            gain_db = request.form.get('gain_db')
            frequency = request.form.get('frequency')
            slope = request.form.get('slope')

        except Exception as e:
            print(e)
            return abort(400, e)

        # validate input params
        if not is_number(gain_db):
            return abort(400, "gain_db must be a number")
        if not is_number(frequency) or frequency <= 0:
            return abort(400, "frequency must be a positive number.")
        if not is_number(slope) or slope <= 0 or slope > 1.0:
            return abort(400, "width_q must be a positive number.")

        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.bass(gain_db, frequency, slope)
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be save')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/speed/<float:new_speed>", methods=['POST'])
def speed(new_speed):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
        except Exception as e:
            print(e)
            return abort(400, e)
        if not MIN_SPEED <= new_speed <= MAX_SPEED:
            return abort(400, 'Change speed, '
                              'max value = {}, min value = {} '.format(MAX_SPEED, MIN_SPEED))
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.speed(new_speed)
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be save')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/repeat/<int:n>", methods=['POST'])
def repeat(n):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
        except Exception as e:
            print(e)
            return abort(400, e)
        if n > MAX_REPEATS:
            return abort(400, 'Too many repeats,limit ' + str(MAX_REPEATS))
        if is_valid_format(format):
            is_success, filename = save_file(file)
            if is_success:
                try:
                    tr = sox.Transformer()
                    tr.repeat(n)
                    tr.build_file(INPUT_DIRECTORY + filename + format,
                                  OUTPUT_DIRECTORY + filename + format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be save')
        return abort(400, 'Format not available, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/convert/<string:new_format>", methods=['POST'])
def convert(new_format):
    if g.access:
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
                    g.path_to_files.append(OUTPUT_DIRECTORY + filename + new_format)
                    sox.Transformer().build_file(INPUT_DIRECTORY + filename + format,
                                                 OUTPUT_DIRECTORY + filename + new_format)
                except Exception as e:
                    print(e)
                    return abort(500, e)
                with open(OUTPUT_DIRECTORY + filename + new_format, 'rb') as file:
                    bytes = file.read()
                return app.make_response(bytes)
            return abort(500, 'File can\'t be save')
        return abort(400, 'Check formats, available formats: ' + str(VALID_FORMATS))
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


if __name__ == "__main__":
    app.run(debug=True)
