import requests
import sys
from bs4 import BeautifulSoup
from google_images_download import google_images_download
import shutil
from random import randrange
import urllib.request
import os
from PIL import Image
import ntpath

#all the specific game exes
game_dict = {"gta v":"playgtav"}

#path to the game list file
exes = []
res_folder = ""
game_list_file =""
background_folder = ""
icon_folder = ""
game_dirs = [""]
choose_images = True

def set_paths(main_path):
    global res_folder
    global game_list_file
    global background_folder
    global icon_folder
    res_folder = main_path
    game_list_file = os.path.join(res_folder, "User/list_game.inc") 
    background_folder = os.path.join(res_folder, "Background")
    icon_folder = os.path.join(res_folder, "Icons")

#gets the games that have been added
def get_added_games():
    f = open(game_list_file, "r")
    lines = f.readlines()
    f.close()

    #parse the lines
    games = []
    current_game = {}
    for line in lines:
        if(line.startswith("Name")):
            name = line[line.index("=")+1:]
            current_game["name"] = name.replace("\n", "")
        elif(line.startswith("Icon")):
            icon = line[line.index("=")+1:]
            current_game["icon"] = icon.replace("\n", "")
        elif(line.startswith("Dir")):
            direct = line[line.index("=")+1:]
            current_game["dir"] = direct.replace("\n", "")
        elif(line.startswith("Cover")):
            cover = line[line.index("=")+1:]
            current_game["cover"] = cover.replace("\n", "")
        elif(line.startswith("Background")):
            bg = line[line.index("=")+1:]
            current_game["background"] = bg.replace("\n", "")      
        elif(line.strip() == ""):
            if(not current_game == {}):
                games.append(current_game)
            current_game = {}
    return games
        
#writes a dictionary of games to the file
def write_games(games):
    lines = ["[Variables]"]
    lines.append("Total="+str(len(games)))
    lines.append("LastOpen=1\n")
    current_game = 1
    for game in games:
        if not game is None:
            lines.append("Name"+str(current_game)+"="+game["name"])
            lines.append("Icon"+str(current_game)+"="+game["icon"])
            lines.append("Cover"+str(current_game)+"="+game["cover"])
            lines.append("Dir"+str(current_game)+"="+game["dir"])
            lines.append("Background"+str(current_game)+"="+game["background"])
            current_game += 1
            lines.append("\n")
        
    #write the lines
    write_string = "\n".join(lines)
    f = open(game_list_file, "w+")
    f.write(write_string)
    f.close()

    

#generates a game from a steam id
def generate_game_from_steam(id):
    print("Generating: " + str(id) + " from Steam")
    url = "https://store.steampowered.com/app/" + str(id)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    title = remove_invalid_characters(soup.title.string)
    return_game = {}
    name = title
    if("on Steam" in title):
        name = title[:title.index("on Steam")-1]
    return_game["name"] = name
    print(name)
    return_game["dir"] =  "steam://rungameid/"+str(id)
    print("Getting background")
    game_background_url = get_game_background(name)
    save_image_and_resize(game_background_url, os.path.join(background_folder, name.replace(" ","") + ".jpg"))
    return_game["background"] = name.replace(" ","") + ".jpg"
    return_game["cover"] = ""
    print("Getting icon")
    game_icon_url = get_game_icon(title) 
    save_image(game_icon_url, os.path.join(icon_folder, name.replace(" ", "") + ".png"))
    return_game["icon"] = name.replace(" ","") + ".png"
    return return_game
    
#generates a game from an general game name
def generate_game_general(game_name):
    print("Generating: " + game_name )
    name = game_name.title()
    return_game = {}
    return_game["name"] = name
    print(name)
    return_game["dir"] =  find_game_path_in_dirs_general(name)
    print("Getting background")
    game_background_url = get_game_background(name)
    save_image_and_resize(game_background_url, os.path.join(background_folder, name.replace(" ","") + ".jpg"))
    return_game["background"] = name.replace(" ","") + ".jpg"
    return_game["cover"] = ""
    print("Getting icon")
    game_icon_url = get_game_icon(name) 
    save_image(game_icon_url, os.path.join(icon_folder, name.replace(" ", "") + ".png"))
    return_game["icon"] = name.replace(" ","") + ".png"
    return return_game




def find_game_path_in_dirs_general(game_name):
    global exes
    for exe in exes:
        if game_name.lower() in ntpath.basename(exe).lower().replace(" ", "") or is_valid_exe(game_name, exe):
                    return exe
    return_path = ""
    for folder in game_dirs:
        walker = Walker(folder)
        while(walker.has_next()):
            filename = walker.get_next_file()
            name, file_extension = os.path.splitext(filename)
            if(file_extension == ".exe"):
                exes.append(filename)
                if game_name.replace(" ", "").lower() in ntpath.basename(name).lower().replace(" ", "") or is_valid_exe(game_name, ntpath.basename(name)):
                    if(is_in_game_dict(game_name) and game_dict[game_name.lower()].lower() == ntpath.basename(name).lower()):
                        return filename
                    elif(not is_in_game_dict(game_name)):
                        return filename

                   
    return ""

