from logic import *
from PyQt6.QtWidgets import *
import qtmodern.styles
import qtmodern.windows


def main() -> None:
    app = QApplication([])
    qtmodern.styles.dark(app)

    window = Logic()
    window.center()  # centers window since qtmodern doesn't by default

    modern_window = CustomModernWindow(window)
    modern_window.setFixedSize(modern_window.size())  # sets window to fixed size since qtmodern overrides
    modern_window.show()
    app.exec()


if __name__ == '__main__':
    main()
