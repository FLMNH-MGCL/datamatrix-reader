import os
import sys
import subprocess
import pandas as pd
from pyzbar.pyzbar import decode
from PIL import Image
import time
import datetime
import re

old_new_paths = []
occurrences = dict()
SCAN_TIME = '30000'
valid_imgs = ['JPG', 'jpg', 'jpeg', 'JPEG']

class Bound:
    def __init__(self, lower, upper, genus, specificEpithet):
        self.lower = lower
        self.upper = upper
        self.genus = genus
        self.specificEpithet = specificEpithet
    
    def should_contain(self, num):
        if num < self.lower or num > self.upper:
            return False
        
        return True

#############################
# ******* MAIN CODE ******* #
def AskUsage():
    prompt = str(
            "This program will help to automate the renaming of specimen images by automatically finding and " \
            "decoding data matrices / barcodes in the images. On start, you will be prompted with whether or not " \
            "to view this help message. After which, the program will begin in 10 seconds. You will enter the path " \
            "to a folder containing the images of the digitized specimen. On a mac, you may simply drag the folder " \
            "into the terminal window. You will then have the option to run the program recursively (scanning all " \
            "images in all subfolders) or standard (scanning only in provided folder, no additional subfolders). " \
            "All changes to file names are temporarily saved, so please review the changes when prompted.\n\nYou will " \
            "have the chance to undo the program's renaming ONLY WHEN PROMPTED, so it is important to check the results " \
            "before closing / terminating the project. If you choose to undo, a log file will not be generated. If you realize " \
            "there is a mistake afterwards, you can use the log file for undoing the changes using the specific undo script."
        )
    wanted = input("\nDo you want to see the usage information?\n [1]yes\n [2]no\n --> ")
    if wanted == '1' or wanted == 'y' or wanted == 'yes':
        print(prompt)
        time.sleep(10)

def Log(path):
    global old_new_paths
    d = datetime.datetime.today()
    date = str(d.year) + '_' + str(d.month) + '_' + str(d.day)
    filename = path + 'DMREAD_SCRIPT_LOG_' + date

    count = ''
    num = 0
    while os.path.exists(filename + count + '.csv'):
        if num == 0:
            filename += '_'
        num += 1
        count = str(num)

    if num == 0:
        filename = filename + '.csv'
    else:
        filename = filename + count + '.csv'

    csv_file = open(filename, mode='w')
    csv_file.write('Old Path,New Path\n')
    for old_path,new_path in old_new_paths:
        csv_file.write(old_path + ',' + new_path + '\n')



def GetDirs(path):
    subdirectories = []
    for folder in sorted(os.listdir(path)):
        if os.path.isdir(path + folder):
            subdirectories.append(folder)
    return subdirectories


def GetImages(path):
    images = []
    for image in sorted(os.listdir(path)):
        if os.path.isfile(path + image) and image.split('.')[1] in valid_imgs:
            images.append(image)
    return images


def GetCR2s(path):
    cr2s = []
    for cr2 in sorted(os.listdir(path)):
        if os.path.isfile(path + cr2) and cr2.split('.')[1] == 'CR2':
            cr2s.append(cr2)
    return cr2s


def RecursiveProcessData(path):
    for dir in GetDirs(path):
        RecursiveProcessData(path + dir + '/')
    ProcessData(path)


def BarcodeRead(path):
    decoder = decode(Image.open(path))
    try:
        name = str(decoder[0].data)
    except:
        name = "nothing"
    return name