#returns true if the game name is in the game dict
def is_in_game_dict(game_name):
    for game in game_dict.keys():
        if(game.lower() == game_name.lower()):
            return True
    return False

def is_valid_exe(game_name, exe_name):
        matching_first = game_name[0].lower() == exe_name[0].lower()
        matching_chars = 0
        if(matching_first):
            for char in game_name:
                if(char in exe_name):
                    game_name = game_name.replace(char, "", 1)
                    matching_chars += 1
        return matching_first and matching_chars >= 3 and len(exe_name) <= len(game_name)


def save_image(url, path):
    if(url != ""):
        urllib.request.urlretrieve(url, path)

def save_image_and_resize(url, path):
    save_image(url, path)
    im = Image.open(path)
    im_r = im.resize((1920, 1080),  Image.ANTIALIAS)
    im_r.save(path)


def get_game_background(game_name):
    return get_google_images(game_name + " game hd", size=">4MP")

def get_game_icon(game_name):
    return get_google_images(game_name + " icon","png")

def get_google_images(search_text, file_type ="", size = "", resize=False):
        arguments = {"keywords": search_text, 
                 "limit":5, 
                 "print_urls"   : True} 
        
        if(file_type != ""):
            arguments["format"] = file_type
        if(size != ""):
            arguments["size"] = size

        response = google_images_download.googleimagesdownload()
        orig_stdout = sys.stdout
        f = open('URLS.txt', 'w')
        sys.stdout = f
        paths = response.download(arguments)
        
        sys.stdout = orig_stdout
        f.close()

        with open('URLS.txt') as f:
            content = f.readlines()
        f.close()
        urls = []
        for j in range(len(content)):
            if content[j][:9] == 'Completed':
                urls.append(content[j-1][11:-1])   
        shutil.rmtree("downloads")
        chosen_image = ""
        if(choose_images):
            for url in urls:
                responded = False
                res = ""
                while(not responded):
                    print(url)
                    res = input("Do you like this image? [y/n]")
                    if(res == "n" or res =="y"):
                        responded = True
                if res == "y":
                    chosen_image = url
                    break
        else:
            chosen_image = urls[randrange(len(urls))]

        return chosen_image

                
def remove_invalid_characters(string_in):
    encoded_string = string_in.encode("ascii", "ignore")
    decode_string = encoded_string.decode()
    return decode_string

def generate_game(game):
        if(game.isnumeric()):
            return generate_game_from_steam(game)
        else:
           return generate_game_general(game)
           """
            try:
                
            except Exception as e:
                print(e)
                print("Could not generate " + str(game))
                return {}
            """

def generate_games(game_ls):
    return list(filter(lambda x: x != {}, list(map(generate_game, game_ls))))


class Walker: #used to walk directories top down and find files

    current_dirs = [] #works like a queue
    current_files = [] #works like queue

    def __init__(self, starting_dir):
        self.current_dirs = [starting_dir]

    
    def has_next(self):
        return self.current_dirs != [] or self.current_files != []

    def get_next_file(self):
        if(self.current_files == []):
            working_path = self.current_dirs.pop(0)
            contents = os.listdir(working_path)
            if contents == [] and self.current_dirs != []:
                return self.get_next_file()
            elif contents == [] and current_dirs == []:
                return ""

            for content in contents:
                if(os.path.isdir(os.path.join(working_path, content))):
                    self.current_dirs.append(os.path.join(working_path, content))
                else:
                    self.current_files.append(os.path.join(working_path, content))
        if(self.current_files == []):
            return self.get_next_file()
        return_file = self.current_files.pop(0)
        return return_file

    


def main():
    game_folders = []
    res_dir = ""
    game_ls = []
    parse_ls = sys.argv[1:]
    while parse_ls != []:
        front = parse_ls.pop(0)
        if(front == "-g"):
            while parse_ls != [] and not parse_ls[0].startswith("-"):
                game_ls.append(parse_ls.pop(0))
            
        elif(front == "-r"):
            while parse_ls != [] and not parse_ls[0].startswith("-"):
                res_dir = parse_ls.pop(0)
    

        elif(front == "-d"):
            while parse_ls != [] and not parse_ls[0].startswith("-"):
               game_folders.append(parse_ls.pop(0))

    set_paths(res_dir)
    global game_dirs
    game_dirs = game_folders
    current_games = get_added_games() #get the users current games - do not overwrite
    print("Generating games")
    games = generate_games(game_ls)
    print("Games generated")
    games = current_games + games
    write_games(games)




main()



