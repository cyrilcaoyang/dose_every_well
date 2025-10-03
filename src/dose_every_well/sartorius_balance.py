from datetime import datetime
from matterlab_balances import SartoriusBalance
from pathlib import Path

# if __name__ == "__main__":
bal = SartoriusBalance(com_port="/dev/ttyUSB1")
weigh = bal.weigh()
print((f"weigh"))