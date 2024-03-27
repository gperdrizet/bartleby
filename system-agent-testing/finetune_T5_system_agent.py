import os
import evaluate
import pandas as pd
import numpy as np
from datasets import Dataset
from transformers import AutoTokenizer, DataCollatorForSeq2Seq, AutoModelForSeq2SeqLM, Seq2SeqTrainingArguments, Seq2SeqTrainer

def preprocess_function(examples):
    '''Helper function to preprocess text in HF dataset for summarization'''

    inputs = ["summarize: " + doc for doc in examples["text"]]
    model_inputs = tokenizer(inputs, max_length=1024, truncation=True)

    labels = tokenizer(text_target=examples["summary"], max_length=128, truncation=True)

    model_inputs["labels"] = labels["input_ids"]

    return model_inputs

def compute_metrics(eval_pred):
    '''Helper function to evaluate predictions using rouge metric'''

    predictions, labels = eval_pred
    decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    result = rouge.compute(predictions=decoded_preds, references=decoded_labels, use_stemmer=True)

    prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in predictions]
    result["gen_len"] = np.mean(prediction_lens)

    return {k: round(v, 4) for k, v in result.items()}

if __name__ == '__main__':

    # Set HuggingFace cache
    os.environ['HF_HOME'] = '/mnt/fast_scratch/huggingface_transformers_cache'

    # Set visible GPUs
    os.environ['CUDA_VISIBLE_DEVICES']='1'

    # Load dataset from csv
    dataset_df = pd.read_csv('NL_commands_dataset.complete.csv', keep_default_na=False)

    # Convert to dict
    dataset = dataset_df.to_dict(orient='records', index='false')

    # Convert to HF dataset
    dataset = Dataset.from_list(dataset)

    # Do train test split
    dataset = dataset.train_test_split(test_size=0.2)

    # Sanity check
    print(dataset["train"][0])

    # Tokenize the dataset
    checkpoint = "google-t5/t5-base"
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    tokenized_dataset = dataset.map(preprocess_function, batched=True)

    # Create batcher
    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=checkpoint)

    # Set eval metric
    rouge = evaluate.load("rouge")

    # Load model
    model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint, device_map='cpu')

    # Set training args
    training_args = Seq2SeqTrainingArguments(
        output_dir="../bartleby/hf_cache/2024-03-26_T5-base-system-agent",
        evaluation_strategy="epoch",
        learning_rate=1e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        weight_decay=0.01,
        save_total_limit=3,
        num_train_epochs=1600,
        predict_with_generate=True,
        #fp16=True,
        #push_to_hub=True,
    )

    # Instantiate trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["test"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    model.save_pretrained('../bartleby/hf_cache/2024-03-26_T5-base-system-agent')
