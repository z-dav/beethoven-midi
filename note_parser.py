import ntpath
import json
import utils
import sys, os
import glob
import pretty_midi
import re
import music21


# Create dictionary consisting of all notes in midi stream
# Contains relevant information to rebuild a midi file later
def get_notes_list_from_stream(midi_stream, view='Note'):
    noteFilter=music21.stream.filters.ClassFilter(view)
    stream_notes = []
    for note in midi_stream.recurse().notesAndRests.addFilter(noteFilter):
        note_dict = {
           'music21_note': note,
           'nameWithOctave': note.nameWithOctave,
           'fullName': note.fullName,
           'word': '{}_{}_{}'.format(note.pitch.name, str(note.pitch.octave), str(note.duration.type)).lower(),
           'pitch': {
               'name': note.pitch.name,
               'microtone': str(note.pitch.microtone),
               'octave': str(note.pitch.octave),
               'step': str(note.pitch.step)
           },
           'duration':{
               'type': str(note.duration.type)
           }
        }
        stream_notes.append(note_dict)
    return stream_notes

# Get all of the notes from a track
def get_notes(track):
    track_stream = music21.midi.translate.midiTrackToStream(track)
    notes_all = get_notes_list_from_stream(track_stream)
    return notes_all


# Get all relevant information from midi files and return in separate tracks
def parse_midi_notes(midi_fname):
    all_tracks = []

    p_midi = pretty_midi.PrettyMIDI(midi_fname)
    mf=music21.midi.MidiFile()
    mf.open(midi_fname)
    mf.read()
    mf.close()

    channel_id = 1 
    for track in mf.tracks:
        if(track.hasNotes()):
            if(len(track.getProgramChanges())>0):
                track_model = {}
                hand = str(track.events[1].data).split('\'', 3)[1].replace(' ', '_').lower()
                
                notes_all = get_notes(track)
                music_21_notes = list(map(lambda x: x['music21_note'], notes_all))
                notes_events = []
                for m21_n in music_21_notes:
                    note_events_note = music21.midi.translate.noteToMidiEvents(m21_n) 
                    notes_events.extend(note_events_note)
                
                for i in range(len(notes_all)):
                    del notes_all[i]['music21_note']

                tempo = music21.midi.translate.midiEventsToTempo(notes_events)
                # ts = music21.midi.translate.midiEventsToTimeSignature(notes_events)

                i_name = pretty_midi.program_to_instrument_name(track.getProgramChanges()[0])
                track_model['hand'] = hand
                track_model['notes'] = notes_all
                track_model['name'] = i_name
                i_key = re.sub(r'[^A-Za-z ]', '', i_name)
                i_key = " ".join(i_key.split())
                track_model['key'] = i_key.replace(' ','_').lower()         
                track_model['program'] = track.getProgramChanges()[0]
                track_model['channel'] = channel_id
                track_model['tempo'] = tempo.number
                all_tracks.append(track_model)
                channel_id += 1
    
    return all_tracks


# This will get just the name of the file at the end of a path
def path_leaf(path):
    head, tail = ntpath.split(path)
    result = tail or ntpath.basename(head)
    return result.split(".", 1)[0]



all_midi = utils.get_files('midis')

session_dir = 'beethoven_jsons'
try:
    os.mkdir(session_dir)
except:
    pass

for midi_file in all_midi:
    print('reading file:', midi_file)
    notes_model_alltracks = parse_midi_notes(midi_file)
    for track_notes in notes_model_alltracks:
        track_dir = '{}/{}'.format(session_dir, track_notes['key'])
        try:
            os.makedirs(track_dir)
        except:
            pass
        track_file_name = "{}/{}-{}.json".format(track_dir, path_leaf(midi_file), track_notes['hand'])
        utils.write_notes_model_json(track_notes, track_file_name)