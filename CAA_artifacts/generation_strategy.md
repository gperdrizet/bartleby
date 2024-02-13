# Generation strategy

Skylines uses an in-house, *de novo* trained convolutional neural network. Both the dataset and model architecture were custom designed and built to illustrate mechanical 'imagination'.

Generation uses a convolutional neural network adversarially trained on 261 real images of city skylines.

## 1. Data source

Images of city skylines were manually curated from Google image search. The resulting set of images were then scaled to 1024 x 1024 pixels and mirrored to maximize dataset diversity.

## 2. Training

Training was conducted via a generative adversarial strategy. Two models were constructed: one for generation and one for discrimination. The discriminator model takes an image as input and returns a 'yes' or 'no' answer to the question, 'Did this image come from the dataset of real images?'. The generator takes a list of 100 random numbers as input and uses convolution to convert them into a 1024 x 1024 pixel RGB image. The training loop is as follows:

1. The generator is fed a set of randomly generated input points and creates an output image from them.
2. A generated image or a real skyline image is given to the discriminator model which scores how likely the image is to have come from the 'real' city skylines image set.
3. The discriminator's neural net is updated to give better answers - i.e. it is penalized for being wrong and rewarded for being right.
4. The generator's neural net is updated to make better fakes - i.e. if the discriminator was 'fooled' by the generated image the generator is rewarded and if not, it is penalized.

## 3. Results

The result is a very large and complex equation which takes a list of 100 numbers and does calculations on them to generate three new sets of 1024 x 1024 numbers. The resulting sets of numbers resemble a city skyline when formatted and displayed as an RGB image.
