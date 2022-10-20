# beethoven-midi
This is my LSTM implementation of note prediction with output midi files for music generation

Most of this was written as a .ipynb for easier testing and experimentation.

# midis
This is the source data that is processed in encoder.ipynb

# beethoven_jsons
This is where the processed data to be read in later is stored. 
I did this because pre-processing using encoder.ipynb takes ~30mins, and this data can be read very quickly afterwards

# output_midis
Once my prediction is done, there are actually 2 different midi outputs. These are then combined into one file, 
since the notes are usually on different 'tracks' in the midi file (2 per source file which were separated)

# final_midis
Result of combination of output_midis. Listen in! They aren't great, but at least there's an attempt at music!
