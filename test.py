import os
import unittest

import sox

from app import app


class AppTests(unittest.TestCase):
    input_file_path = 'test_input_files/testFile.wav'
    output_file_path = 'test_output_files/testFile.wav'

    def setUp(self):
        app.config['TESTING'] = True
        app.config["DEBUG"] = False
        self.app = app.test_client()
        self.transformer = sox.Transformer()

    def tearDown(self):
        pass

    def test_page_not_fount(self):
        input_file = open(self.input_file_path, 'rb')

        response = self.app.post('/dummy-url',
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("404 NOT FOUND", response.status)

    def test_method_not_allowed(self):
        input_file = open(self.input_file_path, 'rb')

        response = self.app.get('/reverse',
                                data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("405 METHOD NOT ALLOWED", response.status)

    def test_treble(self):
        input_file = open(self.input_file_path, 'rb')

        gain = 3
        response = self.app.post('/treble/gain=' + str(3),
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.treble(gain_db=gain)
        expected_file = self.get_expected_file()
        self.assertEqual(expected_file, response.data)

    def test_fade(self):
        input_file = open(self.input_file_path, 'rb')

        fade_start = 1.5
        fade_end = 2.9

        response = self.app.post('/fade/fade_start=' + str(fade_start) + '&fade_end=' + str(fade_end),
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.fade(fade_in_len=fade_start, fade_out_len=fade_end)
        expected_file = self.get_expected_file()
        self.assertEqual(expected_file, response.data)

    def test_tremolo(self):
        input_file = open(self.input_file_path, 'rb')

        speed = 5
        depth = 50

        response = self.app.post('/tremolo/speed=' + str(speed) + '&depth=' + str(depth),
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.tremolo(speed, depth)
        expected_file = self.get_expected_file()
        self.assertEqual(expected_file, response.data)

    def test_volume(self):
        input_file = open(self.input_file_path, 'rb')

        new_volume = 14

        response = self.app.post('/volume/new_volume=' + str(new_volume),
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.vol(new_volume, 'db')
        expected_file = self.get_expected_file()
        self.assertEqual(expected_file, response.data)

    def test_speed(self):
        input_file = open(self.input_file_path, 'rb')

        new_speed = 7.0

        response = self.app.post('/speed/new_speed=' + str(new_speed),
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.speed(factor=new_speed)
        expected_file = self.get_expected_file()
        self.assertEqual(expected_file, response.data)

    def test_repeat(self):
        input_file = open(self.input_file_path, 'rb')

        n = 2

        response = self.app.post('/repeat/n=' + str(n),
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.repeat(count=n)
        expected_file = self.get_expected_file()
        self.assertEqual(expected_file, response.data)

    def test_convert(self):
        input_file = open(self.input_file_path, 'rb')

        new_format = ".au"
        new_format_file_path = 'test_output_files/testFile' + new_format

        response = self.app.post('/convert/new_format=' + new_format,
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.build_file(self.input_file_path,
                                    new_format_file_path)

        with open(new_format_file_path, 'rb') as file:
            expected_file = file.read()
        file.close()

        self.assertEqual(expected_file, response.data)

    def test_bass(self):
        input_file = open(self.input_file_path, 'rb')

        gain_db = 15
        frequency = 90
        slope = 0.7

        response = self.app.post('/bass',
                                 data={'file': input_file,
                                       'gain_db': gain_db,
                                       'frequency': frequency,
                                       'slope': slope
                                       })

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.bass(gain_db=gain_db, frequency=frequency, slope=slope)
        expected_file = self.get_expected_file()
        self.assertEqual(expected_file, response.data)

    def test_echo(self):
        input_file = open(self.input_file_path, 'rb')

        gain_in = 0.8
        gain_out = 0.9
        n_echos = 1

        response = self.app.post('/echo',
                                 data={'file': input_file,
                                       'gain_in': gain_in,
                                       'gain_out': gain_out,
                                       'n_echos': n_echos,
                                       })
        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.echo(gain_in=gain_in, gain_out=gain_out, n_echos=n_echos)
        expected_file = self.get_expected_file()
        self.assertEqual(expected_file, response.data)

    def test_get_info(self):
        input_file = open(self.input_file_path, 'rb')

        response = self.app.post('/info',
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)
        self.assertTrue(response.data)

    def test_chorus(self):
        input_file = open(self.input_file_path, 'rb')

        number_of_voices = 1

        response = self.app.post('/chorus/number_of_voices=3',
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.chorus(n_voices=number_of_voices)
        expected_file = self.get_expected_file()

    def test_reverse(self):
        input_file = open(self.input_file_path, 'rb')

        response = self.app.post('/reverse',
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.reverse()
        expected_file = self.get_expected_file()
        self.assertEqual(expected_file, response.data)

    def get_expected_file(self):
        self.transformer.build_file(self.input_file_path,
                                    self.output_file_path)
        with open(self.output_file_path, 'rb') as file:
            expected_file = file.read()
        file.close()

        return expected_file


if __name__ == '__main__':
    unittest.main()
