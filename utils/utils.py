import pandas as pd
def load_excel_data(file_path: str, skiprows = 0):
    # Load the Excel file, skipping the first three rows
    df = pd.read_excel(file_path, skiprows=skiprows)
    return df

def load_excel_data_without_header(file_path: str):
    df = pd.read_excel(file_path, header=None)
    return df

def load_excel_sheet(file_path, sheet_name="Tous les films"):
    """
    Load a specific sheet from an Excel file.
    
    :param file_path: The path to the Excel file.
    :param sheet_name: The name of the sheet to load.
    :return: A pandas DataFrame containing the data from the specified sheet.
    """
    try:
        # Load the specified sheet into a pandas DataFrame
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df
    except Exception as e:
        print(f"An error occurred: {e}")
        return None