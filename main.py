from src.core.cerebr_ai import CerebrAI
from src.ui.uibby import UibbyApp

def main():

    cerebro = CerebrAI()
    app = UibbyApp(cerebro)
    app.mainloop()

if __name__ == "__main__":
    main()