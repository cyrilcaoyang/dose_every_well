A1_x = 80
A1_y = 288
# those are the CNC coordinates

dx = -30
dy = -25

num_rows = 3
num_cols = 4

letters = "ABCD"

well_dict = {}

for num in range(num_cols):

    # actual location coordinates are computed with the raw index
    well_y = A1_y + (num)*dx

    for i_lett in range(num_rows):
        # actual location coordinates are computed with the raw index
        well_x = A1_x + (i_lett)*dy

        lett = letters[i_lett]
        # add 1 to the displayed well name
        well_dict[f"{lett}{num+1}"] = [well_x, well_y]

# keys are ordered columns first
print(well_dict)
