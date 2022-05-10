"""
Модуль для пьезогенератора
Вдохновлён https://github.com/fruch/micropython-buzzer
"""
# ToDo: изучить и улучшить базовый класс http://sotovaya.com/notes-nokia.html
# много мелодий https://vk.com/topic-96676_22391837?ysclid=l2zvum0o9o
__author__ = "Nikolay Putko"
__copyright__ = "Nikolay Putko, 2022 onwards."
__license__ = "MIT https://opensource.org/licenses/MIT (as used by MicroPython)."
__version__ = "1.5.0"
__repo__ = "https://github.com/Omni-K/Iskra_JS_micropython"

from math import pow

import struct
import sys
from pwm import PWM


class Note(object):
    """Represents a single MIDI note"""

    note_names = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

    def __init__(self, channel, pitch, velocity, start, duration=0):
        self.channel = channel
        self.pitch = pitch
        self.velocity = velocity
        self.start = start
        self.duration = duration

    def __str__(self):
        s = Note.note_names[(self.pitch - 9) % 12]
        s += str(self.pitch // 12 - 1)
        s += " " + str(self.velocity)
        s += " " + str(self.start) + " " + str(self.start + self.duration) + " "
        return s

    def get_end(self):
        return self.start + self.duration


class MidiFile(object):
    """
    Represents the notes in a MIDI file
    """

    def read_byte(self, file):
        return struct.unpack('B', file.read(1))[0]

    def read_variable_length(self, file, counter):
        counter -= 1
        num = self.read_byte(file)

        if num & 0x80:
            num = num & 0x7F
            while True:
                counter -= 1
                c = self.read_byte(file)
                num = (num << 7) + (c & 0x7F)
                if not (c & 0x80):
                    break

        return num, counter

    def __init__(self, file_name):
        self.tempo = 120
        self.file_name = file_name
        file = None
        try:
            file = open(self.file_name, 'rb')
            if file.read(4) != b'MThd': raise Exception('Not a MIDI file')
            size = struct.unpack('>i', file.read(4))[0]
            if size != 6: raise Exception('Unusual MIDI file with non-6 sized header')
            self.format = struct.unpack('>h', file.read(2))[0]
            self.track_count = struct.unpack('>h', file.read(2))[0]
            self.time_division = struct.unpack('>h', file.read(2))[0]
        finally:
            if file:
                file.close()

    def read_track(self, track_num=1):
        file = None
        try:
            file = open(self.file_name, 'rb')
            if file.read(4) != b'MThd': raise Exception('Not a MIDI file')
            size = struct.unpack('>i', file.read(4))[0]
            if size != 6: raise Exception('Unusual MIDI file with non-6 sized header')
            self.format = struct.unpack('>h', file.read(2))[0]
            self.track_count = struct.unpack('>h', file.read(2))[0]
            self.time_division = struct.unpack('>h', file.read(2))[0]

            # Now to fill out the arrays with the notes
            tracks = []
            for i in range(0, self.track_count):
                tracks.append([])

            for nn, track in enumerate(tracks):
                abs_time = 0.

                if file.read(4) != b'MTrk': raise Exception('Not a valid track')
                size = struct.unpack('>i', file.read(4))[0]

                # To keep track of running status
                last_flag = None
                while size > 0:
                    delta, size = self.read_variable_length(file, size)
                    delta /= float(self.time_division)
                    abs_time += delta

                    size -= 1
                    flag = self.read_byte(file)
                    # Sysex messages
                    if flag == 0xF0 or flag == 0xF7:
                        # print "Sysex"
                        while True:
                            size -= 1
                            if self.read_byte(file) == 0xF7: break
                    # Meta messages
                    elif flag == 0xFF:
                        size -= 1
                        type = self.read_byte(file)
                        if type == 0x2F:  # end of track event
                            self.read_byte(file)
                            size -= 1
                            break
                        length, size = self.read_variable_length(file, size)
                        message = file.read(length)
                        # if type not in [0x0, 0x7, 0x20, 0x2F, 0x51, 0x54, 0x58, 0x59, 0x7F]:
                        if type == 0x51:  # qpm/bpm
                            # http://www.recordingblogs.com/sa/Wiki?topic=MIDI+Set+Tempo+meta+message
                            self.tempo = 6e7 / struct.unpack('>i', b'\x00' + message)[0]
                    # MIDI messages
                    else:
                        if flag & 0x80:
                            type_and_channel = flag
                            size -= 1
                            param1 = self.read_byte(file)
                            last_flag = flag
                        else:
                            type_and_channel = last_flag
                            param1 = flag
                        type = ((type_and_channel & 0xF0) >> 4)
                        channel = type_and_channel & 0xF
                        if type == 0xC:  # detect MIDI program change
                            continue
                        size -= 1
                        param2 = self.read_byte(file)

                        # detect MIDI ons and MIDI offs
                        if type == 0x9:
                            note = Note(channel, param1, param2, abs_time)
                            if nn == track_num:
                                track.append(str(note).split())

                        elif type == 0x8:
                            for note in reversed(track):
                                if note.channel == channel and note.pitch == param1:
                                    note.duration = abs_time - note.start
                                    break

        finally:
            if file:
                file.close()

        return self.parse_into_song(tracks[track_num])

    def parse_into_song(self, track):
        notes = {}
        song = []
        last2 = 0

        def getnote(q):
            for x in q.keys():
                if q[x] > 0:
                    return x
            return None

        for nn in track:
            start, stop = float(nn[2]), float(nn[3])

            if start != stop:  # note ends because of NOTE OFF event
                if last2 > -1 and start - last2 > 0:
                    song.append(('r', getdur(last2, start)))
                song.append((nn[0].lower(), getdur(start, stop)))
                last2 = stop
            elif float(nn[1]) == 0 and notes.get(nn[0].lower(),
                                                 -1) >= 0:  # note ends because of NOTE ON with velocity = 0
                if last2 > -1 and notes[nn[0].lower()] - last2 > 0:
                    song.append(('r', getdur(last2, notes[nn[0].lower()])))
                song.append((nn[0].lower(), getdur(notes[nn[0].lower()], start)))
                notes[nn[0].lower()] = -1
                last2 = start
            elif float(nn[1]) > 0 and notes.get(nn[0].lower(), -1) == -1:  # note ends because of new note
                old = getnote(notes)
                if old != None:
                    if notes[old] != start:
                        song.append((old, getdur(notes[old], start)))
                    notes[old] = -1
                elif start - last2 > 0:
                    song.append(('r', getdur(last2, start)))
                notes[nn[0].lower()] = start
                last2 = start

        return song


def getdur(a, b):
    """Calculate note length for PySynth"""
    return 4 / (b - a)


try:
    import re
except ImportError:
    import ure as re

# try:
#     from rtttl import RTTTL
# except ImportError:
#     RTTTL = None

SAMPLING_RATE = 1000
from pyb import delay

names = ("c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b")

A4 = 440
C0 = A4 * pow(2, -4.75)


def note_freq(note):
    n, o = note[:-1], int(note[-1])
    index = names.index(n)
    return int(round(pow(2, (float(o * 12 + index) / 12.0)) * C0, 2))


def isplit(iterable, sep=None):
    r = ''
    for c in iterable:
        r += c
        if sep is None:
            if not c.strip():
                r = r[:-1]
                if r:
                    yield r
                    r = ''
        elif r.endswith(sep):
            r = r[:-len(sep)]
            yield r
            r = ''
    if r:
        yield r


class BuzzerPlayer(object):

    def __init__(self, pin="P8", callback=None):

        self.buzzer_pin = PWM(pin, freq=10000, width=0)
        self.callback = callback

    def from_file(self, filename, chunksize=5):
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(chunksize)
                if chunk:
                    for b in chunk:
                        yield chr(b)
                else:
                    break

    def play_nokia_tone(self, song, tempo=None, transpose=6, name="unkown"):

        pattern = "([0-9]*)(.*)([0-9]?)"

        def tune():
            for item in isplit(song):
                if item.startswith('t'):
                    _, tempo = item.split('=')
                    yield tempo
                    continue
                match = re.match(pattern, item)
                duration = match.group(1)
                pitch = match.group(2)
                octave = match.group(3)

                if pitch == "-":
                    pitch = "r"
                if pitch.startswith("#"):
                    pitch = pitch[1] + "#" + pitch[2:]
                dotted = pitch.startswith(".")
                duration = -int(duration) if dotted else int(duration)
                yield (pitch + octave, int(duration))

        t = tune()
        if not tempo:
            tempo = next(t)
        self.play_tune(tempo, t, transpose=transpose, name=name)

    def play_melody(self, melodyname=None, transpose=6):
        """
        Проигрывает предустановленную мелодию из списка
        :param melodyname: имя мелодии
        :param transpose: транспонирование мелодии (от 1 до 7)
        """
        #  вдохновение http://forum.amperka.ru/threads/%D0%9C%D0%B5%D0%BB%D0%BE%D0%B4%D0%B8%D0%B8-%D0%B4%D0%BB%D1%8F-%D0%BF%D1%8C%D0%B5%D0%B7%D0%BE%D0%BF%D0%B8%D1%89%D0%B0%D0%BB%D0%BA%D0%B8.272/page-2
        songs = dict(
            pink_panther="t=90 8#g1 2a1 8b1 2c2 8#g1 8a1 8b1 8c2 8f2 8e2 8a1 8c2 8e2 2#d2 16d2 16c2 16a1 8g1 1a1 8#g1 2a1 8b1 2c2 8#g1 8a1 8b1 8c2 8f2 8e2 8c2 8e2 8a2 1#g2 8#g1 2a1 8b1 2c2 16#g1 8a1 8b1 8c2 8f2 8e2 8a1 8c2 8e2 2#d2 8d2 16c2 16a1",
            imperial_march="t=100 4e1 4e1 4e1 8c1 16- 16g1 4e1 8c1 16- 16g1 4e1 4- 4b1 4b1 4b1 8c2 16- 16g1 4#d1 8c1 16- 16g1 4e1 8-",
            starwars="t=100 8#c1 8#c1 16#c1 2#f1 2#c2 8b1 16#a1 8#g1 2#f2 4#c2 8b1 16#a1 8#g1 2#f2 4#c2 8b1 16#a1 8b1 2#g1 8#c1 8#c1 16#c1 2#f1 2#c2 8b1 16#a1 8#g1 2#f2 4#c2 8b1 16#a1 8#g1 2#f2 4#c2 8b1 16#a1 8b1 2#g1 4#c1 16#c1 2#d1 8#c2 8b1 8#a1 8#g1 8#f1 16#f1 8#g1 16#a1 4#g1",
            pulp_fiction="t=113 16f1 16f1 16f1 16f1 16f1 16f1 16f1 16f1 16a1 16a1 16a1 16a1 16#a1 16#a1 16#a1 16#a1 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16f1 16e2 16e2 16e2 16e2 16#c2 16#c2 16#c2 16#c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2 16c2",
            agent007="t=100 16#d1 32f1 32f1 16f1 8f1 16#d1 16#d1 16#d1 16#d1 32#f1 32#f1 16#f1 8#f1 16f1 16f1 16f1 16#d1 32f1 32f1 16f1 8f1 16#d1 16#d1 16#d1 16#d1 32#f1 32#f1 16#f1 8#f1 16f1 16e1 16#d1 16#d2 2d2 16#a1 16#g1 2#a1",
            american_pie="t=125 2g2 4f2 8f2 8f2 8e2 32d2 16- 32- 8c2 8d2 4- 8g2 32g2 16- 32- 32g2 16- 32- 32g2 16- 32- 32g2 16- 32- 32g2 16- 32- 32f2 16- 32- 32f2 16- 32- 32f2 16- 32- 32f2 16- 32- 8e2 32d2 16- 32- 8c2 8g1",
            sex_bomb="t=125 8c2 8- 4a1 8c2 8- 4a1 8- 4d2 8c2 4e2 16c2 16d2 4e2 4c2 8c2 8c2 8c2 8c2 8c2 8c2 8a1 8c2 8a1 8a1 8g1 4a1 8c2 8- 4a1 8c2 8- 4a1 8- 4d2 8c2 4e2 4c2 8- 4c2 8a1 8c2 8a1 8g1 16- 8#g1 16- 4a1",
            colors_of_the_night="t=80 2#g2 8c2 2#c2 4g2 8#g2 4#a2 8c2 8#a1 2#g1 2f2 8#g1 2g1 8f2 16e2 8f2 2g2 2#g2 8c2 2#c2 4g2 8#g2 4#a2 8c2 8#a1 2#g1 2f2 8#g1 2g1 8f2 8e2 8f2 2g2 8#a1 8c2 8c2 4c2 4#c2 2#a2 8#a1 8#a2 8#a2 4#a2 4c2 4#a2 8#g2 4g2 2#g2 8c2 8c2 4c2",
            boomer="t=100 8e2 4g2 4- 8g2 4e2 4- 8a2 8g2 8a2 8g2 8a2 8g2 8a2 8g2 8a2 4b2",
            boomer2="t=200 4a1 4g1 4f1 4e1 4d1 4- 4a1 4g1 4f1 4e1 4d1 4- 4a1 4g1 4f1 4- 4#a1 4a1 4g1 4f1 4e1 4- 4#a1 4a1 4g1 4f1 4e1",
            ddt_fall="t=100 8e2 16c2 8b1 8a1 8e2 8b1 16b1 8c2 8b1 2a1 8a1 16a1 8a1 8a1 8a1 8a1 16#c2 8e2 8g2 2f2 8d2 16d2 8d2 8d2 8g2 8f2 8e2 8d2 8e2 8e2 16e2 8d2 8c2 4a1 8- 8b1 8b1 8g2 8f2 8e1 16e1 8e2 8c2 8b1 2a1",
            sailormoon="t=100 4e2 8b1 4e2 4#f2 8g2 4a2 8g2 4#f2 4e2 8d2 1c2 1d2 4e2 8b1 4e2 4#f2 8g2 4a2 8g2 4#f2 4e2 8#f2 1g2 1a2 4- 4b2 8#g2 4a2 8b2 4c3 8a2 4e2 8g2 2#f2 32- 8#f2 8d3 8c3 1b2 4- 4a2 8#f2 4g2 8a2 4c3 8b2 4#d3 8b2 8a2 8#f2",
            mozart='t=240 8a2 16#g2 16- 8#g2 8- 8a2 16#g2 16- 8#g2 8- 8a2 16#g2 16- 4#g2 8.e3 4- 16- 8e3 16#d3 16- 8#c3 8- 8#c3 16b2 16- 8a2 8- 16.a2 32- 16#g2 16- 8#f2 8- 8#f2 4- 8- 16.#g2 32- 16.#f2 32- 8#f2 8- 8#g2 16#f2 16- 8#f2 8- 8#g2 16#f2 16- 4#f2 8#d3 4- 8- 8#d3 8#c3 8c3 8- 8c3 8a2 16.#g2 8- 32- 8#g2 8#f2 8e2 8- 8e2 4- 8- 8e3 16#d3 16- 4#d3 4#f3 4c3 4#d3 4#c3 4#g2 4- 16.e3 32- 16#d3 16- 4#d3 4#f3 4c3 4#d3 4#c3 4e3 8#d3 8#c3 8b2 8a2 1#g2 1g2 2#g2 4- 16#g1 16- 16#g1 16- 2#g1 4- 16#g1 16- 16#g1 16- 2#g1 4- 16#g1 16- 16#g1 16- 8#g1 8- 16#g1 16- 16#g1 16- 8#g1 8- 16#g1 16- 16#g1 16- 2#g1',
            tmnt="t=100 4- 8g2 8a2 8g2 8a2 8g2 16a2 8g2 16- 8a2 8#a2 8c3 8#a2 8c3 8#d3 16c3 8#a2 16- 8c3 8f3 8f3 8#d3 8f3 8#g3 16f3 8#d3 16- 8f3 16c3 16c3 16c3 16c3 8#a2 4c3 16c3 16c3 16c3 8c3",
            mortalkombat="t=140 8a1 8a1 8c2 8a1 8d2 8a1 8e2 8d2 8c2 8c2 8e2 8c2 8g2 8c2 8e2 8c2 8g1 8g1 8b1 8g1 8c2 8g1 8d2 8c2 8f1 8f1 8a1 8f1 8c2 8f1 8c2 8b1",
            ussr="t=100 8g1 4c2 8g1 16a1 4b1 8e1 8e1 4a1 8g1 16f1 4g1 8c1 8c1 4d1 8d1 8e1 4f1 8f1 8g1 4a1 8b1 8c2 4d2 8- 8g1 4e2 8d2 16c2 4d2 8b1 8g1 4c2 8b1 16a1 4b1 8e1 8e1 4a1 8g1 8f1 4g1 8c1 8c1 4c2 8b1 16a1 4g1",
            bach_fuga="t=100 8a1 8e1 8b1 8e1 8c2 8e1 8a1 8e1 8b1 8e1 8c2 8e1 8d2 8e1 8b1 8e1 8c2 8e1 8d2 8e1 8e2 8e1 8c2 8e1 8d2 8e1 8e2 8e1 8f2 8e1 8d2 8e1 8e2 8e1 8c2 8e1 8d2 8e1 8b1 8e1 8c2 8e1 8a1 8e1 8b1 8e1 8#g1 8e1 4a1",
            fur_elise="t=140 8e2 8#d2 8e2 8#d2 8e2 8b1 8d2 8c2 4a1 8- 8c1 8e1 8a1 4b1 8- 8e1 8#g1 8b1 4c2 8- 8e1 8e2 8#d2 8e2 8#d2 8e2 8b1 8d2 8c2 4a1 8- 8c1 8e1 8a1 4b1 8- 8e1 8c2 8b1 4a1",
            katyusha="t=100 4d2 8e2 4f2 8d2 8f2 8f2 8e2 8d2 4e2 4a1 4e2 8f2 4g2 8e2 8g2 8g2 8f2 8e2 2d2 4a2 4d3 4c3 8d3 8c3 8#a2 8#a2 8a2 8g2 4a2 4d2 8- 4#a2 8g2 4a2 8- 8f2 8g2 8g2 8f2 8e2 4d2 4-",
            podmoskovnie_vechera="t=100 8d1 8f1 8a1 8f1 4g1 8f1 8e1 4a1 4g1 4d1 4- 8f1 8a1 8c2 8c2 4d2 8c2 8#a1 4a1 4- 4b1 4#c2 8e2 8d2 4a1 4- 8e1 8d1 8a1 8g1 4#a1 4- 8c2 8#a1 4a1 8g1 8f1 4a1 4g1 2d1",
            brigada="t=112 16#g1 16#d2 16#c2 16e2 8#d2 16#d2 16b1 16#c2 16#d2 8e2 16#d2 2#g1 16#g1 16#d2 16#c2 16e2 4#d2 16#c2 16b1 8#a1 16b1 2#f1 16#g1 16#d2 16#c2 16e2 8#d2 16#d2 16b1 16#c2 16#d2 8e2 16#d2 4#f1 16- 16- 8#g1 16#a1 16b1 8#c2 16b1 4#g1 16- 16#g1 16b1 16#a1 16#g1 8#f1 2#g1",

        )
        if melodyname:
            self.play_nokia_tone(songs[melodyname], transpose=transpose, name=melodyname)
        else:
            print('Допустимые имена мелодий:')
            for idx, name in enumerate(songs.keys(), 1):
                print(f' {idx}\t{name}')

    def tone(self, hz: int, duration=0, duty=30):
        """
        Проигрывает звук с заданной частотой определённое время ы мс
        :param hz: частота в герцах
        :param duration: время звучания в милисекундах
        :param duty: влияет на громкость сигнала. 1-25 сигнал увеличивается, затем снова затухает до 26-50 и так далее
        """
        self.buzzer_pin.frequency(int(hz))  # change frequency for change tone
        self.buzzer_pin.pulse_width_percent(duty)
        delay(duration)
        self.buzzer_pin.value(0)

        if callable(self.callback):
            self.callback(hz)

    def play_tune(self, tempo, tune, transpose=0, name="unknown"):

        print("\n== playing '%s' ==:" % name)
        full_notes_per_second = float(tempo) / 60 / 4
        full_note_in_samples = SAMPLING_RATE / full_notes_per_second

        for note_pitch, note_duration in tune:
            duration = int(full_note_in_samples / note_duration)

            if note_pitch == "r":
                self.tone(0, duration, 0)
            else:
                freq = note_freq(note_pitch)
                if transpose: freq *= 2 ** transpose
                print("%s " % note_pitch, end="")
                self.tone(freq, duration, 30)

        self.tone(0, 0, 0)

    def play_midi(self, filename, track=1, transpose=6):
        midi = MidiFile(filename)
        tune = midi.read_track(track)
        self.play_tune(midi.tempo, tune, transpose=transpose, name=filename)

    # if RTTTL:
    #     def play_rtttl(self, input):
    #         tune = RTTTL(input)
    #         for freq, msec in tune.notes():
    #             self.tone(freq, msec)
