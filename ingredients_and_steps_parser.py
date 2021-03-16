import nltk
import requests
from bs4 import BeautifulSoup
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from nltk import pos_tag, word_tokenize
import re
import string
from vague_how_tos import questions
import action_parser
# from transform import replace_ingredients, replace_instructions
# from vegetarian_transform import vegetarian, not_vegetarian
# from to_healthy_transform import to_healthy
# from from_healthy_transform import from_healthy
# from to_chinese_transform import to_chinese
# from to_mexican_transform import to_mexican

def convertToFraction(test):
    fractions = {
        0x2189: 0.0,  # ; ; 0 # No       VULGAR FRACTION ZERO THIRDS
        0x2152: 0.1,  # ; ; 1/10 # No       VULGAR FRACTION ONE TENTH
        0x2151: 0.11111111,  # ; ; 1/9 # No       VULGAR FRACTION ONE NINTH
        0x215B: 0.125,  # ; ; 1/8 # No       VULGAR FRACTION ONE EIGHTH
        0x2150: 0.14285714,  # ; ; 1/7 # No       VULGAR FRACTION ONE SEVENTH
        0x2159: 0.16666667,  # ; ; 1/6 # No       VULGAR FRACTION ONE SIXTH
        0x2155: 0.2,  # ; ; 1/5 # No       VULGAR FRACTION ONE FIFTH
        0x00BC: 0.25,  # ; ; 1/4 # No       VULGAR FRACTION ONE QUARTER
        0x2153: 0.33333333,  # ; ; 1/3 # No       VULGAR FRACTION ONE THIRD
        0x215C: 0.375,  # ; ; 3/8 # No       VULGAR FRACTION THREE EIGHTHS
        0x2156: 0.4,  # ; ; 2/5 # No       VULGAR FRACTION TWO FIFTHS
        0x00BD: 0.5,  # ; ; 1/2 # No       VULGAR FRACTION ONE HALF
        0x2157: 0.6,  # ; ; 3/5 # No       VULGAR FRACTION THREE FIFTHS
        0x215D: 0.625,  # ; ; 5/8 # No       VULGAR FRACTION FIVE EIGHTHS
        0x2154: 0.66666667,  # ; ; 2/3 # No       VULGAR FRACTION TWO THIRDS
        0x00BE: 0.75,  # ; ; 3/4 # No       VULGAR FRACTION THREE QUARTERS
        0x2158: 0.8,  # ; ; 4/5 # No       VULGAR FRACTION FOUR FIFTHS
        0x215A: 0.83333333,  # ; ; 5/6 # No       VULGAR FRACTION FIVE SIXTHS
        0x215E: 0.875,  # ; ; 7/8 # No       VULGAR FRACTION SEVEN EIGHTHS
    }

    rx = r'(?u)([+-])?(\d*)(%s)' % '|'.join(map(chr, fractions))

    for sign, d, f in re.findall(rx, test):
        sign = -1 if sign == '-' else 1
        d = int(d) if d else 0
        number = sign * (d + fractions[ord(f)])

    try:
        return (f, number)
    except:
        return -1

def convert_to_float(frac):
    try:
        return float(frac)
    except ValueError:
        num, denom = frac.split('/')
        try:
            leading, num = num.split(' ')
            whole = float(leading)
        except ValueError:
            whole = 0
        frac = float(num) / float(denom)
        return whole - frac if whole < 0 else whole + frac

