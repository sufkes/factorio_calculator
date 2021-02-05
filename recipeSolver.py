#!/usr/bin/env python

#from Collections import OrderedDict
import os
import sys

import pandas as pd
import numpy as np

import readGameFiles
from pprint import pprint, pformat

## Custom "items" which are used in recipes.
# automation-science-pack
# logistic-science-pack
# military-science-pack
# chemical-science-pack
# production-science-pack
# utility-science-pack
# space-science-pack

# water
# steam
# crude-oil
# heavy-oil
# light-oil
# petroleum-gas
# sulfuric-acid
# lubricant

class Assembler(object):
    # Includes assembling machine 1, 2, 3, oil refinery, chemical plant, and rocket silo, (and mines, furnaces etc?)
    def __init__(self, name, crafting_speed, num_module_slots):
        self.name = name
        self.crafting_speed = crafting_speed
        self.num_module_slots = num_module_slots

    def __str__(self):
        return pformat({'name':self.name, 'crafting_speed':self.crafting_speed, 'num_module_slots':self.num_module_slots})

class AssemblerManager(object):
    def __init__(self, assembler_defaults=None):
        self.assembler_dictionary = self.buildAssemblerDictionary(assembler_defaults=assembler_defaults)

    def buildAssemblerDictionary(self, assembler_defaults=None):
        base_assembler_defaults = {'assembling-machine':'assembling-machine-3',
                                   'furnace':'electric-furnace',
                                   'oil-refinery':'oil-refinery',
                                   'chemical-plant':'chemical-plant',
                                   'rocket-silo':'rocket-silo',
                                   'centrifuge':'centrifuge'}

        if assembler_defaults is None:
            assembler_defaults = base_assembler_defaults
        else:
            # If assembler name was not explicitly specified for this assembler type, use the base default.
            for assembler_type, assembler_name in base_assembler_defaults.items():
                if (not assembler_type in assembler_defaults):
                    assembler_defaults[assembler_type] = assembler_name

        # Define dictionary which is used to map a recipe's category (or lack thereof) to a specific assembler (e.g. 'crafting':'assembing-machine-3').
        # BUG: THIS DOES NOT HANDLE THE FACT THAT CERTAIN RECIPES NEED BETTER ASSEMBLERS THAN 'assembling-machine-1'.
        assembler_dictionary = {None:assembler_defaults['assembling-machine'],
                                'advanced-crafting':assembler_defaults['assembling-machine'],
                                'basic-crafting':assembler_defaults['assembling-machine'],
                                'crafting':assembler_defaults['assembling-machine'],
                                'crafting-with-fluid':assembler_defaults['assembling-machine'],
                                'smelting':assembler_defaults['furnace'],
                                'rocket-building':assembler_defaults['rocket-silo'],
                                'chemistry':assembler_defaults['chemical-plant'],
                                'oil-processing':assembler_defaults['oil-refinery'],
                                'centrifuging':assembler_defaults['centrifuge'],
                                'raw':'raw'}
        return assembler_dictionary

    def buildAssembler(self, recipe):        
        # Should read this information from game files instead.
        crafting_speed_dictionary = {'assembling-machine-1':0.5,
                               'assembling-machine-2':0.75,
                               'assembling-machine-3':1.25,
                               'stone-furnace':1,
                               'steel-furnace':2,
                               'electric-furnace':2,
                               'oil-refinery':1,
                               'chemical-plant':1,
                               'rocket-silo':1,
                               'centrifuge':1,
                               'raw':1}
        
        num_module_slots_dictionary = {'assembling-machine-1':0,
                                       'assembling-machine-2':2,
                                       'assembling-machine-3':4,
                                       'stone-furnace':0,
                                       'steel-furnace':0,
                                       'electric-furnace':2,
                                       'oil-refinery':3,
                                       'chemical-plant':3,
                                       'rocket-silo':4,
                                       'centrifuge':2,
                                       'raw':0}
    
        # Construct an assembler with appropriate settings for a given recipe.
        name = self.assembler_dictionary[recipe.category] # e.g. 'assembling-machine-3'
        crafting_speed = crafting_speed_dictionary[name]
        num_module_slots = num_module_slots_dictionary[name]
        
        assembler = Assembler(name, crafting_speed, num_module_slots)
        return assembler

