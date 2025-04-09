import requests
import time
import pandas as pd
from tabulate import tabulate

s = requests.Session() # session is used so that we can reuse the same TCP connection, which is more performant

def main():
    
    # ask the user if they want full visualised experience, or just the CLI version
    user_prompt = user_input_init()
    if user_prompt == 1:
        visualised_experience()

    # get all the data we need at the start
    poke_data = get_all_pokemon_data()
    
    ## Q1: Fetch Data for Pikachu, and display 
    display_characteristics(poke_data['pikachu'])

    ## Q2: Choose data for any pokemon
    choose_pokemons()

    # create base df for further analysis in Q3 onwards
    df = create_base_df(poke_data)

    ## Q3: List pokemon and their count by type
    print("Q3\nListing types and the count of pokemon per type by descending amount")
    count = count_type(df)

    ## Q4: Calculate avg base speed, then display the type with the highest avg base speed
    print("Calculating average base speed of all pokemon per Type.")
    print("The type with the highest avg base speed is shown below:")
    avg_base_exp(data=df, count=count)

    ## Q5: Display distinct counts of abilities and moves
    print("Displaying the distinct counts of abilities and moves across all pokemon separately below:")
    distinct_moves_abilities(df)

    ## Q6: Group pokemon by primary type, list distinct moves for each group. Identify most common move
    print("Grouping pokemon by primary type, listing distinct moves for each group, then identifying most common move within each group")
    groupby_type_distinct(df)

    ## Q7.1: Identify top 3 pokemon with highest base stats,
    top3 = top3_pokemon(df)

    ## Q7.2: Identify the most diverse moves
    diverse_moves = identify_diverse_moves(top3)
    print_tabulated(diverse_moves)

def print_tabulated(df, headers="keys"):
    print(tabulate(df, headers=headers, tablefmt="grid"))

def list_pokemon():
    response = s.get('https://pokeapi.co/api/v2/pokemon/?limit=151') # limit to 151 pokemons, as per requirements
    return response.json()

def get_all_pokemon_data():
    poke_data = {}

    print("Requesting data for all required pokemon...")
    for num in range(1, 152):
        response = exponential_backoff(f"https://pokeapi.co/api/v2/pokemon/{num}")

        if response.status_code == 200:
            data = response.json()
            # add the response to the dictionary, with the pokemon name as the key
            poke_data[data['name']] = data
    return poke_data

def exponential_backoff(url,retries=3):

    # loops through retries and gets the response from the url
    for i in range(retries):
        response = s.get(url)

        # if the response is 200 (OK), return the response
        if response.status_code == 200:
            return response
        
        # if the response is not 200, print a message and wait for 2^i seconds
        else:
            print(f"Failed to get response from {url}. Retrying in {2*i} seconds.")
            time.sleep(2**i) # use ^2 rather than x2 so we get exponential backoff
            if i == retries - 1: # checks to see if we have hit the max retries (retries - 1 because we start from 0)
                print(f"The API limit has hit our max retry threshold. Exiting.")
    return None

def display_characteristics(response):

    # name
    print("-----------------------------")
    print(f"You chose: \n{response['name'].upper()} \n-----------------------------")
    

    # abilities
    print("Abilities:")
    for i in response['abilities']:
        print(i['ability']['name'].capitalize())
    
    # stats
    print("Stats:")
    for stat in response['stats']:
        stat_name = stat['stat']['name'].capitalize()
        base_stat = stat['base_stat']
        print(f"{stat_name} - {base_stat}")

    # base exp
    print("Base experience:")
    print(response['base_experience'])

def user_input_init():
    print("Hello! Welcome to the Pokemon analysis lab!")
    print("Would you like the full visualised, advanced experience that includes measures of performance? Or a more simplistic, lightweight version of the program?")
    print("Please note that the full visualised experience requires Docker to be installed on your machine. See the README.md for furhter info")
    print("1. Visualised, interactive experience.\n 2. Simplistic, lightweight version.")

    while True:
        user_input = input("Enter your choice: ")
        user_input = int(user_input)
        if user_input == 1 or user_input == 2:
            print("Thanks! You have chosen option", user_input)
            break
        else:
            print("Invalid input. Please enter 1 or 2.")
    return user_input

