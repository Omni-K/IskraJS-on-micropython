"""
Модуль для пьезогенератора
Вдохновлён https://github.com/fruch/micropython-buzzer
"""
__author__ = "Nikolay Putko"
__copyright__ = "Nikolay Putko, 2022 onwards."
__license__ = "MIT https://opensource.org/licenses/MIT (as used by MicroPython)."
__version__ = "0.3.0"
__repo__ = "https://github.com/Omni-K/Iskra_JS_micropython"

from math import pow

import struct
import sys
import logging

logger = logging.getLogger(__name__)


class Note(object):
    "Represents a single MIDI note"

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
                        logger.debug("Meta: %s", str(type))
                        length, size = self.read_variable_length(file, size)
                        message = file.read(length)
                        # if type not in [0x0, 0x7, 0x20, 0x2F, 0x51, 0x54, 0x58, 0x59, 0x7F]:
                        logger.debug("%s %s", length, message)
                        if type == 0x51:  # qpm/bpm
                            # http://www.recordingblogs.com/sa/Wiki?topic=MIDI+Set+Tempo+meta+message
                            self.tempo = 6e7 / struct.unpack('>i', b'\x00' + message)[0]
                            logger.debug("tempo = %sbpm", self.tempo)
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
                            logger.debug("program change, channel %s = %s", channel, param1)
                            continue
                        size -= 1
                        param2 = self.read_byte(file)

                        # detect MIDI ons and MIDI offs
                        if type == 0x9:
                            note = Note(channel, param1, param2, abs_time)
                            if nn == track_num:
                                logger.debug("%s", note)
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
    "Calculate note length for PySynth"
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

    def __init__(self, pin="X8", timer_id=1, channel_id=1, callback=None, platform=None):

        if not platform:
            platform = sys.platform

        self.platform = platform
        print(self.platform)

        from machine import Pin
        from pwm import PWM
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

    def tone(self, hz: int, duration=0, duty=30):
        self.buzzer_pin.frequency(int(hz))  # change frequency for change tone
        self.buzzer_pin.pulse_width_percent(30)
        delay(duration)

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

    if MidiFile:
        def play_midi(self, filename, track=1, transpose=6):
            midi = MidiFile(filename)
            tune = midi.read_track(track)
            self.play_tune(midi.tempo, tune, transpose=transpose, name=filename)

    # if RTTTL:
    #     def play_rtttl(self, input):
    #         tune = RTTTL(input)
    #         for freq, msec in tune.notes():
    #             self.tone(freq, msec)
