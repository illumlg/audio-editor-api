import werkzeug,time, random, sox, re, os
from flask import Flask, abort, g
from flask import request
from sox.core import is_number
from const import *

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_SIZE


def get_format(file):
    return '.' + re.split('\.', file.filename)[-1].lower()


def is_valid_format(format):
    return format.lower() in VALID_FORMATS


def generate_filename():
    return str(round(time.time() * 1000)) + str(random.randint(1, 10000))


def read_file(path):
    with open(path, 'rb') as file:
        return file.read()


def save_file(file):
    format = get_format(file)
    try:
        filename = generate_filename()
        g.path_to_files.append(INPUT_DIRECTORY + filename + format)
        g.path_to_files.append(OUTPUT_DIRECTORY + filename + format)
        file.save(INPUT_DIRECTORY + filename + format)
    except Exception as e:
        return False, str(e)
    return True, filename

@app.before_request
def before_request():
    g.path_to_files = []
    g.transformer = sox.Transformer()
    g.combiner = sox.Combiner()
    total_size = sum([os.path.getsize(INPUT_DIRECTORY + file) for file in os.listdir(INPUT_DIRECTORY)]) + \
                 sum([os.path.getsize(OUTPUT_DIRECTORY + file) for file in os.listdir(OUTPUT_DIRECTORY)])
    g.access = total_size < STORAGE_LIMIT


@app.teardown_request
def clear(error=None):
    for path_to_file in g.path_to_files:
        if os.path.exists(path_to_file):
            os.remove(path_to_file)


@app.route("/trim/start_time=<int:start_time>&end_time=<int:end_time>", methods=['POST'])
def trim(start_time, end_time):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            g.transformer.trim(start_time, end_time)
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/treble/gain=<int:gain>", methods=['POST'])
def treble(gain):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            g.transformer.treble(gain_db=gain)
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400,e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500,e)
        except Exception as e:
            return abort(500,e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/reverse", methods=['POST'])
def reverse():
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            g.transformer.reverse()
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
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
            output_filename = generate_filename()
            g.path_to_files.append(OUTPUT_DIRECTORY + output_filename + '.ogg')
            g.combiner.build(path_to_files, OUTPUT_DIRECTORY + output_filename + '.ogg', 'concatenate')
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
            output_filename = generate_filename()
            g.path_to_files.append(OUTPUT_DIRECTORY + output_filename + '.ogg')
            g.combiner.build(path_to_files, OUTPUT_DIRECTORY + output_filename + '.ogg', 'mix')
            with open(OUTPUT_DIRECTORY + output_filename + '.ogg', 'rb') as file:
                bytes = file.read()
            return app.make_response(bytes)
        except Exception as e:
            print(e)
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/fade/fade_start=<float:fade_start>&fade_end=<float:fade_end>", methods=['POST'])
def attenuation_effect(fade_start, fade_end):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            g.transformer.fade(fade_start, fade_end)
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res

@app.route("/flanger/effect=<string:effect>", methods=['POST'])
def flanger(effect):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            if effect == 'low':
                g.transformer.flanger()
            elif effect == 'medium':
                g.transformer.flanger(5, 4, speed=2, shape='triangle')
            elif effect == 'high':
                g.transformer.flanger(20, 8, speed=5, shape='triangle')
            else: return abort(400, 'Choose one of them: low, medium, high')
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res

@app.route("/tremolo", methods=['POST'], defaults={'speed': 6, 'depth': 50})
@app.route("/tremolo/speed=<int:speed>&depth=<int:depth>", methods=['POST'])
def tremolo(speed, depth):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            g.transformer.tremolo(speed, depth)
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res

@app.route("/volume/new_volume=<string:new_volume>", methods=['POST'])
def volume(new_volume):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            if not MIN_VOLUME <= new_volume <= MAX_VOLUME:
                return abort(400, 'Change volume, '
                                  'max value = {}, min value = {} '.format(MAX_VOLUME, MIN_VOLUME))
            g.transformer.vol(new_volume, 'db')
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/info", methods=['POST'])
def get_info():
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            filename = INPUT_DIRECTORY + filename + format
            return {'channels': sox.file_info.channels(filename),
                    'sample_rate': sox.file_info.sample_rate(filename),
                    'encoding': sox.file_info.encoding(filename),
                    'duration': sox.file_info.duration(filename),
                    'size': os.stat(filename).st_size}
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res

@app.route("/chorus/number_of_voices=<int:number_of_voices>", methods=['POST'])
def chorus(number_of_voices):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            if number_of_voices > MAX_VOICES:
                return abort(400, 'Too many voices, limit ' + str(MAX_VOICES))
            g.transformer.chorus(n_voices=number_of_voices)
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
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
                    g.transformer.echo(gain_in, gain_out, n_echos, delays, decays)
                    g.transformer.build_file(INPUT_DIRECTORY + filename + format,
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
                    g.transformer.bass(gain_db, frequency, slope)
                    g.transformer.build_file(INPUT_DIRECTORY + filename + format,
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


@app.route("/speed/new_speed=<float:new_speed>", methods=['POST'])
def speed(new_speed):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            if not MIN_SPEED <= new_speed <= MAX_SPEED:
                return abort(400, 'Change speed, '
                                  'max value = {}, min value = {} '.format(MAX_SPEED, MIN_SPEED))
            g.transformer.speed(new_speed)
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/repeat/n=<int:n>", methods=['POST'])
def repeat(n):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            if n > MAX_REPEATS:
                return abort(400, 'Too many repeats,limit ' + str(MAX_REPEATS))
            g.transformer.repeat(n)
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/convert/new_format=<string:new_format>", methods=['POST'])
def convert(new_format):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            g.path_to_files.append(OUTPUT_DIRECTORY + filename + new_format)
            sox.Transformer().build_file(INPUT_DIRECTORY + filename + format,
                                         OUTPUT_DIRECTORY + filename + new_format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            return abort(500, e)
        except Exception as e:
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


if __name__ == "__main__":
    app.run(debug=True)
