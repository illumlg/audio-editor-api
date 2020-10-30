import datetime
import sqlite3

import werkzeug, time, random, sox, re, os
from flask import Flask, abort, g, render_template
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


def save_log(request_name,status,status_code,description,params):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO logs VALUES (NULL ,?,?,?,?,?,?)",
                (datetime.datetime.now(),request_name,status,status_code,description,params))
            conn.commit()
    except sqlite3.Error as e:
        print(e)

def main(func, *args):
    if g.access:
        try:
            file = request.files['file']
            format = get_format(file)
            is_success, filename = save_file(file)
            if args == ():
                func()
            else:
                func(*args)
            g.transformer.build_file(INPUT_DIRECTORY + filename + format,
                                     OUTPUT_DIRECTORY + filename + format)
            return app.make_response(read_file(OUTPUT_DIRECTORY + filename + format))
        except werkzeug.exceptions.BadRequest as e:
            g.error = True
            save_log(g.request_name,'ERROR',400, str(e), g.params)
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 400, str(e), g.params)
            return abort(500, e)
        except Exception as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 500, str(e), g.params)
            return abort(500, e)
    g.error = True
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    save_log(g.request_name, 'ERROR', 507,
             'Storage is overflow, try again after a few seconds', g.params)
    return res

@app.errorhandler(404)
def page_not_found(e):
    g.error = True
    save_log(g.request_name, 'ERROR', 404, '404 Not Found: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.', g.params)
    res = app.make_response('404 Not Found: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.')
    res.status_code = 404
    return res

@app.before_request
def before_request():
    g.request_name = request.path
    g.params = '()'
    g.error = False
    g.path_to_files = []
    g.transformer = sox.Transformer()
    g.combiner = sox.Combiner()
    total_size = sum([os.path.getsize(INPUT_DIRECTORY + file) for file in os.listdir(INPUT_DIRECTORY)]) + \
                 sum([os.path.getsize(OUTPUT_DIRECTORY + file) for file in os.listdir(OUTPUT_DIRECTORY)])
    g.access = total_size < STORAGE_LIMIT


@app.teardown_request
def finish_request(error=None):
    for path_to_file in g.path_to_files:
        if os.path.exists(path_to_file):
            os.remove(path_to_file)
    if not g.error:
        save_log(g.request_name, 'OK', 200, 'success', g.params)


def core_trim(start_time, end_time):
    g.transformer.trim(start_time, end_time)


@app.route("/trim/start_time=<int:start_time>&end_time=<int:end_time>", methods=['POST'])
def trim(start_time, end_time):
    g.request_name = request.path
    g.params = str((start_time,end_time))
    return main(core_trim, start_time, end_time)


def core_treble(gain):
    g.transformer.treble(gain_db=gain)


@app.route("/treble/gain=<int:gain>", methods=['POST'])
def treble(gain):
    g.params = '('+str(gain)+')'
    return main(core_treble, gain)


def core_reverse():
    g.transformer.reverse()


@app.route("/reverse", methods=['POST'])
def reverse():
    return main(core_reverse)


@app.route("/concatenate", methods=['POST'])
def concatenate():
    if g.access:
        try:
            dict_files = dict(request.files)
            path_to_files = []
            for item in dict_files:
                is_success, filename = save_file(dict_files[item])
                path_to_files.append(INPUT_DIRECTORY + filename + get_format(dict_files[item]))
                if not is_success:
                    return abort(500, 'File can\'t be saved')
            output_filename = generate_filename()
            g.path_to_files.append(OUTPUT_DIRECTORY + output_filename + '.ogg')
            g.combiner.build(path_to_files, OUTPUT_DIRECTORY + output_filename + '.ogg', 'concatenate')
            return app.make_response(read_file(OUTPUT_DIRECTORY + output_filename + '.ogg'))
        except werkzeug.exceptions.BadRequest as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 400, str(e), g.params)
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 400, str(e), g.params)
            return abort(500, e)
        except Exception as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 500, str(e), g.params)
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


