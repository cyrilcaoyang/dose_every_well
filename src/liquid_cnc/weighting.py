from datetime import datetime
from matterlab_balances import SartoriusBalance
from pathlib import Path

# bal = SartoriusBalance("COM3")
# record = Path(__file__).parent/f"record{datetime.now().strftime("%Y-%m-%d")}.log"

# while True:
#     inp = input("Input T/t for tare, W/w for weigh, Q/q for quit\n")
#     if inp in ["Q","q"]:
#         break
#     elif inp in ["T","t"]:
#         bal.tare()
#     elif inp in ["W", "w"]:
#         name = input("Sample name:\n")
#         weight = bal.weigh()
#         print(f"{weight:.4f}")
#         with open(record, "a") as f:
#             f.write(f"{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}, {name}, {weight:.4f}\n")


if __name__ == "__main__":
    bal = SartoriusBalance(com_port="COM3")
    weigh = bal.weigh()
    print((f"weigh"))