class Recipe(object):
    def __init__(self, name, ingredients, results, crafting_time, category, productivity_module_compatible=True):
        self.name = name # name of recipe; not necessarily name of the result (e.g. 'advanced-oil-processing').
        self.ingredients = ingredients # dict - keys are item names, values are numbers
        self.results = results # dict - keys are item names, values are numbers
        self.crafting_time = crafting_time
        self.category = category

        self.productivity_module_compatible = productivity_module_compatible
    
    def __str__(self):
        return pformat({'name':self.name, 'ingredients':self.ingredients, 'results':self.results, 'crafting_time':self.crafting_time, 'category':self.category})

class RecipeManager(object):
    def __init__(self, expensive=False):
        self.setRecipeDictionary(expensive=expensive)

    def setRecipeDictionary(self, expensive=False):
        recipe_dictionary = {}
        
        raw_recipes = readGameFiles.getRawRecipes()
        productivity_module_limitation = readGameFiles.getProductivityModuleLimitation()

        for raw_recipe in raw_recipes:
            
            recipe_name=raw_recipe['name']
            
            debug = 0
 
            if (debug):
                pprint(raw_recipe)
            # If recipe has normal and expensive modes, pick the value (normal or expensive) and simplify the raw_recipe format to match those without normal and expensive modes.
            if ('normal' in raw_recipe):
                # For some reason, spidertron has a 'normal' key but no 'expensive' key. This is the only such case.
                if expensive and ('expensive' in raw_recipe):
                    price = 'expensive'
                else:
                    price = 'normal'
                for key, value in raw_recipe[price].items():
                    raw_recipe[key] = value

            # Parse ingredients.
            ingredients = {}
            for ingredient in raw_recipe['ingredients']:
                if type(ingredient) == list:
                    ingredient_name = ingredient[0]
                    ingredient_quantity = ingredient[1]
                    ingredients[ingredient_name] = ingredient_quantity
                elif type(ingredient) == dict:
                    ingredient_name = ingredient['name']
                    ingredient_quantity = ingredient['amount']
                    ingredients[ingredient_name] = ingredient_quantity

            # Parse results. Doesn't handle centrifuging.
            results = {}
            if 'result' in raw_recipe:
                result_name = raw_recipe['result']
                if 'result_count' in raw_recipe:
                    result_quantity = raw_recipe['result_count']
                else:
                   result_quantity = 1
                results[result_name] = result_quantity
            elif 'results' in raw_recipe:
                for result in raw_recipe['results']:
                    if type(result) == list:
                        result_name = result[0]
                        result_quantity = result[1]
                        results[result_name] = result_quantity
                    elif type(result) == dict:
                        if 'probability' in result: # handle probabilistic output of Kovarex enrichment.
                            result_quantity = result['amount']*result['probability']
                        else:
                            result_quantity = result['amount']
                        
                        result_name = result['name']
                        results[result_name] = result_quantity

            # Parse crafting time
            if 'energy_required' in raw_recipe:
                crafting_time = raw_recipe['energy_required']
            else:
                crafting_time = 0.5 # seems to be the default.

            if 'category' in raw_recipe:
                category = raw_recipe['category']
            else:
                category = None

            # Determine if recipe can use productivity modules.
            productivity_module_compatible = raw_recipe['name'] in productivity_module_limitation

            # Instantiate recipe objecft.
            recipe = Recipe(recipe_name, ingredients, results, crafting_time, category, productivity_module_compatible=productivity_module_compatible)
            
            recipe_dictionary[recipe_name] = recipe
           
            if (debug):
                print(recipe)
                pprint('')
                
        self.recipe_dictionary = recipe_dictionary # doesn't include the "recipes" for "raw" items yet.

        # Add "recipes" for "raw" items.
        self.setItemToRecipeDictionaries()
            
        for item_name in self.raw_items:
            recipe_name = item_name
            ingredients = {}
            results = {item_name:1}
            crafting_time = 1
            category = 'raw'
            productivity_module_compatible = True
            recipe = Recipe(recipe_name, ingredients, results, crafting_time, category, productivity_module_compatible=productivity_module_compatible)
            recipe_dictionary[recipe_name] = recipe
            
        self.recipe_dictionary = recipe_dictionary
        return recipe_dictionary
        
    def setItemToRecipeDictionaries(self): 
        result_to_recipe_dictionary = {}
        ingredient_to_recipe_dictionary = {}
        for recipe_name, recipe in self.recipe_dictionary.items():
            for result in recipe.results:
                if result in result_to_recipe_dictionary:
                    result_to_recipe_dictionary[result].append(recipe_name)
                else:
                    result_to_recipe_dictionary[result] = [recipe_name]
            for ingredient in recipe.ingredients:
                if ingredient in ingredient_to_recipe_dictionary:
                    ingredient_to_recipe_dictionary[ingredient].append(recipe_name)
                else:
                    ingredient_to_recipe_dictionary[ingredient] = [recipe_name]

        all_items = set(result_to_recipe_dictionary.keys())
        all_items.update(ingredient_to_recipe_dictionary.keys())
        raw_items = [item for item in all_items if not item in result_to_recipe_dictionary]
       
        # Store some well-defined results.
        self.result_to_recipe_dictionary = result_to_recipe_dictionary
        self.ingredient_to_recipe_dictionary = ingredient_to_recipe_dictionary
        self.all_items = list(all_items)
        self.raw_items = raw_items
        return


