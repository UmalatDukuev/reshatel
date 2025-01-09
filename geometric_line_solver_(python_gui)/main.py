import sys

from gui import App


def main():
    app = App(sys.argv)
    sys.exit(app.start())


if __name__ == '__main__':
    main()
