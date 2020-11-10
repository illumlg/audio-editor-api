from locust import HttpUser, task, constant


class User(HttpUser):
    host = 'https://audio-editor-api.herokuapp.com'
    wait_time = constant(0)

    @task
    def get_info(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/info", files={'file': input_file})

    @task
    def reverse(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/reverse", files={'file': input_file})

    @task
    def trim(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/trim/start_time=5&end_time=15", files={'file': input_file})

    @task
    def treble(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/treble/gain=5", files={'file': input_file})

    @task
    def concatenate(self):
        with open('loadtest.wav', 'rb') as input_file, open('loadtest.wav', 'rb') as input_file1:
            self.client.post("/concatenate", files={'file': input_file, 'file1': input_file1})

    @task
    def mix(self):
        with open('loadtest.wav', 'rb') as input_file, open('loadtest.wav', 'rb') as input_file1:
            self.client.post("/mix", files={'file': input_file, 'file1': input_file1})

    @task
    def fade(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/fade/fade_start=5.0&fade_end=5.0", files={'file': input_file})

    @task
    def tremolo(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/tremolo", files={'file': input_file})

    @task
    def flanger(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/flanger/effect=medium", files={'file': input_file})

    @task
    def volume(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/volume/new_volume=5", files={'file': input_file})

    @task
    def chorus(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/chorus/number_of_voices=5", files={'file': input_file})

    @task
    def echo(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/echo", data={'gain_in': 0.4, 'gain_out': 0.6, 'n_echos': 1}, files={'file': input_file})

    @task
    def bass(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/bass", data={'gain_db': 4, 'frequency': 6, 'slope': 0.5}, files={'file': input_file})

    @task
    def speed(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/speed/new_speed=1.2", files={'file': input_file})

    @task
    def repeat(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/repeat/n=2", files={'file': input_file})

    @task
    def convert(self):
        with open('loadtest.wav', 'rb') as input_file:
            self.client.post("/convert/new_format=.snd", files={'file': input_file})