class Factory(object):
    def __init__(self, recipe, assembler_manager, default_module=None, default_num_modules=0):
        self.recipe = recipe
        self.assembler = assembler_manager.buildAssembler(recipe)

        self.setModules(default_module=default_module, default_num_modules=default_num_modules)
        self.setRateFactors()
        
    def setModules(self, default_module=None, default_num_modules=0):
        if default_module not in [None, 'productivity-module-3']:
            raise Exception('Unhandled module. Need to improve code.')

        self.modules = {'speed-module':0,
                        'speed-module-2':0,
                        'speed-module-3':0,
                        'productivity-module':0,
                        'productivity-module-2':0,
                        'productivity-module-3':0,
                        'effectivity-module':0,
                        'effectivity-module-2':0,
                        'effectivity-module-3':0}
        
        if (self.recipe.productivity_module_compatible or (default_module not in ['productivity-module', 'productivity-module-2', 'productivity-module-3'])) and (default_module is not None):
            self.modules[default_module] = min(self.assembler.num_module_slots, default_num_modules)
        return

    def setRateFactors(self):
        self.production_rate_factor = self.assembler.crafting_speed*(1+0.1*self.modules['productivity-module-3'])*(1-0.15*self.modules['productivity-module-3'])
        self.consumption_rate_factor = self.assembler.crafting_speed*(1-0.15*self.modules['productivity-module-3'])
        return
    
    def numAssemblersToRateDictionary(self, num_assemblers):
        if self.recipe.name == 'kovarex-enrichment':
            raise Exception('Cannot convert number of Kovarex enrichment centrifuges to item rate. I do not know what that should mean and also do not care right now.')
        rate_dictionary = {}
        for result, quantity in self.recipe.results.items():
            rate = quantity/self.recipe.crafting_time*self.production_rate_factor*num_assemblers
            rate_dictionary[result] = rate
        return rate_dictionary