def visualised_experience():
    pass
    # start grafana dashboard 

def choose_pokemons():
    
    # get all pokemons via the session object
    pokemons = s.get('https://pokeapi.co/api/v2/pokemon/')
    
    ## init counter variable to keep track of the index of the pokemon
    # (needed as we aren't using range(len()) to iterate the pokemons)
    counter = 0
    
    # iterate over the pokemons and print the name of each pokemon
    for i in pokemons.json()['results']:
        print(f"{counter}: {i['name']}")
        counter += 1
    
    # get user input, use a while loop to ensure the user enters a valid input
    while True:
        user_input = input("Enter your choice: ")
        user_input = int(user_input)
        if user_input >= 0 and user_input < counter: # check if the user input is within the range of the number of pokemons
            # break out the loop and continue if input is correct
            break
        else:
            print("Invalid input. Please enter the number of the pokemon you want to analyse.")

    # get the pokemon the user chose
    response = s.get(f'https://pokeapi.co/api/v2/pokemon/{user_input}')
    display_characteristics(response.json())
    
def create_base_df(poke_data):

    master_dict = {}

    # Get master dict to operate on 
    # loop through each Pokémon in poke_data
    for name, pokemon in poke_data.items():
        
        # get types, handle for primary and secondary
        # create empty types list
        types = []
        for t in pokemon['types']:
            types.append(t['type']['name']) # add types names to list
        type1 = types[0] # get primary type from types list 
        type2 = types[1] if len(types) > 1 else None # check if secondary type exists
        
        # Base exp
        base_exp = pokemon.get('base_experience', None)

        # Abilities
        abilities = [] 
        for ability in pokemon['abilities']:
            abilities.append(ability['ability']['name'])

        # Moves
        moves = []
        for move in pokemon['moves']:
            moves.append(move['move']['name'])

        # Base Stats
        # store base stats as a dict, because they are key: value pairs (base_stat: num)
        base_stats = {}
        for stat in pokemon['stats']:
            stat_name = stat['stat']['name']
            stat_value = stat['base_stat']
            base_stats[stat_name] = stat_value

        # create the dict format, store data in the master dict
        master_dict[name] = {
            "type1": type1,
            "type2": type2,
            "types": types,
            "base_experience": base_exp,
            "abilities": abilities,
            "moves": moves,
            "base_stats": base_stats
        }

    df = pd.DataFrame(master_dict)
    df = df.T # transpose the dataframe so that the we have pokemon per row rather than per col

    # reset_index() resets the index and turns it into a col
    # this allows us to have pokemon name as a col, rather than an index
    df_reset = df.reset_index()
    df = df_reset.rename(columns={'index': 'pokemon'}) # rename the index to pokemon


    return df

## Q3
def count_type(df): 
    
    count_df = df[['pokemon', 'types']]

    exploded = df.explode('types') # explode the types column so we can count the number of each type
    count = exploded.groupby('types').size().sort_values(ascending=False) # group by type and count the number of each type
    
    # reset the index so we can access the columns
    # after using .size(), the the df is converted into a pandas series, where you cant access cols directly
    count_df = count.reset_index()
    count_df.columns = ['types', 'count'] # manually map the columns, so that we can see count and type
    
    print_tabulated(count_df)
    return count_df