"""
takes path to image, scans matrix, returns new name
"""
def DMRead(path):
    global SCAN_TIME
    p = subprocess.Popen('cat ' + path + ' | dmtxread --stop-after=1 -m' + SCAN_TIME, shell=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return str(p.stdout.readline())

def ProcessData(path, range_data=None):
    print("\nWorking in... {}\n".format(path))
    
    global old_new_paths
    global occurrences

    genus = None
    species = None

    cr2s = GetCR2s(path)
    for image in GetImages(path):
        if range_data:
            # remove potential dupl indicators
            image_test = re.sub(r"\(\d+\)", "", image).strip()
            int_in_img = int(''.join(filter(str.isdigit, image_test)))
            
            should_skip = False
            for bound in range_data:
                if bound.should_contain(int_in_img):
                   should_skip = False

                   genus = bound.genus
                   species = bound.specificEpithet

                   break
                else:
                    should_skip = True
            
            if should_skip:
                continue

        # scanning
        ext = '.' + image.split('.')[1]
        arg = path + image

        new_name = BarcodeRead(arg)
        if "MGCL" not in new_name:
            print('Could not find barcode... Searching for Datamatrix...')
            new_name = DMRead(arg)
            if "MGCL" not in new_name:
                print('Could not find matrix in ' + image + '...')
                continue
    
        # Replace garbage characters read in
        new_name = str(new_name).replace("b\'", '').replace(' ', '_').replace('\'', '')

        new_name = new_name.replace("b\'", '').replace(' ', '_').replace('\'', '')

        # get and check specimen id
        scanned_id = int(new_name.split('_')[1])

        if genus is not None and species is not None:
            new_name += "_{}_{}".format(genus, species) 
        
        if "lateral" in new_name.lower() or "lat" in new_name.lower() or "_l" in new_name.lower():
            # Lateral
            new_name.replace("lat", "")
            new_name.replace("eral", "")
            new_name += '_L'
        
        else:
            if not occurrences or not scanned_id in occurrences:
                occurrences[scanned_id] = 1
            elif scanned_id in occurrences:
                occurrences[scanned_id] += 1

            if occurrences[scanned_id] == 1:
                # Dorsal
                new_name += '_D'
            elif occurrences[scanned_id] == 2:
                # Ventral
                new_name += '_V'
            else:
                new_name += '_MANUAL'


        # renaming
        os.rename(path + image, path + (new_name + ext))
        print ('Renaming {} as {}\n'.format(path + image, path + new_name + ext))
        old_new_paths.append(tuple((path + image, path + new_name + ext)))

        # find and rename corresponding cr2
        if image.split('.')[0] + '.CR2' in cr2s:
            cr2_name = new_name.split('.')[0] + '.CR2'
            os.rename(path + image.split('.')[0] + '.CR2', path + cr2_name)
            print('Renaming {} as {}\n'.format(path + image.split('.')[0] + '.CR2', path + cr2_name))
            old_new_paths.append(tuple((path + image.split('.')[0] + '.CR2', path + cr2_name)))



def Wait(path):
    wait = True
    print("Program completed... Please look over changes.")

    while wait == True:
        undo = input("Do you wish to undo?\n [1]yes\n [2]no\n --> ")
        if undo == '1' or undo == 'y' or undo =='yes':
            print(Undo())
            wait = False
        elif undo == '2' or undo == 'n' or undo == 'no':
            wait = False
            Log(path)
        else:
            print('Input error. Invalid option.')
            continue

def Undo():
    global old_new_paths
    print('\nUndoing changes...')
    for old_path,new_path in old_new_paths:
        os.rename(new_path, old_path)
        print ('Renaming {} back to {}\n'.format(new_path, old_path))
    return 'Success... Restored original state.'

def get_existing_path(path, is_dir):
    correct_path = path
    while not os.path.exists(correct_path) or (is_dir and not os.path.isdir(correct_path)) or (not is_dir and os.path.isdir(correct_path)):
        print("\nCould not find path / file in filesystem (or is wrong type, i.e. requires file but provided directory)...")
        correct_path = input('\nPlease input an appropriate path: \n --> ')
        correct_path = correct_path.strip()

        if is_dir:
            if not correct_path.endswith('/') or not correct_path.endswith('\\'):
                correct_path += '/'
        else:
            if correct_path.endswith('/'):
                correct_path = correct_path[:-1]

            elif correct_path.endswith('\\'):
                correct_path = correct_path[:-2]

    
    return correct_path

def file_prompt(prompt):
    file_path = input(prompt)
    file_path = file_path.strip()
    file_path = file_path.replace('\\', '/')

    if file_path.endswith('/') or file_path.endswith('\\'):
        file_path = file_path[:-1]
    
    return file_path

def getrange():
    lower_bound = None
    while True:
        try:
            lower_bound = int(input("\nPlease enter a lower bound for the range: "))
            break
        except:
            print("Invalid entry. Please only input integers")
            lower_bound = None

        if lower_bound is None or type(lower_bound) != type(1):
            print("Invalid entry. Please only input integers")
            lower_bound = None
    
    upper_bound = None
    while True:
        try:
            upper_bound = int(input("\nPlease enter an upper bound for the range: "))
            break
        except:
            print("Invalid entry. Please only input integers")
            upper_bound = None

        if upper_bound is None or type(upper_bound) != type(1):
            print("Invalid entry. Please only input integers")
            upper_bound = None

    return lower_bound, upper_bound
    



def main():
    global SCAN_TIME 

    # museum preformatted file names => MGCL_7digitnum
    AskUsage()
    path = input('\nPlease enter the path to the folder of images: \n --> ')

    new_time = input('\nPlease enter the max amount of scan time to search for a matrix per image (in seconds): \n --> ')
    while not new_time.isdigit():
        new_time = input('Input error. Please enter an integer. \n --> ')
    SCAN_TIME = new_time + '000'

    # this check removes trailing whitespace, an occurrence when dragging a folder into the terminal prompt in MacOS
    if path.endswith(' '):
        path = path[:-1]

    # ensures trailing '/' is present
    if not path.endswith('/') or not path.endswith('\\'):
        path += '/'

    range_data = None
    ranged_run = input("\nDo you have a range to provide for the image files to check?\n [1]yes\n [2]no\n --> ")
    if ranged_run == '1' or ranged_run == 'y' or ranged_run == 'yes':
        csv_path = get_existing_path(file_prompt("Enter the path to the CSV of range data: "), False)
        csv_data = pd.read_csv(csv_path, header=0)
        range_data = []
        for _, row in csv_data.iterrows():
            lower_bound = int(''.join(filter(str.isdigit, row['ImageStart'])))
            upper_bound = int(''.join(filter(str.isdigit, row['ImageStop'])))
            print(lower_bound, upper_bound)
            genus = row['genus']
            species = row['specificEpithet']
            range_data.append(Bound(lower_bound, upper_bound, genus, species))


    method = input("\nChoose 1 of the following: \n [1]Standard (All files " \
        "in this directory level only) \n [2]Recursive (All files in this " \
        "directory level AND every level below) \n--> ")

    if method == '1':
        ProcessData(path, range_data)
        Wait(path)
    elif method == '2':
        RecursiveProcessData(path)
        Wait(path)
    else:
        print("Input error.")
        sys.exit(1)

    print ('Program completed...\n')


if __name__ == '__main__':
    main()