class FactoryManager(object):
    def __init__(self, recipe_exclusions=['basic-oil-processing', 'coal-liquefaction', 'solid-fuel-from-heavy-oil', 'solid-fuel-from-petroleum-gas', 'nuclear-fuel-reprocessing'], default_module=None, default_num_modules=0):
        self.assembler_manager = AssemblerManager()
        self.recipe_manager = RecipeManager()
        
        self.recipe_exclusions = recipe_exclusions
        self.default_module = default_module
        self.default_num_modules = default_num_modules
        
        self.setFactoryDictionary()
        
        self.item_name_list = list(self.recipe_manager.all_items)
        self.recipe_name_list = list(self.factory_dictionary.keys())
        print('recipes_without_matching_item_name:')
        pprint([i for i in self.item_name_list if not i in self.recipe_name_list])
        print('items_without_matching_recipe_name:')
        pprint([i for i in self.recipe_name_list if not i in self.item_name_list])
        self.raw_item_name_list = self.recipe_manager.raw_items
        
        debug = 0
        if debug:
            for k, v in self.factory_dictionary.items():
                print('Factory:', k)
                print('Recipe:')
                print(v.recipe)
                print('Assembler:')
                print(v.assembler)
                print('Modules:')
                pprint(v.modules)
                print('')
    
    def setFactoryDictionary(self):
        factory_dictionary = {}
        for recipe_name, recipe in self.recipe_manager.recipe_dictionary.items():
            if recipe_name in self.recipe_exclusions:
                continue
            factory = Factory(recipe, self.assembler_manager, default_module=self.default_module, default_num_modules=self.default_num_modules)
            factory_dictionary[recipe_name] = factory

        self.factory_dictionary = factory_dictionary
        return
    
    def convertNumAssemblersToRates(self, num_assemblers_dictionary):
        rate_dictionary = {}
        for recipe_name, num_assemblers in num_assemblers_dictionary.items():
            factory = self.factory_dictionary[recipe_name]
            factory_rate_dictionary = factory.numAssemblersToRateDictionary(num_assemblers)
            for item_name, rate in factory_rate_dictionary.items():
                if item_name in rate_dictionary:
                    rate_dictionary[item_name] += rate
                else:
                    rate_dictionary[item_name] = rate
        return rate_dictionary
        
    def guessNameMatch(self, name, item_or_recipe):
        def leviathanDistance(string1, string2):
            # Remove capitals.
            string1 = string1.lower()
            
            # Remove ' and "
            string1 = string1.replace('"', '')
            string1 = string1.replace("'", '')
            
            # Remove leading and trailing whitespace.
            string1 = string1.strip()
            
            # Replace underscores and spaces with dashes.
            string1 = string1.replace('_', '-')
            string1 = string1.replace(' ', '-')
            
            
            score = 0
            for c1, c2 in zip(string1, string2):
                if c1 != c2:
                    score += 1
            score = score/min(len(string1), len(string2))
            return score
    
        def findBest(string1, string_list, scoreFunction=leviathanDistance):
            best_index = 0
            best_score = 1e6 # fake giant score that everthing should be able to beat.
            for index, string2 in enumerate(string_list):
                score = scoreFunction(string1, string2)
                if score < best_score:
                    best_index = index
                    best_score = score
            return string_list[best_index]
    
        if item_or_recipe not in ['item', 'recipe']:
            raise Exception("item_or_recipe must be set to 'item' or 'recipe'.")
        string_list = self.item_name_list if item_or_recipe == 'item' else self.recipe_name_list
        
        if name in string_list:
            match = name
        else:
            match = findBest(name, string_list)
        return match

