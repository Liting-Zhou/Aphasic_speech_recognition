import pandas as pd

def clean_dataset(file_path):
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return
    
    # get total number of rows
    num_rows = df.shape[0]
    print(f"Total rows: {num_rows}") # 129295

    df['difference'] = df.iloc[:, 1] - df.iloc[:, 0]
    # get the total duration
    sum_duration = df['difference'].sum()/1000/60/60 # 143 hours
    print(f"The total duration of all audios: {sum_duration} hours")

    # get the rows with differences larger than 30,000 and empty transcripts
    large_differences = df[df['difference'] > 30000]
    empty_transcripts = df[df['transcriptions'].isnull() | (df['transcriptions'].str.strip() == '')]

    if not large_differences.empty:
        num_large_differences = large_differences.shape[0]
        print(f"Number of rows with differences larger than 30,000: {num_large_differences}")
        # print("Differences larger than 30,000 found in the following rows:")
        # print(large_differences)
    else:
        print("No differences larger than 30,000 found.")
    
    if not empty_transcripts.empty:
        num_empty_transcripts = empty_transcripts.shape[0]
        print(f"Number of rows with empty_transcripts: {num_empty_transcripts}")
    else:
        print("No empty transcripts found.")

    rows_to_drop = pd.concat([large_differences, empty_transcripts]).drop_duplicates()
    if not rows_to_drop.empty:
        num_rows_dropped = rows_to_drop.shape[0]
        print(f"Dropping {num_rows_dropped} rows due to large differences or empty transcripts.")
        df = df.drop(rows_to_drop.index)
    else:
        print("No rows to drop based on the given criteria.")
    
    df.to_csv(file_path, index=False)

    # get total number of rows after cleaning
    num_rows_cleaned = df.shape[0]
    print(f"Total rows after cleaning: {num_rows_cleaned}") # 128334

    # get the total duration after cleaning
    sum_duration_cleaned = df['difference'].sum()/1000/60/60 # 139 hours
    print(f"The total duration of all audios after cleaning: {sum_duration_cleaned} hours")



def main():
    csv_file = "../data_processed/clean_dataset.csv"
    clean_dataset(csv_file)

if __name__ == "__main__":
    main()