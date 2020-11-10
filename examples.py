import requests

base_url = 'https://audio-editor-api.herokuapp.com'

filename = 'example input files/input.wav'

req = requests.post(base_url + '/repeat/n=3',files={'file': open(filename,'rb')})
print('Repeat',req.status_code)
with open('example output files/repeat-3.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/speed/new_speed=2.0',files={'file': open(filename,'rb')})
print('Speed',req.status_code)
with open('example output files/speed-2.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/bass',data={'gain_db':13,'frequency':300,'slope':0.5},files={'file':  open(filename,'rb')})
print('Bass',req.status_code)
with open('example output files/bass-13-300-0.5.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/echo',data={'gain_in':1,'gain_out':1,'n_echos':1},files={'file':  open(filename,'rb')})
print('Echo',req.status_code)
with open('example output files/echo-1-1-1.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/chorus/number_of_voices=3',files={'file':  open(filename,'rb')})
print('Chorus',req.status_code)
with open('example output files/chorus-3.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/info',files={'file':  open(filename,'rb')})
print('Info',req.status_code)
with open('example output files/info.txt','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/volume/new_volume=-20',files={'file':  open(filename,'rb')})
print('Volume',req.status_code)
with open('example output files/volume-20.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/tremolo',files={'file':  open(filename,'rb')})
print('Tremolo',req.status_code)
with open('example output files/tremolo-default.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/flanger/effect=medium',files={'file':  open(filename,'rb')})
print('Flanger',req.status_code)
with open('example output files/flanger-medium.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/fade/fade_start=3.0&fade_end=7.0',files={'file':  open(filename,'rb')})
print('Fade',req.status_code)
with open('example output files/fade-3-7.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/mix',files={'file2':  open('example input files/input2.wav','rb'),'file3':  open('example input files/input3.wav','rb'),'file4':  open('example input files/input4.wav','rb')})
print('Mix',req.status_code)
with open('example output files/mix.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/concatenate',files={'file':  open(filename,'rb'),'file2':  open('example input files/input2.wav','rb'),'file3':  open('example input files/input3.wav','rb'),'file4':  open('example input files/input4.wav','rb')})
print('Concatenate',req.status_code)
with open('example output files/concatenate-4.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/reverse',files={'file':  open(filename,'rb')})
print('Reverse',req.status_code)
with open('example output files/reverse.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/treble/gain=18',files={'file':  open(filename,'rb')})
print('Treble',req.status_code)
with open('example output files/treble-18.wav','wb') as file:
    file.write(req.content)

req = requests.post(base_url + '/trim/start_time=2&end_time=5',files={'file':  open(filename,'rb')})
print('Trim',req.status_code)
with open('example output files/trim-2-5.wav','wb') as file:
    file.write(req.content)