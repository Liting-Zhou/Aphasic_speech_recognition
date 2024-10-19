from transformers import pipeline
import pandas as pd
import torch
import os

def transcribe_and_save(csv_path, audio_root, model_pipeline, detailed_csv):
    """
    Transcribe audio and save the predictions in a CSV file using the Hugging Face pipeline.
    """
    # Load the dataset CSV
    df = pd.read_csv(csv_path)
    test_rows = df[df['split'] == 'test']
    
    # Process each row in the test set
    first_write = True  # Ensures header is written once
    with open(detailed_csv, mode='a') as f:
        for index, row in test_rows.iterrows():
            file_name = row['file_cut']
            transcription = row['transcriptions']
            folder_name = row['folder_name']
            audio_path = os.path.join(audio_root, folder_name, file_name)

            if not os.path.exists(audio_path):
                print(f"Audio file {audio_path} not found")
                continue

            # Transcribe audio using the pipeline
            print(f"Transcribing {audio_path}")
            result = model_pipeline(audio_path)
            predicted_text = result['text']

            # Collect data for detailed CSV
            output_data = {
                "folder": folder_name,
                "file_name": file_name,
                "prediction": predicted_text,
                "reference": transcription
            }

            # Write data row-by-row to the CSV file
            output_df = pd.DataFrame([output_data])
            output_df.to_csv(f, mode='a', header=first_write, index=False)
            first_write = False

    print(f"Detailed results saved to {detailed_csv}")

def run_all_transcriptions(csv_path, audio_root, models, detailed_results_folder):
    """
    Run transcription for all models and save the results.
    """
    for model_name in models:
        torch.cuda.empty_cache()

        # Load the model pipeline
        model_pipeline = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            device="cuda:0" if torch.cuda.is_available() else "cpu"
        )

        # Transcribe and save results for this model
        detailed_csv = f"{detailed_results_folder}/detailed_{model_name}_results.csv"
        transcribe_and_save(csv_path, audio_root, model_pipeline, detailed_csv)

        torch.cuda.empty_cache()

# Main script to run the models and transcriptions
csv_path = "../data_processed/dataset_splitted.csv"
audio_root = "../data_processed/audios"
models = ["openai/whisper-medium", "openai/whisper-large", "openai/whisper-large-v2", "openai/whisper-large-v3"]
detailed_results_folder = "../data_processed/detailed_wer_results"

if not os.path.exists(detailed_results_folder):
    os.makedirs(detailed_results_folder)
    print(f"Directory '{detailed_results_folder}' created.")

run_all_transcriptions(csv_path, audio_root, models, detailed_results_folder)
