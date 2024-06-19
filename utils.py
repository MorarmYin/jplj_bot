import os

def create_dir():
    # Create directories if they don't exist
    os.makedirs("imgs/videos", exist_ok=True)
    os.makedirs("imgs/at", exist_ok=True)
    os.makedirs("imgs/owner", exist_ok=True)

def contains_substring(main_string, sub_string):
    return sub_string in main_string