@app.route("/mix", methods=['POST'])
def mix():
    if g.access:
        try:
            dict_files = dict(request.files)
            path_to_files = []
            for item in dict_files:
                is_success, filename = save_file(dict_files[item])
                path_to_files.append(INPUT_DIRECTORY + filename + get_format(dict_files[item]))
                if not is_success:
                    return abort(500, 'File can\'t be saved')
            output_filename = generate_filename()
            g.path_to_files.append(OUTPUT_DIRECTORY + output_filename + '.ogg')
            g.combiner.build(path_to_files, OUTPUT_DIRECTORY + output_filename + '.ogg', 'mix')
            return app.make_response(read_file(OUTPUT_DIRECTORY + output_filename + '.ogg'))
        except werkzeug.exceptions.BadRequest as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 400, str(e), g.params)
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 400, str(e), g.params)
            return abort(500, e)
        except Exception as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 500, str(e), g.params)
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


def core_fade(fade_start, fade_end):
    g.transformer.fade(fade_start, fade_end)


@app.route("/fade/fade_start=<float:fade_start>&fade_end=<float:fade_end>", methods=['POST'])
def fade(fade_start, fade_end):
    g.params = str((fade_start, fade_end))
    return main(core_fade, fade_start, fade_end)


def core_flanger(preset):
    if preset == 'low':
        g.transformer.flanger()
    elif preset == 'medium':
        g.transformer.flanger(5, 4, speed=2, shape='triangle')
    elif preset == 'high':
        g.transformer.flanger(20, 8, speed=5, shape='triangle')
    else:
        return abort(400, 'Choose one of them: low, medium, high')


@app.route("/flanger/effect=<string:effect>", methods=['POST'])
def flanger(effect):
    g.params = '('+effect+')'
    return main(core_flanger, effect)


def core_tremolo(speed, depth):
    g.transformer.tremolo(speed, depth)


@app.route("/tremolo", methods=['POST'], defaults={'speed': 6, 'depth': 50})
@app.route("/tremolo/speed=<int:speed>&depth=<int:depth>", methods=['POST'])
def tremolo(speed, depth):
    g.params = str((speed, depth))
    return main(core_tremolo, speed, depth)


def core_volume(new_volume):
    if not MIN_VOLUME <= new_volume <= MAX_VOLUME:
        return abort(400, 'Change volume, '
                          'max value = {}, min value = {} '.format(MAX_VOLUME, MIN_VOLUME))
    g.transformer.vol(new_volume, 'db')


@app.route("/volume/new_volume=<string:new_volume>", methods=['POST'])
def volume(new_volume):
    g.params = '('+new_volume+')'
    return main(core_volume, int(new_volume))


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
            g.error = True
            save_log(g.request_name, 'ERROR', 400, str(e), g.params)
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 400, str(e), g.params)
            return abort(500, e)
        except Exception as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 500, str(e), g.params)
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


def core_chorus(number_of_voices):
    if number_of_voices > MAX_VOICES:
        return abort(400, 'Too many voices, limit ' + str(MAX_VOICES))
    g.transformer.chorus(n_voices=number_of_voices)


@app.route("/chorus/number_of_voices=<int:number_of_voices>", methods=['POST'])
def chorus(number_of_voices):
    g.params = '('+str(number_of_voices)+')'
    return main(core_chorus, number_of_voices)

#!!!
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

#!!!
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


def core_speed(new_speed):
    if not MIN_SPEED <= new_speed <= MAX_SPEED:
        return abort(400, 'Change speed, '
                          'max value = {}, min value = {} '.format(MAX_SPEED, MIN_SPEED))
    g.transformer.speed(new_speed)


@app.route("/speed/new_speed=<float:new_speed>", methods=['POST'])
def speed(new_speed):
    g.params = '('+str(new_speed)+')'
    return main(core_speed, new_speed)


def core_repeat(n):
    if n > MAX_REPEATS:
        return abort(400, 'Too many repeats,limit ' + str(MAX_REPEATS))
    g.transformer.repeat(n)


@app.route("/repeat/n=<int:n>", methods=['POST'])
def repeat(n):
    g.params = '('+str(n)+')'
    return main(core_repeat, n)


@app.route("/convert/new_format=<string:new_format>", methods=['POST'])
def convert(new_format):
    g.params = '('+new_format+')'
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
            g.error = True
            save_log(g.request_name, 'ERROR', 400, str(e), g.params)
            return abort(400, e)
        except sox.core.SoxiError or sox.core.SoxError as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 400, str(e), g.params)
            return abort(500, e)
        except Exception as e:
            g.error = True
            save_log(g.request_name, 'ERROR', 500, str(e), g.params)
            return abort(500, e)
    res = app.make_response('Storage is overflow, try again after a few seconds')
    res.status_code = 507
    return res


if __name__ == "__main__":
    app.run(debug=True)
