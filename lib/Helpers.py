import os
import time
import datetime

# I chose to wrap these functions in a class so that I am not 
# confused when I see them called in the other files 
# (basically just me enforcing the use of visual scope)

class Helpers:
    @staticmethod
    def ask_usage(prompt):
        wanted = input("Do you want to see the usage information?\n [1]yes\n [2]no\n --> ")
        if wanted == '1' or wanted == 'y' or wanted == 'yes':
            print(prompt)
            time.sleep(5)

    @staticmethod
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

    @staticmethod
    def path_prompt(prompt):
        path = input(prompt)
        path = path.strip()
        path = path.replace('\\', '/')

        if not path.endswith('/'):
            path += '/'

        return path

    @staticmethod
    def file_prompt(prompt):
        file_path = input(prompt)
        file_path = file_path.strip()
        file_path = file_path.replace('\\', '/')

        if file_path.endswith('/') or file_path.endswith('\\'):
            file_path = file_path[:-1]
        
        return file_path

    @staticmethod
    def rescurse_prompt(prompt):
        recurse = input(prompt)
        valid = False

        if recurse in ['1', '2', '[1]', '[2]']:
            valid = True

        while not valid:
            recurse = input("\nInvalid input. {}".format(prompt))
            
            if recurse in ['1', '2', '[1]', '[2]']:
                valid = True


        if recurse == '1' or recurse == '[1]':
            return False
        
        else: 
            return True
    
    @staticmethod
    def get_dirs(path):
        dirs = []
        for dir in sorted(os.listdir(path)):
            if os.path.isdir(path + dir):
                dirs.append(dir)
        return dirs

    @staticmethod
    def valid_images():
        """
            returns arr of valid image ext
        """
        return ["jpg", "jpeg", "cr2", "png"]

    @staticmethod
    def valid_image(img):
        img_vec = img.split(".")

        # cannot verify w/o ext
        if len(img_vec) < 2:
            return False
        
        img_ext = img_vec[1]
        if img_ext.lower() not in ["jpg", "jpeg", "cr2", "png"]:
            return False
        
        return True

    @staticmethod
    def get_valid_images(path):
        files = []
        for f in sorted(os.listdir(path)):
            if os.path.isfile(path + f) and Helpers.valid_image(f):
                files.append(f)
        return files

    @staticmethod
    def is_int(target):
        try: 
            int(target)
            return True
        except ValueError:
            return False

    @staticmethod
    def generate_logname(filename, ext, path):
        d = datetime.datetime.today()
        date = '{}_{}_{}'.format(str(d.year), str(d.month), str(d.day))

        filename = '{}_{}'.format(filename, date)

        count = ''
        num = 0
        while os.path.exists(filename + count + ext):
            if num == 0 :
                filename += '_'
            num += 1
            count = str(num)

        if num == 0:
            filename = filename + ext
        else:
            filename = filename + count + ext

        return filename