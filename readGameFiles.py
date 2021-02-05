#!/usr/bin/env python

import os
from glob import glob
from slpp import slpp as lua
from pprint import pprint
import json 

#def getRawRecipes(game_dir = 'F:\\Tower Program Files\\Program Files (x86)\\SteamLibrary\\steamapps\\common\\Factorio'):
def getRawRecipes(game_dir='F:\\Tower Program Files\\Program Files (x86)\\SteamLibrary\\steamapps\\common\\Factorio', update_from_game_files=False):
    # recipe_dir = os.path.join(game_dir, 'data\\base\\prototypes\\recipe') # Changed in 1.1
    # recipe_paths = glob(os.path.join(recipe_dir,'*'))
    
    if update_from_game_files:
        recipe_dir = os.path.join(game_dir, 'data\\base\\prototypes')
        recipe_lua_path = os.path.join(recipe_dir, 'recipe.lua') # path to the actual game file. Only used for updated JSON.
    recipe_json_path = 'recipe.json'

    raw_recipes = []
    recipe_names = set()
    
    if update_from_game_files:
        with open(recipe_lua_path, 'r') as lua_file:
            recipe_string = lua_file.read().strip().lstrip('data:extend(').rstrip(')')
            recipe_list = lua.decode(recipe_string)
            with open(recipe_json_path, 'w') as json_file:
                json.dump(recipe_list, json_file)
    else:
        with open(recipe_json_path, 'r') as json_file:
            recipe_list = json.load(json_file)

    
    raw_recipes.extend(recipe_list)
    for recipe in recipe_list:

        if 'name' not in recipe:
            print('Warning: Malformed recipe:', recipe)
        else:
            if recipe['name'] not in recipe_names:
                recipe_names.add(recipe['name'])
            else:
                if recipe['name'] != recipe:
                    #print('Warning: Multiple entries for recipe:', recipe['name'], '; first duplicate found in file:', os.path.basename(recipe_path))
                    pass
    return raw_recipes

#def getProductivityModuleLimitation(game_dir = 'F:\\Tower Program Files\\Program Files (x86)\\SteamLibrary\\steamapps\\common\\Factorio'):
def getProductivityModuleLimitation(game_dir='F:\\Tower Program Files\\Program Files (x86)\\SteamLibrary\\steamapps\\common\\Factorio', update_from_game_files=False):
    # module_dir = os.path.join(game_dir, 'data\\base\\prototypes\\item')
    # module_file_name = 'module.lua'
    
    module_dir = os.path.join(game_dir, 'data\\base\\prototypes')
    module_file_name = 'item.lua'
    
    module_path = os.path.join(module_dir, module_file_name)
    
    with open(module_path, 'r') as f:
        module_string = f.read()
    
    productivity_module_limitations = module_string.split('function productivity_module_limitation')[1]
    productivity_module_limitations = productivity_module_limitations.split('return')[1].split('end')[0]
    productivity_module_limitations = productivity_module_limitations.replace('{', '[').replace('}', ']')
    productivity_module_limitations = json.loads(productivity_module_limitations)
    
    return productivity_module_limitations
    

if __name__ == '__main__':
    raw_recipes = getRawRecipes(update_from_file=True)
    raw_recipes = getRawRecipes()
    print(raw_recipes)
    productivity_module_limitation = getProductivityModuleLimitation()
