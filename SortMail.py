import GUI
import sys


if __name__ == "__main__":
    app = GUI.QtWidgets.QApplication(sys.argv)
    gui = GUI.Main_Window()   
    
    gui.show()
    sys.exit(app.exec_())