def calculate(to_do, input_type, default_module='productivity-module-3', default_num_modules=4):
    # to_do: dict - keys are item names, values are either desired production rates (items/s) or number of assemblers.
    # input_type: bool - whether values in to_do are rates or numbers of assemblers

    factory_manager = FactoryManager(default_module=default_module, default_num_modules=default_num_modules)

    # Get lists of item names, recipe names, and items designated as "raw" in this script (e.g. crude-oil, iron-ore, wood).
    # item_name_list = list(factory_manager.recipe_manager.all_items)
    # recipe_name_list = list(factory_manager.factory_dictionary.keys()) # force some ordering for the matrices
    # raw_item_name_list = factory_manager.recipe_manager.raw_items
    item_name_list = factory_manager.item_name_list
    recipe_name_list = factory_manager.recipe_name_list
    raw_item_name_list = factory_manager.raw_item_name_list

    # Check that requested items or recipes exist.
    error_name_list = []
    for name in to_do:
        error = ((input_type == 'rate') and (name not in item_name_list)) or ((input_type == 'num_assemblers') and (name not in recipe_name_list))
        if error:
            error_name_list.append(name)
    item_or_recipe_string = 'item' if (input_type == 'rate') else 'recipe'
    if len(error_name_list) == 1:
        error_message = 'Requested '+item_or_recipe_string+' name does not exist: '+error_name_list[0]
    elif len(error_name_list) > 1:
        error_message = 'Requested '+item_or_recipe_string+' names do not exist: '+', '.join(error_name_list)
    if error_name_list:
        raise Exception(error_message)

    # If request is given in numbers of assemblers, convert to rates.
    to_do_raw_request = to_do.copy() # keep this in the original format (possible in terms of numbers of assemblers) only for printing purposes. Henceforth, to_do shall be stored in terms of rates.
    if input_type == 'num_assemblers':
        to_do = factory_manager.convertNumAssemblersToRates(to_do)

    # Build a matrix that stores the production or consumption rate of each item for each recipe. 

    
    rate_dataframe = pd.DataFrame(index=item_name_list, columns=recipe_name_list, data=0, dtype=np.float64)
    
    for recipe_name in recipe_name_list:
        factory = factory_manager.factory_dictionary[recipe_name]
        recipe = factory.recipe
        
        for result, quantity in recipe.results.items():
            production_rate = quantity/recipe.crafting_time*factory.production_rate_factor
            rate_dataframe.loc[result, recipe_name] += production_rate
        
        for ingredient, quantity in recipe.ingredients.items():
            consumption_rate = quantity/recipe.crafting_time*factory.consumption_rate_factor
            rate_dataframe.loc[ingredient, recipe_name] -= consumption_rate

    output_rate_dataframe = pd.DataFrame(index=item_name_list, columns=['output_rate'], dtype=np.float64, data=0)
    for item_name, output_rate in to_do.items():
        output_rate_dataframe.loc[item_name, 'output_rate'] = output_rate

    print(rate_dataframe.values.shape, output_rate_dataframe.values.shape)
    num_assemblers_array = np.linalg.solve(rate_dataframe.values, output_rate_dataframe.values)
    num_assemblers_array[abs(num_assemblers_array) < 1e-8] = 0.0 # get rid of the tiny junk that results from solving the system numerically.
    
    negative_assemblers = False
    num_assemblers_dictionary = {}
    for recipe_name, num_assemblers in zip(recipe_name_list, num_assemblers_array):
        num_assemblers = num_assemblers[0]
        if num_assemblers != 0:
            num_assemblers_dictionary[recipe_name] = num_assemblers
            if (num_assemblers < 0):
                negative_assemblers = True

    rate_dictionary = factory_manager.convertNumAssemblersToRates(num_assemblers_dictionary)
    for recipe_name in list(num_assemblers_dictionary.keys()):
        if recipe_name in raw_item_name_list:
            del num_assemblers_dictionary[recipe_name]
    num_assemblers_dict = {}
    print('-'*80)
    n_or_r = 'Production rate' if input_type == 'rate' else 'Number of assemblers'
    print('Request ('+n_or_r.lower()+'):')
    pprint(to_do_raw_request)
    print('')
    print('Numbers of assemblers:')
    pprint(num_assemblers_dictionary)
    print('')
    print('Rates:')
    pprint(rate_dictionary)
    print('')
    if negative_assemblers:
        print("Warning: Answer has negative numbers of assemblers. This is usually due to insufficient petroleum consumption.")
    return

def findIntegerRatio(item_name_to_solve, input_type='num_assemblers', threshold=1e-8):
    # for now, only handle case in which we are given a single item.
    num_assemblers = 1

    all_integers = False
    while not all_integers:
        all_integers = True # assume all numbers of assemblers are integers until proven wrong.
        to_do = {item_name_to_solve:num_assemblers}
        recipe_manager = calculate(to_do, input_type, quiet=True)
        for item_name, item in recipe_manager.recipe_dictionary.items():
            if item.raw:
                continue
            remainder = min((item.num_assemblers % 1), 1 - (item.num_assemblers % 1))
            if remainder > threshold:
                all_integers = False
                num_assemblers += 1
                break
    recipe_manager.summarize(verbose=True)

