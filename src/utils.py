import logging
import os


def read_file(path: str) -> str:
    """Reads in the txt file at the fiven path

    The method reads a .txt file from the given path and
    returns it as a string

    Args:
        path (str): A path to a .txt file,

    Returns:
        str: The txt file or None if the file is not found
    """

    # Set the root path constant for all methods
    root_path: str = os.path.dirname(os.path.abspath(__file__))

    try:
        file_path = os.path.join(root_path, path)
        with open(file_path, "r") as file:
            return file.read()

    except FileNotFoundError:
        logging.error(f"File not found at {path}")
        return None


if __name__ == "__main__":
    print(read_file("../prompts/self_refine/system_refine.txt"))
