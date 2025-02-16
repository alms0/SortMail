import functions
from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as pyplot
import configparser
import time
import logging
import os, shutil

def write_list_to_ini(section_name, list_items):
    config = configparser.ConfigParser()
    config.read('config.ini')
    config[section_name] = {}
    for i, item in enumerate(list_items):
        key = f"item{i}"
        config[section_name][key] = item
    with open('config.ini', "w") as configfile:
        config.write(configfile)

def read_list_from_ini(section_name):
    config = configparser.ConfigParser()
    config.read('config.ini')
    list_items = []
    i = 0
    while True:
        key = f"item{i}"
        if key in config[section_name]:
            list_items.append(config[section_name][key])
            i += 1
        else:
            break
    return list_items

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Einstellungen")
        self.setGeometry(500, 500, 400, 150)
        layout = QtWidgets.QVBoxLayout(self)

        # Text boxes
        tb1_label = QtWidgets.QLabel("Posteingang")
        tb2_label = QtWidgets.QLabel("Ablageordner")
        tb3_label = QtWidgets.QLabel("Ausgeschlossene Ordner")
        self.tb_inbox_path = QtWidgets.QLineEdit()
        self.tb_archive_path = QtWidgets.QLineEdit()
        self.tb_excluded_folders = QtWidgets.QTextEdit()
        font=self.tb_excluded_folders.font()
        self.tb_excluded_folders.setMaximumHeight(font.pointSize()*8)
        layout.addWidget(tb1_label)
        layout.addWidget(self.tb_inbox_path)
        layout.addWidget(tb2_label)
        layout.addWidget(self.tb_archive_path)
        layout.addWidget(tb3_label)
        layout.addWidget(self.tb_excluded_folders)

        # Confirmation button
        self.button = QtWidgets.QPushButton("Ok")
        self.button.clicked.connect(self.accept)
        layout.addWidget(self.button)


    
    