def prompt():
    factory_manager = FactoryManager() # This is not the instance used in the actual calculation. Need this now to validate item and recipe names while building request.
    # item_name_list = list(factory_manager.recipe_manager.all_items)
    # recipe_name_list = list(factory_manager.factory_dictionary.keys())
    item_name_list = factory_manager.item_name_list
    recipe_name_list = factory_manager.recipe_name_list

    def itemOrRecipeExists(name, input_type, item_name_list, recipe_name_list):
        exists = ((input_type == 'rate') and (name in item_name_list)) or ((input_type == 'num_assemblers') and (name in recipe_name_list))
        return exists

    quit = False
    while not quit:
        print('='*80)
        print('#### New request ####')
        print('-'*80)
        to_do = {} # Need to populate
    
        # Get input type.
        while not quit:
            ans = input("Input type ('r': Rate; 'n': Number of assemblers; 'q' to quit): ")
            quit = ans == 'q'
            if quit:
                break
            input_type = 'rate' if ans.lower()=='r' else 'num_assemblers' if ans.lower()=='n' else print("Invalid response.")
            if input_type is not None:
                break
        if quit:
            break
            
        i_or_r = 'Item' if input_type == 'rate' else 'Recipe'
        n_or_r = 'Production rate' if input_type == 'rate' else 'Number of assemblers'

        # Get item or recipe names and numbers.
        need_name = True
        request_complete = False
        while (not quit) and (not request_complete):
            # Get name of new item/recipe entry.
            if need_name:
                print('-'*80)
                ans = input(i_or_r+' name (press ENTER to cancel new '+i_or_r.lower()+' and complete request; \'q\' to quit): ')
                quit = ans == 'q'
                if quit:
                    break
                request_complete = ans == ''
                if request_complete:
                    continue
                if not itemOrRecipeExists(ans, input_type, item_name_list, recipe_name_list):
                    match = factory_manager.guessNameMatch(ans, i_or_r.lower())
                    while True:
                        ans = input('Invalid '+i_or_r.lower()+' name. Did you mean \''+match+'\'?\nPress ENTER to confirm; \'n\' if incorrect ; \'q\' to quit): ')
                        if ans in ['', 'y', 'n', 'q']:
                            break
                        else:
                            print('Invalid response.')
                    quit = ans == 'q'
                    if quit:
                        break
                    elif ans == 'n':
                        continue
                    else:
                        ans = match

                key = ans
                need_name = False
            # Get rate/number of assemblers for new entry.
            else:
                ans = input(n_or_r+' (press ENTER to cancel new '+i_or_r.lower()+' and complete request; \'q\' to quit): ')
                quit = ans == 'q'
                if quit:
                    break
                request_complete = ans == ''
                if request_complete:
                    continue                    
                try:
                    val = float(eval(ans))
                except ValueError:
                    print('Invalid '+n_or_r.lower()+'.')
                    continue
                to_do[key] = val
                need_name = True
            if (not quit) and (not request_complete) and need_name:
                print('-'*80)
                print('Current request ('+n_or_r.lower()+'):')
                pprint(to_do)
                print('-'*80)
                while True:
                    ans = input('Press ENTER to complete request; \'a\' to add more items or recipes; \'q\' to quit: ')
                    if ans in ['', 'a', 'q']:
                        break
                    else:
                        print('Invalid response.')
                quit = ans == 'q'
                request_complete = ans == ''
                
        if not quit:
            if to_do != {}:
                calculate(to_do, input_type=input_type, default_num_modules=0)
            else:
                print('-'*80)
                print('Error: Request must have at least one (item, value) pair.')
                
            print('')
            while True:
                ans = input('Press ENTER to create a new request; \'q\' to quit: ')
                quit = ans == 'q'
                if quit or (ans == ''):
                    break
                else:
                    print('Invalid response.')
    return

if __name__ == '__main__':
    prompt()
    
    # Test out the name match guesser.
    sys.exit()
    factory_manager = FactoryManager()
    while True:
        name = input('Item name: ')
        match = factory_manager.guessNameMatch(name, 'item')
        print('I think you mean: '+match)
    # calculate({'petroleum-gas':1, 'heavy-oil':1}, input_type='rate', default_num_modules=0)
    #calculate({'nuclear-fuel':1, 'petroleum-gas':100}, input_type='rate', default_num_modules=0)
    #print('')
    # calculate({'advanced-circuit':1}, input_type='num_assemblers', default_num_modules=0)
    #calculate({'chemical-science-pack':48}, input_type='num_assemblers', default_num_modules=0)
    #calculate({'satellite':1}, input_type='rate', default_num_modules=0)
    
