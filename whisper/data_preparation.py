# based on https://huggingface.co/blog/fine-tune-whisper
# usage example: python3 data_preparation.py "small"

import argparse
from transformers import WhisperFeatureExtractor
from transformers import WhisperTokenizer
import soundfile as sf
from datasets import Dataset, DatasetDict, Audio,load_from_disk
import pandas as pd
import os 

def process_dataset(model_size):
    # map model size to the corresponding model name
    model_map = {
        "tiny": "openai/whisper-tiny",
        "small": "openai/whisper-small",
        "medium": "openai/whisper-medium",
        "large": "openai/whisper-large-v3"
    }

    if model_size not in model_map:
        raise ValueError("Model size must be one of 'tiny', 'small', 'medium', or 'large'.")

    model_name = model_map[model_size]

    # load dataset
    csv_file_path = '../../data_processed/dataset_splitted.csv'
    df = pd.read_csv(csv_file_path)

    columns_to_drop = ['mark_start', 'mark_end', 'name','sex','age','file','WAB_AQ','aphasia_type','WAB_AQ_category','fluency_speech','original_file_length','difference','name_extracted_from_filename','name_unique_speaker']
    df = df.drop(columns=columns_to_drop)
    dataset = Dataset.from_pandas(df)

    dataset_dict=DatasetDict()
    dataset_dict["train"] = dataset.filter(lambda example: example["split"] == "train")
    dataset_dict["eval"] = dataset.filter(lambda example: example["split"] == "validation")
    dataset_dict["test"] = dataset.filter(lambda example: example["split"] == "test")

    print("Data splitting finished.")

    # directory to save the processed audio dataset
    processed_audio_data_path = f'../../data_processed/processed_audio_dataset_{model_size}'

    # list to keep track of missing audio files
    missing_files = []

    def load_audio(batch):
        audio_file_path = os.path.join("../../data_processed/audios", batch["folder_name"], batch["file_cut"])
        # check if the file exists
        if os.path.exists(audio_file_path):
            try:
                audio, sample_rate = sf.read(audio_file_path)
                batch["audio"] = {"array": audio, "sampling_rate": sample_rate}
            except Exception as e:
                print(f"Error loading {audio_file_path}: {e}")
                batch["audio"] = None
        else:
            print(f"File not found: {audio_file_path}")
            missing_files.append(audio_file_path)
            batch["audio"] = None  # assign None for missing audio files
        
        return batch

    # check if the processed dataset already exists
    if os.path.exists(processed_audio_data_path):
        dataset_dict = load_from_disk(processed_audio_data_path)
        print("Loaded existing audio dataset!")
    else:
        dataset_dict = dataset_dict.map(load_audio)
        dataset_dict.save_to_disk(processed_audio_data_path)
        print("Processed audio dataset saved.")

    # save the missing files to a CSV
    if missing_files:
        missing_files_df = pd.DataFrame(missing_files, columns=["missing_file_path"])
        missing_files_df.to_csv("../../data_processed/missing_audio_files.csv", index=False)
        print("Missing audio files saved to 'missing_audio_files.csv'.")
    else:
        print("No missing audio files detected.")

    feature_extractor = WhisperFeatureExtractor.from_pretrained(model_name)
    tokenizer = WhisperTokenizer.from_pretrained(model_name, language="English", task="transcribe")

    def prepare_dataset(batch):
        audio = batch["audio"]
        if audio is None or not audio["array"]:
            print(f"Invalid or empty audio data for batch {batch}")
            print(f"Audio is None or empty in file: {batch['file_cut']}")
            batch["input_features"] = None
            batch["labels"] = None
            return batch
        
        try:
            # compute log-Mel input features from input audio array
            batch["input_features"] = feature_extractor(audio["array"], sampling_rate=audio["sampling_rate"]).input_features[0]
            # encode target text to label ids
            batch["labels"] = tokenizer(batch["transcriptions"]).input_ids
        except Exception as e:
            print(f"Error processing audio: {e}")
            batch["input_features"] = None
            batch["labels"] = None
        return batch

    # prepare the datasets
    dataset_dict = dataset_dict.map(prepare_dataset, num_proc=8)

    print("finished preparing dataset")

    # save the dataset_dict
    dataset_dict_path = f'../../data_processed/dataset_dict_{model_size}'
    dataset_dict.save_to_disk(dataset_dict_path)
    print("Dataset_dict saved to disk.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare a dataset with Whisper model.")
    parser.add_argument("model_size", type=str, choices=["tiny", "small", "medium", "large"],
                        help="Size of the Whisper model to use.")
    
    args = parser.parse_args()
    process_dataset(args.model_size)