class Main_Window(QtWidgets.QWidget):
    # InboxPath=""
    # ArchivePath=""
    current_file=""
    def __init__(self):
        logging.basicConfig(level=logging.ERROR)

        start_time = time.time()
        config = configparser.ConfigParser()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        config.read('config.ini')
        self.InboxPath = config.get('DEFAULT', 'InboxPath').rstrip("/") + "/"
        self.ArchivePath = config.get('DEFAULT', 'ArchivePath').rstrip("/") + "/"
        self.excluded_directories=read_list_from_ini('EXCLUDED_DIRS')
        
        self.new_mail = sorted(functions.find_pdf_files(self.InboxPath))
        self.archived_PDF_list = functions.find_pdf_files(self.ArchivePath, self.excluded_directories)
        
        self.buffer_list = []
        self.is_loading = False
        super().__init__()
        self.setWindowTitle("SortMail")
        self.setGeometry(50, 50, 1000, 1000)
        # Create the layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)
        
        # labels and text boxes
        label_1 = QtWidgets.QLabel("aktueller Name:")
        self.label_current_file = QtWidgets.QLabel()
        self.label_current_file.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(label_1, 0, 0, QtCore.Qt.AlignBottom)
        layout.addWidget(self.label_current_file, 1, 0, QtCore.Qt.AlignTop)
        #font = self.label_current_file.font()
        self.pb_file_progress= QtWidgets.QProgressBar()
        self.pb_file_progress.setGeometry(50, 50, 200, 25)
        layout.addWidget(self.pb_file_progress,1,0,QtCore.Qt.AlignBottom)
        
        label_2 = QtWidgets.QLabel("Datum:")
        self.label_date = QtWidgets.QLabel()
        self.label_date.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(label_2, 2, 0, QtCore.Qt.AlignBottom)
        layout.addWidget(self.label_date, 3, 0, QtCore.Qt.AlignTop)
        
        
        label_3 = QtWidgets.QLabel("relativer Ablageordner")
        self.cb_archive_folder = QtWidgets.QComboBox()
        self.cb_archive_folder.setEditable(True)
        layout.addWidget(label_3, 4, 0, QtCore.Qt.AlignBottom)
        layout.addWidget(self.cb_archive_folder, 5, 0, QtCore.Qt.AlignTop)
        self.btn_choose_folder = QtWidgets.QPushButton("...")
        self.btn_choose_folder.clicked.connect(self.choose_folder)
        self.btn_choose_folder.setFixedSize(30, 20)
        layout.addWidget(self.btn_choose_folder, 4, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        
        #self.cb_archive_folder.setMaximumHeight(font.pointSize() * 8)
        
        label_4 = QtWidgets.QLabel("neuer Name")
        self.cb_new_name = QtWidgets.QComboBox()
        self.cb_new_name.setEditable(True)
        layout.addWidget(label_4, 6, 0, QtCore.Qt.AlignBottom)
        layout.addWidget(self.cb_new_name, 7, 0, QtCore.Qt.AlignTop)
        
        # PDF preview
        
        
        pyplot.figure(figsize=(20, 20), dpi=72)
        self.figure = pyplot.Figure()
        self.subplot = self.figure.add_subplot(111)
        self.subplot.axis('off')
        self.figure.tight_layout()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, 0, 1, 20, 1)
        
        #text boxes and PDF preview stretch in 1:2 ratio:
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)
        
        
        # buttons
        self.button_1 = QtWidgets.QPushButton("Archivieren")
        self.button_1.clicked.connect(self.show_confirmation_dialog)
        layout.addWidget(self.button_1, 8, 0, QtCore.Qt.AlignHCenter)
        self.button_1.setChecked = True
        enter_key = QtWidgets.QShortcut(QtGui.QKeySequence("Return"), self)
        enter_key.activated.connect(self.show_confirmation_dialog)
        
        self.button_2 = QtWidgets.QPushButton("Einstellungen")
        self.button_2.clicked.connect(self.show_settings_dialog)
        layout.addWidget(self.button_2, 19, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft)
        
        self.button_3 = QtWidgets.QPushButton("Überspringen")
        self.button_3.clicked.connect(self.load_new_file)
        layout.addWidget(self.button_3, 8, 0, QtCore.Qt.AlignRight)
        
        
        if not self.new_mail==[]:
            self.thread=functions.BackgroundTask([self.new_mail, self.InboxPath, self.archived_PDF_list])
            self.thread.start()
            self.thread.add_to_buffer.connect(self.add_to_buffer)
            self.thread.update_progress.connect(self.update_progress)
            self.load_new_file()
            processing_time = time.time() - start_time
            print("Initialization time:", processing_time, "seconds")
        else:
            self.label_current_file.setText("keine weiteren Dokumente")
            self.pb_file_progress.hide()
        
        self.confirmation_dialog = QtWidgets.QMessageBox()
        self.confirmation_dialog.setWindowTitle("Archivieren")
        self.confirmation_dialog.setText("Datei speichern?")
        self.confirmation_dialog.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Cancel)
        self.confirmation_dialog.setDefaultButton(QtWidgets.QMessageBox.Save)
        
        
        
    def add_to_buffer(self, buffer_item):
        self.buffer_list.append(buffer_item)
        if self.is_loading:
            self.load_new_file()
    def update_progress(self, value):
        if self.is_loading:
            self.pb_file_progress.setValue(value)
            if value == 100:
                self.pb_file_progress.hide()
            else:
                self.pb_file_progress.show()
    
    def load_new_file(self):
        if self.buffer_list == []:
            if not hasattr(self, 'thread') or not self.thread.isRunning():
                print("keine weiteren Dokumente")
                self.label_current_file.setText("keine weiteren Dokumente")
                self.pb_file_progress.hide()
                self.cb_archive_folder.clear() 
                self.cb_new_name.clear()
                self.label_date.setText("")
                self.figure.clf()
                self.canvas.draw()
            else:    
                self.label_current_file.setText("lädt...")
                self.is_loading=True
                self.pb_file_progress.show()
                self.thread.user_is_waiting() #speeds up background thread
        else:
            self.is_loading=False
            self.pb_file_progress.hide()
            self.thread.user_is_not_waiting() #makes GUI more responsive
            self.label_current_file.setText(self.buffer_list[0][0])       
            self.label_date.setText(self.buffer_list[0][1])
            suggested_folders=self.buffer_list[0][2]
            suggested_folders=[x[len(self.ArchivePath):] for x in suggested_folders] #remove absolute path prefix
            self.cb_archive_folder.clear()            
            self.cb_archive_folder.addItems(suggested_folders)
            self.cb_archive_folder.setCurrentIndex(0)
            suggested_names=self.buffer_list[0][3]
            self.cb_new_name.clear()
            self.cb_new_name.addItems(suggested_names)
            self.cb_new_name.setCurrentIndex(0)
            rendered_image=self.buffer_list[0][4]
            self.subplot.imshow(rendered_image)
            self.canvas.draw()
            self.current_file = self.buffer_list.pop(0)[5]
        
    def show_confirmation_dialog(self):
        full_file_name=self.ArchivePath + self.cb_archive_folder.currentText().rstrip("/") + "/" + self.cb_new_name.currentText() +".pdf"
        old_file_name=self.current_file
        if os.path.exists(full_file_name):
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Es existiert bereits eine Datei diesem Namen.")
            msg.setWindowTitle("Fehler")
            msg.exec_()
        else:
            self.confirmation_dialog.setText("Datei von\n\n" + old_file_name +"\n\n nach\n\n"+ full_file_name + "\n\n verschieben?")
            if self.confirmation_dialog.exec_() == QtWidgets.QMessageBox.Save:
                shutil.move(old_file_name, full_file_name)
                self.load_new_file()
                print("Moving\n" + old_file_name +"\n to\n" + full_file_name)
                
        
    def show_settings_dialog(self):
        #fill text boxes with current values
        settings_dialog = SettingsDialog()
        settings_dialog.tb_inbox_path.setText(self.InboxPath)
        settings_dialog.tb_archive_path.setText(self.ArchivePath)
        settings_dialog.tb_excluded_folders.setText(";".join(self.excluded_directories))
        
        if settings_dialog.exec_() == QtWidgets.QDialog.Accepted:
            # save the settings
            self.InboxPath=settings_dialog.tb_inbox_path.text().rstrip("/") + "/"
            self.ArchivePath=settings_dialog.tb_archive_path.text().rstrip("/") + "/"
            self.excluded_directories=settings_dialog.tb_excluded_folders.toPlainText().split(";")
            
            write_list_to_ini('EXCLUDED_DIRS', self.excluded_directories)
            config = configparser.ConfigParser()
            config.read('config.ini')
            config['DEFAULT']['InboxPath'] = self.InboxPath
            config['DEFAULT']['ArchivePath'] = self.ArchivePath
                        
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
    
    def choose_folder(self):
        folder_dialog=QtWidgets.QFileDialog()
        folder_dialog.setDirectory(self.ArchivePath)
        self.cb_archive_folder.setCurrentText(folder_dialog.getExistingDirectory(self, "Ordner wählen").lstrip(self.ArchivePath))
        
        
        
        
