# Bitsandbytes setup

2024-03-12 setup notes for bitsandbytes library used for model quantization

After some reading in the [github repo](https://github.com/TimDettmers/bitsandbytes), I noticed that the compile from source instructions mention using a different make target for kepler cards. See [here](https://github.com/TimDettmers/bitsandbytes/blob/main/compile_from_source.md). Following those instructions seems to work:

## 1. Install

```bash
git clone https://github.com/TimDettmers/bitsandbytes.git
cd bitsandbytes
CUDA_VERSION=118 make cuda11x_nomatmul_kepler
python setup.py install
```

Note: this install is for a pair of K80s, which are kepler cards, hence the _kepler. Also we are running cuda 11.4/11.4 but the CUDA_VERSION=118 is correct. Running make with CUDA_VERSION=114 does not work.

## 2. Test

```text
$ python -m bitsandbytes

++++++++++++++++++ LD_LIBRARY CUDA PATHS +++++++++++++++++++

++++++++++++++++++++++++++ OTHER +++++++++++++++++++++++++++
COMPILED_WITH_CUDA = True
COMPUTE_CAPABILITIES_PER_GPU = ['3.7', '3.7', '3.7', '3.7']
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++ DEBUG INFO END ++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Running a quick check that:
    + library is importable
    + CUDA function is callable


WARNING: Please be sure to sanitize sensible info from any such env vars!

SUCCESS!
Installation was successful!
```

## 3. GOTCHYAs

Now the benchmark runs, but we have two more issues. During benchmark runs with no quantization we get the following warning:

```text
W tensorflow/compiler/tf2tensorrt/utils/py_utils.cc:38] TF-TRT Warning: Could not find TensorRT
```

Trivial fix - not even sure why or what is looking or TensorRT, as far as I know, we are not using tensorflow at all. Removing tensorflow and TensorRT from the environment silences the warning. No apparent issues.

Eight bit quantization works with no issues, but four bit complains:

```text
bnb/nn/modules.py:226: UserWarning: Input type into Linear4bit is torch.float16, but bnb_4bit_compute_type=torch.float32 (default). This will lead to slow inference or training speed.
  warnings.warn(f'Input type into Linear4bit is torch.float16, but bnb_4bit_compute_type=torch.float32 (default). This will lead to slow inference or training speed.')
```

Fixed by adding the following to model load:

```text
bnb_4bit_compute_dtype=torch.float16
```

Note: this is different from the torch.bfloat16 suggested in the [huggingface docs](https://huggingface.co/docs/transformers/main_classes/quantization).

```text
huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
To disable this warning, you can either:
        - Avoid using `tokenizers` before the fork if possible
        - Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
Error named symbol not found at line 74 in file /mmfs1/gscratch/zlab/timdettmers/git/bitsandbytes/csrc/ops.cu
```

A little strange since we are not using multiprocessing for this benchmark - it should be a single job on a single GPU. Did sporadically see this warning when working on the parallel summarization benchmark too, never figured out what it was because it was not reliably reproducible.

Fixed by setting:

```text
os.environ['TOKENIZERS_PARALLELISM'] = 'true'
```
