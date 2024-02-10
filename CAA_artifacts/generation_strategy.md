# Generation strategy

Generation is accomplished with an iterative '[exquisite corpse](https://www.moma.org/collection/terms/exquisite-corpse)'-style exchange between the human director and the machine director.

## Algorithm

### 1. Model startup

Model is loaded and initial prompt is read into chat buffer:

```text
'Continue the story in a surprising and interesting way.
It is morning, the sun is rising and it is very quiet.
The lamps are on and she rearranges them for hours.
She deals a deck of cards in silence.'
```

### 2. User input

Program waits for input from the human director. Once received, the new direction is appended to the chat buffer e.g.:

```text
Continue the story in a surprising and interesting way.
It is morning, the sun is rising and it is very quiet.
The lamps are on and she rearranges them for hours.
She deals a deck of cards in silence.'

human_director: She sweeps stage left, ignoring a knock at the door.
```

### 3. Generation

The contents of the chat buffer are tokenized to numerical inputs and sent to the model. The model calculates the 'most likely' next line based on the input and returns it. The return is un-tokenized back to human readable text. The chat buffer is updated:

```text
Continue the story in a surprising and interesting way.
It is morning, the sun is rising and it is very quiet.
The lamps are on and she rearranges them for hours.
She deals a deck of cards in silence.'

human_director: She sweeps stage left, ignoring a knock at the door.
machine_director: As far as I know, she never got to play with dolls.
```

Then the cycle repeats.

The model does not 'learn' from user input on-the-fly. This is a common misconception. The model itself is pretrained and static. It is a large and complex equation which takes a numerical input and does math to give a numerical output. The 'machine learning' happens when the model is trained during development on a large amount of human generated text. The training process determines exactly what mathematical operations need to be done on a given input to convert it into output which mimics the human generated text.