## Q4
def avg_base_exp(data, count):

    df = data[['types', 'base_experience']] # create df from master df with relevant cols

    df = df.explode('types') # explode the types column so we can count the number of each type
    avg_exp = df.groupby('types')['base_experience'].sum().reset_index() # group by type and get the mean of base experience
    
    avg_exp = pd.merge(avg_exp, count, on='types', how='left') # merge the count of each type with the average base experience
    avg_exp['avg_base_exp'] = avg_exp['base_experience'] / avg_exp['count'] # calculate the average base experience

    highest_avg = avg_exp.iloc[0,[0, -2, -1]]
    print(highest_avg.to_string())
    return avg_exp

## Q5
def distinct_moves_abilities(df):

    # abilities
    df_abilities = df[['abilities']]
    df_abilities = df_abilities.explode('abilities')
    df_abilities = df_abilities.groupby('abilities').size().reset_index(name='count')
    
    print(df_abilities)


    # moves
    df_moves = df[['moves']]
    df_moves = df_moves.explode('moves')
    df_moves = df_moves.groupby('moves').size().reset_index(name='count')

    print(df_moves)
    
    return df_abilities, df_moves

## Q6
def groupby_type_distinct(df):
    # first we create the df with the columns we will need 
    type_moves = df[['type1', 'moves']]
    
    # explode the df on moves so we can iterate and aggregate on each move
    type_moves = type_moves.explode('moves').reset_index(drop=True)

    # group by 'type1' and count the frequency of each move
    move_counts = type_moves.groupby(['type1', 'moves']).size().reset_index(name='count')

    # sort by type1, and then count in ascending order
    # So that the highest count move is the first value for each type 
    move_counts.sort_values(by=['type1', 'count'], ascending=[False, False])

    # get a unique list of types
    types = df['type1'].unique()

    highest_moves = {}
    for t in types:
        # get the 1st value for each type
        highest_move = move_counts[move_counts['type1'] == t].iloc[0]

        highest_moves[t] = {
        'move': highest_move['moves'],
        'count': highest_move['count']
        }

    common_moves = pd.DataFrame(highest_moves)
    
    print("Highest moves:")
    print(common_moves)

    print("Move counts:\n(printing head(5) due to long size")
    print(move_counts.head(5))


    return move_counts, common_moves

## Q7.1
def top3_pokemon(df):
    top3_df = df[['pokemon', 'base_stats', 'types', 'moves']]
        
    # Sum all values in the base_stats dictionary
    top3_df['total_base_stats'] = top3_df['base_stats'].map(lambda x: sum(x.values()))

    # x
    top3_df = top3_df.explode('types')
    top3_df = top3_df.sort_values(by=['types', 'total_base_stats'], ascending=[False, False])

    print("Top 3 highest total base stats:")
    print(top3_df)

    # get a unique list of types
    types = top3_df['types'].unique()


    base_stats_moves = {}

    for t in types:
        # get the top 3 rows of base_stats for each type
        highest_exp = top3_df[top3_df['types'] == t].iloc[:3]


        base_stats_moves[t] = {
        'pokemon': list(highest_exp['pokemon']),
        'move': list(highest_exp['moves']),
        'total_base_stats': list(highest_exp['total_base_stats'])
        }

    output_df = pd.DataFrame(base_stats_moves)
    output_df = output_df.T

    print("Most diverse move set amongst top 3 pokemon:")
    print(output_df)

    return output_df

## Q7.2
def identify_diverse_moves(df): # takes input from func: top3_pokemon
    
    # reset index to allow col access
    df = df.reset_index(names='type')

    # Explode the 'move' column so each move list has its own row
    exploded_moves = df.explode('move')
    exploded_moves = exploded_moves.explode('move') # this is confusing, but the original moves was a list of lists, so we need to explode again

    # group the moves col back together, so we can get the unique values
    # this handling is needed because moves was a list of lists
    distinct_moves_per_type = exploded_moves.groupby('type')['move'].nunique().reset_index()


    distinct_moves_per_type.rename(columns={'move': 'distinct_moves_count'}, inplace=True)
    
    return distinct_moves_per_type.sort_values(by='distinct_moves_count', ascending=False)



if __name__ == "__main__":
    main()