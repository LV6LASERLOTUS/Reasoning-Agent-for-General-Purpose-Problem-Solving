import logging

def read_file(path: str) -> str:
    """Reads in the txt file at the fiven path

    The method reads a .txt file from the given path and 
    returns it as a string

    Args:
        path (str): A path to a .txt file,

    Returns:
        str: The txt file or None if the file is not found
    """
    try:
        with open(path, 'r') as file:
            return file.read()
        
    except FileNotFoundError:
        logging.error(f'File not found at {path}')
        return None