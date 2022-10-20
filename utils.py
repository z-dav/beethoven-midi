import glob
import numpy as np
#import sys, os
import json
import music21
from music21 import note, stream
import random
import re
import torch
from pathlib import Path

from collections import Counter
    
""" 
output:
int_to_vocab: dictionary converting integers to the vocab words
vocab_to_int: dictionary converting vocab words to integers
n_vocab: size of the vocabulary
in_text: input text
out_text: the expected output of the model
"""
def make_vocabulary(text, batch_size, seq_size):

    word_counts = Counter(text)
    sorted_vocab = sorted(word_counts, key=word_counts.get, reverse=True)
    int_to_vocab = {k: w for k, w in enumerate(sorted_vocab)}
    vocab_to_int = {w: k for k, w in int_to_vocab.items()}
    n_vocab = len(int_to_vocab)
    print(n_vocab)

    inputs = [vocab_to_int[w] for w in text]
    #num_batches = int(len(int_text) / (seq_size * batch_size))
    #inputs = int_text[:num_batches * batch_size * seq_size]
    ideal = np.zeros_like(inputs)
    print(len(inputs))
    
    ideal[:-1] = inputs[1:]
    ideal[-1] = inputs[0]
    return int_to_vocab, vocab_to_int, n_vocab, inputs, ideal

# Find all files in the given directory
def get_files(dir_name, pattern='*.mid', recursive=True):
    all_files = []  
    for name in glob.glob('{}/**/{}'.format(dir_name, pattern), recursive=True): 
        all_files.append(name)
        
    return all_files

# The output is a dictionary with all the training and test words
# with necessary dictionaries for converting to ints and back
# as well as lists of inputs and expected outputs
def get_data_from_files(data_dir, batch_size, seq_size):
    
    data = {'words':[], 'songs_lengths':{}, 'instruments':[], 'tempos':[], 'song_names':[]}
    test_in=[]
    test_out=[]
    train_in=[]
    train_out=[]
    
    all_files = get_files(data_dir, pattern="*.json", recursive=True)
    
    # read all files to memory
    for train_file in all_files:
        file_name = Path(train_file).stem
        data['song_names'].append(file_name)
        with open(train_file, 'r') as f:
            t_f = f.read()

            ## this is a json file so make it a dictionary
            track_notes = json.loads(t_f)
            
            data['instruments'].append(track_notes['key'])
            data['tempos'].append(track_notes['tempo'])
            #determine test and training sizes
            start = len(data['words'])
            length = len(track_notes['notes'])
            data['songs_lengths'][file_name] = length
            
            for note in track_notes['notes']:
                data['words'].append(note['word'])
                         
    int_to_vocab, vocab_to_int, n_vocab, inputs, ideal = make_vocabulary(data['words'], batch_size, seq_size)
    data['int_to_vocab'] = int_to_vocab
    data['vocab_to_int'] = vocab_to_int
    data['n_vocab'] = n_vocab
    data['train_set'] = []
    data['test_set'] = []
    data['ideal'] = ideal
    data['inputs'] = inputs
    
    data['words']
    
    # Re-structure the data out
    # build the test and training data sets
    current_place = 0
    test_song_starts = []
    lengths = []
    for song in data['songs_lengths'].keys():
        length = data['songs_lengths'][song]
        lengths.append(length)
        train_size = int(length * .8)
        test_size = length - train_size
        
        # The test data can come from anywhere up to test_size before the end of the data
        # This would be length-test_size which is the train_size
        test_start = random.randrange(train_size) + current_place
        test_in.extend(inputs[test_start:test_start + test_size])
        test_out.extend(ideal[test_start:test_start + test_size])
        
        test_song_starts.append(len(test_in))
        
        train_in.extend(inputs[current_place:test_start])
        train_in.extend(inputs[test_start+test_size:test_start+test_size+length])
        train_out.extend(ideal[current_place:test_start])
        train_out.extend(ideal[test_start+test_size:test_start+test_size+length])
        
        current_place += length
        
    padding = batch_size - len(test_in)%batch_size
    test_in.extend([0] * padding)
    test_out.extend([0] * padding)
    padding = batch_size - len(train_in)%batch_size
    train_in.extend([0] * padding)
    train_out.extend([0] * padding)
    
    data['test_in'] = torch.tensor(test_in)
    data['test_out'] = torch.tensor(test_out)
    data['train_in'] = torch.tensor(test_in)
    data['train_out'] = torch.tensor(test_out)
    
    data['test_in'] = np.reshape(data['test_in'], (batch_size, -1))
    data['test_out'] = np.reshape(data['test_out'], (batch_size, -1))
    data['train_in'] = np.reshape(data['train_in'], (batch_size, -1))
    data['train_out'] = np.reshape(data['train_out'], (batch_size, -1))
    
    return data, test_song_starts, lengths

def write_notes_model_json(notes_model, file_name):
    with open(file_name, 'w+') as f:
        f.write(json.dumps(notes_model))
    
    f.close()
    print("wrote", file_name)

def decode_words_to_notes(words_list, words_channel=1, words_program=0):

    times = {
        'breve' : 8,
        'whole' : 4,
        'half' : 2,
        'quarter': 1,
        'eighth' : .5,
        '16th' : .25,
        'zero' : .5,
        'complex': .5,
        
    }
    total_length = 0
    s = stream.Stream()
    #i = 0
    for note_word in words_list:
        note_word_parts = note_word.split('_')
        
            
        note_duration = times[note_word_parts[2]]
        note_name = '{}{}'.format(note_word_parts[0], note_word_parts[1])
        
        midi_note = music21.note.Note(note_name)
        midi_note.duration = music21.duration.Duration(note_duration)
        total_length += note_duration
        s.append(midi_note)
        
    return s, total_length

if __name__ == "__main__":
    pass