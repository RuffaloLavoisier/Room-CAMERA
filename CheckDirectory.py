import os

def createFolder(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
