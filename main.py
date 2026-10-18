"""
AVI Conversor - Punto de entrada.

Ejecuta: python main.py
"""

from src.app import AVIConversorApp


def main():
    app = AVIConversorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
