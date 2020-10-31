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


    def test_reverse(self):
        input_file = open(self.input_file_path, 'rb')

        response = self.app.post('/reverse',
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.reverse()
        self.transformer.build_file(self.input_file_path,
                                    self.output_file_path)

        with open(self.output_file_path, 'rb') as file:
            expected_file = file.read()

        self.assertEqual(expected_file, response.data)


    def test_treble(self):
        input_file = open(self.input_file_path, 'rb')

        gain = 3
        response = self.app.post('/treble/gain=' + str(3),
                                 data={'file': input_file})

        input_file.close()

        self.assertTrue(response)
        self.assertEqual("200 OK", response.status)

        self.transformer.treble(gain_db=gain)
        self.transformer.build_file(self.input_file_path,
                                    self.output_file_path)

        with open(self.output_file_path, 'rb') as file:
            expected_file = file.read()

        self.assertEqual(expected_file, response.data)


if __name__ == '__main__':
    unittest.main()
