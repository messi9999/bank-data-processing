import pandas as pd
def load_excel_data(file_path: str, skiprows = 0):
    # Load the Excel file, skipping the first three rows
    df = pd.read_excel(file_path, skiprows=skiprows)
    return df

def load_excel_data_without_header(file_path: str):
    df = pd.read_excel(file_path, header=None)
    return df