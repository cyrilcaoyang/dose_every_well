A1_x = 24
A1_y = 24

dx = -2
dy = -3

num_rows = 4
num_cols = 6

letters = "ABCD"

well_dict = {}

for num in range(num_cols):

    # actual location coordinates are computed with the raw index
    well_x = A1_x + (num)*dx

    for i_lett in range(num_rows):
        # actual location coordinates are computed with the raw index
        well_y = A1_y + (i_lett)*dy

        lett = letters[i_lett]
        # add 1 to the displayed well name
        well_dict[f"{lett}{num+1}"] = [well_x, well_y]

# keys are ordered columns first
print(list(well_dict.keys()))