def getRecipe(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup

def getTitle(soup):
    title = str(soup.title.text)
    return title

def getSteps(soup):
    result = []
    directions = soup.find_all("div", class_= "section-body")
    for direction in directions:
        x = direction.get_text().replace("\n", "").strip()
        result.append(x)

    result = result[:-1]
    return result

def getIngredients(soup):

    ingredients = soup.find_all("li", class_="ingredients-item")
    if not ingredients:
        #do this later
        pass
    result = []
    for ingredient in ingredients:
        x = ingredient.label.text.replace("\n", "").strip()
        numbers = convertToFraction(x)
        if numbers == -1:
            result.append(x)
        else:
            x = x.replace(numbers[0], str(numbers[1]))
            result.append(x)

    x = getIngredientParts(result)
    return x, result

def getIngredientParts(ingredients):

    measurements = ['tablespoon', 'tablespoons', 'ounce', 'ounces', 'teaspoon', 'teaspoons', 'cup', 'cups', 'quart',
                    'quarts', 'pint', 'pints', 'gallon', 'gallons', 'pound', 'pounds', 'pinch', 'package', 'packages',
                    'pound', 'pounds', 'slice', 'slices', 'packet', 'packets', 'cube', 'cubes', 'quart', 'quarts',
                    'halves', 'jar', 'jars', 'inch', 'inches']

    descriptors = ['ground', 'all-purpose', 'extra-virgin', 'unsweetened', 'provolone']

    keywords = ['black']

    finalIngredients = []


    for ingredient in ingredients:
        shouldContinue = False
        ingredientName = ""
        quantity = 0
        measurement = ""
        descriptor = ""
        preparation = ""
        text = word_tokenize(ingredient)

        test = pos_tag(text)

        for i in range(0, len(text)):
            if shouldContinue:
                shouldContinue = False
                continue

            if test[i][1] == 'CD':
                try:
                    x = convert_to_float(text[i])
                    quantity += x
                except:
                    if text[i] in descriptors:
                        if descriptors != "":
                            descriptor += ' ' + text[i]
                        else:
                            descriptor += text[i]

            else:
                if text[i] in measurements:
                    measurement += text[i]
                else:
                    if text[i] in keywords:
                        if ingredientName != "":
                            ingredientName += ' and ' + text[i] + ' ' + text[i + 1]
                            shouldContinue = True
                        else:
                            ingredientName += text[i] + ' ' + text[i + 1]
                            shouldContinue = True
                    elif text[i] in descriptors:
                        if descriptors != "":
                            descriptor += ' ' + text[i]
                        else:
                            descriptor += text[i]
                    elif test[i][1] == 'JJ':
                        if descriptors != "":
                            descriptor += ' ' + text[i]
                        else:
                            descriptor += text[i]
                    elif test[i][1] == 'NN' or test[i][1] == 'NNS':
                        if ingredientName != "":
                            ingredientName += ' ' + text[i]
                        else:
                            ingredientName += text[i]
                    elif test[i][1] == 'RB':
                        #for adverbs, eg 'finely chopped'
                        if preparation != "":
                            preparation += ' and ' + text[i] + ' ' + text[i + 1]
                            shouldContinue = True
                        else:
                            preparation += text[i] + ' ' + text[i + 1]
                            shouldContinue = True
                    elif test[i][1] == 'VBN' or test[i][1] == 'VBD':
                        if preparation != "":
                            preparation += ' and ' + text[i]
                        else:
                            preparation += text[i]

        ingredientObj = {
            "name": ingredientName,
            "quantity": str(quantity),
            "measurement": measurement,
            "descriptor": descriptor,
            "preparation": preparation
        }
        finalIngredients.append(ingredientObj)

    return finalIngredients

def getTools(directions):
    table = str.maketrans(dict.fromkeys(string.punctuation))
    toolsList = ['knife', 'cutting board', 'can opener', 'bowl', 'bowls', 'colander', 'peeler', 'masher',
                 'potato masher', 'whisk', 'grater', 'shears', 'shear', 'juicer', 'skillet', 'pan', 'pans',
                 'pot', 'pots', 'saucepan', 'stockpot', 'spatula', 'stirring spoon', 'spoon', 'tongs',
                 'ladle', 'oven mitts', 'trivet', 'splatter guard', 'thermometer', 'blender', 'scale', 'container',
                 'aluminum foil', 'parchment paper', 'towel', 'towels', 'food processor', 'grill', 'baster',
                 'beanpot', 'brush', 'basket', 'timer', 'sheet', 'baking sheet', 'poacher', 'grittle', 'grater',
                 'grinder', 'griddle', 'mixer', 'microwave', 'oven', 'strainer', 'steamer', 'scissors', 'sieve',
                 'skewer', 'wok', 'zester', 'plate', 'mortar', 'pestle', 'gloves', 'cookie cutter', 'cookie sheet',
                 'cookie sheets', 'bread knife', 'cheese grater', 'cheese cutter', 'cheese knife', 'pizza wheel',
                 'pizza cutter', 'soup ladle', 'rolling pin', 'baking dish', 'baking pan', 'baking sheet', 'baking sheets',
                 'air fryer', 'shallow dish', 'container', 'containers']

    returnList = []
    for i in range(len(directions)):
        bigrams = list(nltk.bigrams(directions[i].lower().split()))
        for x in bigrams:
            two_words = x[0] + ' ' + x[1]
            two_words = two_words.translate(table)
            if two_words in toolsList:
                returnList.append(two_words)

        words = directions[i].lower().split()
        for x in words:
            x = x.translate(table)
            test = [y.split() for y in returnList]
            combined = []
            for j in test:
                combined = combined + j

            if x in toolsList and x not in combined and x not in returnList:
                returnList.append(x)

    return returnList


def getMethods(directions):
    table = str.maketrans(dict.fromkeys(string.punctuation))
    possibleMethods = ['bake', 'heat', 'cook', 'boil', 'saute', 'broil', 'poach', 'roast', 'steam']

    resultList = []
    for i in range(len(directions)):
        directionCleaned = directions[i].translate(table).lower()
        for word in directionCleaned.split():
            if word in possibleMethods:
                if word not in resultList:
                    resultList.append(word)

    return resultList

def goOverIngredients(title, ingredients, steps):
    print("Here are the ingredients for " + title + ".\n")
    for i in range(0, len(ingredients)):
        print(str(i + 1) + '. ' + ingredients[i])

    print("\nWhat would you like to do?")
    print("[1] Go over the steps")
    response = input("[0] Exit\n")

    if response == "0":
        exit(0)
    elif response == "1":
        goOverSteps(title, steps, 1, ingredients)
    else:
        invalid = True
        while invalid:
            response = input("Invalid input. What would you like to do? [1] Go over ingredients or [2] Go over recipe steps [0] Exit \n")
            if response == "0":
                invalid = False
                exit(0)
            elif response == "1":
                invalid = False
                goOverSteps(title, steps, 1, ingredients)


def goOverSteps(title, steps, stepNumber, ingredients):

    specialSteps = [1, 2, 3]

    if stepNumber - 1 >= 0 and stepNumber <= len(steps):

        if stepNumber in specialSteps:
            if stepNumber == 1:
                print("The 1st step is: " + steps[stepNumber - 1])
            elif stepNumber == 2:
                print("The 2nd step is: " + steps[stepNumber - 1])
            elif stepNumber == 3:
                print("The 3rd step is: " + steps[stepNumber - 1])
        else:
            print("The " + str(stepNumber) + "th step is: " + steps[stepNumber - 1])


        print("What would you like to do?")
        print("[1] Go to the ingredients")
        print("[2] Go to the next step")
        print("[3] Go to the previous step")
        print("[4] Go to a specific step")
        print("Confused? Say something like 'How do I do that?'")
        print("\n")
        response = input("[0] Exit\n")

        if response == "0":
            exit(0)
        elif response == "1":
            goOverIngredients(title, ingredients, steps)
        elif response == "2":
            stepNumber = stepNumber + 1
            goOverSteps(title, steps, stepNumber, ingredients)
        elif response == "3":
            stepNumber = stepNumber - 1
            goOverSteps(title, steps, stepNumber, ingredients)
        elif response == "4":
            stepNumber = input("Which step would you like to go to? Type a number between 1 and " + str(len(steps)) + ".\n")
            stepNumber = int(stepNumber)
            goOverSteps(title, steps, stepNumber, ingredients)
        elif response.lower().replace("?", "") in questions:
            step = steps[stepNumber - 1]
            link = action_parser.parse_command(step)
            print("Here's what I found: " + link)
            goOverSteps(title, steps, stepNumber, ingredients)
        else:
            invalid = True
            while invalid:
                print("Invalid input. What would you like to do?")
                print("[1] Go to the ingredients")
                print("[2] Go to the next step")
                print("[3] Go to the previous step")
                print("[4] Go to a specific step")
                print("Confused? Say something like 'How do I do that?'")
                print("\n")
                response = input("[0] Exit\n")

                if response == "0":
                    invalid = False
                    exit(0)
                elif response == "1":
                    invalid = False
                    goOverIngredients(title, ingredients, steps)
                elif response == "2":
                    invalid = False
                    stepNumber = stepNumber + 1
                    goOverSteps(title, steps, stepNumber, ingredients)
                elif response == "3":
                    invalid = False
                    stepNumber = stepNumber - 1
                    goOverSteps(title, steps, stepNumber, ingredients)
                elif response == "4":
                    invalid = False
                    stepNumber = input(
                        "Which step would you like to go to? Type a number between 1 and " + str(len(steps)) + ".\n")
                    stepNumber = int(stepNumber)
                    goOverSteps(title, steps, stepNumber, ingredients)
                elif response.lower().replace("?", "") in questions:
                    step = steps[stepNumber - 1]
                    link = action_parser.parse_command(step)
                    print("Here's what I found: " + link)
                    goOverSteps(title, steps, stepNumber, ingredients)






    else:
        print("There are only " + str(len(steps)) + " steps in this recipe!")
        print("What would you like to do?")
        print("[1] Go to the ingredients")
        print("[2] Go to the first step")
        print("[3] Go to the last step")
        print("[4] Go to a specific step")
        print("Confused? Say something like 'How do I do that?'")
        print("\n")
        response = input("[0] Exit\n")

        if response == "0":
            exit(0)
        elif response == "1":
            goOverIngredients(title, ingredients, steps)
        elif response == "2":
            goOverSteps(title, steps, 1, ingredients)
        elif response == "3":
            #go to the last step in this case
            goOverSteps(title, steps, len(steps), ingredients)
        elif response == "4":
            stepNumber = input("Which step would you like to go to? Type a number between 1 and " + str(len(steps) + 1) + ".\n")
            stepNumber = int(stepNumber)
            goOverSteps(title, steps, stepNumber, ingredients)
        elif response.lower().replace("?", "") in questions:
            step = steps[stepNumber - 1]
            link = action_parser.parse_command(step)
            print("Here's what I found: " + link)
            goOverSteps(title, steps, stepNumber, ingredients)

def main(url):
    try:
        recipeSoup = getRecipe(url)
    except:
        print("Invalid URL")
        exit(0)

    title = getTitle(recipeSoup)
    ingredients = getIngredients(recipeSoup)[1]
    steps = getSteps(recipeSoup)
    tools = getTools(steps)
    methods = getMethods(steps)

    stillRunning = True

    first_input = input(
        "Alright. Let's start working with " + title + ".\n" + "What would you like to do? [1] Go over ingredients or [2] Go over recipe steps [0] Exit \n")
    while stillRunning:
        if first_input == "0":
            stillRunning = False
            exit(0)
        elif first_input == "1":
            stillRunning = False
            goOverIngredients(title, ingredients, steps)
        elif first_input == "2":
            stillRunning = False
            goOverSteps(title, steps, 1, ingredients)
        else:
            first_input = input("Invalid input. What would you like to do? [1] Go over ingredients or [2] Go over recipe steps [0] Exit \n")


















    print("Recipe Ingredients (before transformation): ")
    for i in range(0, len(ingredients)):
        print(str(i + 1) + '. ' + ingredients[i]['name'])
        print("quantity: " + ingredients[i]['quantity'])
        print("measurement: " + ingredients[i]['measurement'])
        print("descriptor: " + ingredients[i]['descriptor'])
        print("preparation: " + ingredients[i]['preparation'] + '\n')

    # print(ingredients)
    # print('\n')
    print("Recipe Tools: ")
    for i in range(0, len(tools)):
        print(str(i + 1) + '. ' + tools[i])

    print("\nRecipe Methods: ")
    for i in range(0, len(methods)):
        print(str(i + 1) + '. ' + methods[i])

    print("\nRecipe Steps: (before transformation): ")
    for i in range(0, len(steps)):
        print(str(i + 1) + '. ' + steps[i])



if __name__ == '__main__':
    recipeUrl = input('Please enter a URL for a recipe from AllRecipes.com (enter 0 to exit): ')
    if recipeUrl == '0':
        exit(0)
    main(recipeUrl)
