import pandas as pd
import df_fuzzy_merge

# allow pandas to print all columns so we can see outputs
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# load source and target dataframes
source_df = pd.read_csv('college_stats_2022.csv')
target_df = pd.read_csv('college_stats_annual.csv')
position_df = pd.read_csv('2022_nfl_combine.csv')

source_df = source_df.drop(['playerId'], axis=1)  # no need for their key

# merge the category and stat type into a new column and drop original columns
source_df['new_stat'] = source_df['category'] + '_' + source_df['statType']
source_df = source_df.drop(['category', 'statType'], axis=1)  # drop unneeded data

print(position_df)
print(position_df.columns)

''' 
    this is a bit hacky. pivot_table doesn't do well with multiple index columns so I'll combine player and college
    using * as a deliminator and then split them out later
'''

source_df['player_college'] = source_df['player'] + '*' + source_df['college']

# pivot the data to be wide
source_df = source_df.pivot_table(index=['player_college'], columns=['new_stat'], values=['stat'], aggfunc='first')

# this resets the multi index so that it's totally flat again
source_df.columns = source_df.columns.droplevel(0)
source_df.reset_index(inplace=True)

# split player and college back out
source_df['player'] = source_df['player_college'].str.split('*', expand=True)[0]
source_df['college'] = source_df['player_college'].str.split('*', expand=True)[1]
source_df = source_df.drop('player_college', axis=1)  # drop the combined data

# check the output
print(source_df.columns)
print(source_df.tail())

# drop unneeded columns
dropped = pd.read_excel('column_mapping.xlsx', sheet_name='dropped', header=None)
dropped = list(dropped[0])
source_df = source_df.drop(dropped, axis=1)


# one to one map columns
one_to_one = pd.read_excel('column_mapping.xlsx', sheet_name='one_to_one')
one_to_one_mapping = dict(zip(one_to_one['old'], one_to_one['new']))
source_df = source_df.rename(columns=one_to_one_mapping)


# copy columns
copied = pd.read_excel('column_mapping.xlsx', sheet_name='copy')

# this for loop iterates through the copied columns and assigns a name
for idx, row in copied.iterrows():
    source_df[row['copy']] = source_df[row['old']]


# calculate columns
source_df['defense_ast_tackles'] = source_df['defense_tackles'] - source_df['defense_solo_tackes']
source_df['passing_comp_pct'] = source_df['passing_completions'] / source_df['passing_attempts']
source_df['rushing_scrim_tds'] = source_df['receiving_rec_td'] + source_df['rushing_rush_td']
source_df['rushing_scrim_yds'] = source_df['receiving_rec_yards'] + source_df['rushing_rush_yds']
source_df['receiving_scrim_tds'] = source_df['receiving_rec_td'] + source_df['rushing_rush_td']
source_df['receiving_scrim_yds'] = source_df['receiving_rec_yards'] + source_df['receiving_rush_yds']

# assign data
assigned = pd.read_excel('column_mapping.xlsx', sheet_name='assigned')

# this for loop goes through the assigned data and assigns a value to the entire column, usually null
for idx, row in assigned.iterrows():
    source_df[row['Column']] = row['Value']

# drop the teams out, which has a space before them for some reason
source_df = source_df[source_df['player'] != ' Team']


# how to check to make sure everything aligns
df_set = set(source_df.columns)  # create a set of the first dataframes columns
target_df_set = set(target_df.columns)  # create a set of the target dataframe column

print('the difference between the new columns and old columns are: ')
print(df_set - target_df_set)
print('the difference between the new columns and old columns are: ')
print(target_df_set-df_set)

print("The two datasets columns align: ", set(source_df.columns) == set(target_df.columns))

# save the output
source_df = source_df[target_df.columns]
source_df.to_csv('2022_college_stats.csv', index=False)
