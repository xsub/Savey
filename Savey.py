#!/bin/env python3
# (c) 2022 Linbedded Savey//PyQt5

#import gc
import os.path
import subprocess
import sys
import time
import os
import platform

# PyQt5 imports
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QDateTime, QObject, QRegExp, QSettings, QTimer, Qt
from PyQt5.QtWidgets import QAction, QApplication, QDesktopWidget, QMainWindow, QMenu, QMessageBox
from PyQt5.QtWidgets import QCheckBox, QComboBox, QGridLayout, QLabel, QLineEdit
from PyQt5.QtWidgets import QProgressBar, QPushButton, QScrollArea, QSpinBox, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage

# Custom modules
import SaveyLED
import SaveySftp
import SaveyTree

# Globals
globals()["window"] = None
globals()['transfer_scale'] = 10  # TODO: move to Settings
globals()['transfer_inscale'] = 0 #1
globals()['transfers_done'] = 0
globals()['FILE_HASH'] = {'root': []}
globals()['LOCAL_LIST'] = []

class Settings():

    def __init__(self, vendor, programName):
        self.script_name = os.path.basename(__file__)
        # Read Settings
        settings = QSettings(vendor, programName)
        self.code_version = settings.value("code_version", "0.726")
        __version__ = self.code_version
        self.host_name = settings.value("host_name", "freezer")
        self.host_port = settings.value("host_port", "22")
        self.user_name = settings.value("user_name", "pablo")


class Savey_SFTP(QtCore.QObject):

    update_status_signal = QtCore.pyqtSignal(bool)

    def __init__(self, conf):
        super(Savey_SFTP, self).__init__()
        self.setObjectName(conf.host_name)

        # Create SaveSftp object
        self._sftp = SaveySftp.SaveySftp(conf.host_name)
        # Connect SFTP
        self._status = None
        self._sftp.define_con(conf.host_name, conf.user_name)
        self._sftp.con()

        # Timer
        self.timer = QTimer()
        self.timer.setInterval(100)  # 100 ms

        # Connect Signals
        self.timer.timeout.connect(self.on_check_status)

        # Set initial path
        # self._sftp.set_path("/RAID1_HOME/_AUTOMATED_/10.0.0.17/")
        #self._sftp.set_path("/tmp/")
        self._sftp.set_path("/RAID1_HOME/_AUTOMATED_/android/")

    def set_widget(self, widget):
        self._widget = widget

    def update_label(self, text):
        self._widget.setText(text)

    @QtCore.pyqtSlot()
    def on_clean_up_action(self):
        print("Savey_SFTP: received clean up message")   # {self}")
        if self._sftp.connected:
            self._sftp.close_con()

    def on_check_status(self):
        self._status = self._sftp.is_connected()
        # print(f"on_check_status()={status}")
        self.update_status_signal.emit(self._status)

    def connect_status_signal(self):
        w = globals()["window"]
        self.update_status_signal.connect(w.on_status_update)
        self.timer.start()


class Ui(QtWidgets.QMainWindow):

    prev_con_stat = False

    clean_up_signal = QtCore.pyqtSignal(str)
    button_press_signal = QtCore.pyqtSignal(str)

    def __init__(self, conf, sftp):
        # Init Super QMainWindow
        super(Ui, self).__init__()

        # UI
        uic.loadUi('Savey_mainwindow.ui', self)

        # Find elements
        self.constr_QLE = self.findChild(QLineEdit, "QLE_SSH_args")
        # Find Status line
        self.status_QLE = self.findChild(QLineEdit, "STATUS_lineEdit")
        # Find Info line
        self.info_QLE = self.findChild(QLineEdit, "INFO_lineEdit")
        # Find Exif info box
        #self.exif_QLV = self.findChild(QListView, "EXIF_list_view")

        # Find ProgressBar
        self.progressbar = self.findChild(QProgressBar, "TRANSprogressBar")
        # Find Checkbox
        cb = self.findChild(QCheckBox, "TRANSSCALEDcheckBox")
        # Find SpinBox and set it
        sb = self.findChild(QSpinBox, "TRANSSCALEDspinBox")
        sb.setValue(globals()['transfer_scale'])        

        # Connect Signals
        self.clean_up_signal.connect(sftp.on_clean_up_action)
        cb.stateChanged.connect(self.on_trans_scaled)
        sb.valueChanged.connect(self.on_trans_scaled)

        # Geometry and Title
        self.setGeometry(50, 50, 1050, 800)
        self.setWindowTitle("Savey (PyQt5(UI)/Fabric(SFTP)")

        # Alignment
        # scr = self.findChild(QScrollArea, "PIC_scrollArea")
        # scr.setAlignment(Qt.AlignCenter)
        # label = self.findChild(QLabel, "PIClabel")
        # label.setAlignment(Qt.AlignCenter)

        # Center
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        # Button
        b = self.findChild(QPushButton, "aButton")
        # b.clicked.connect(self.on_button_clicked)
        # b.clicked.connect(lambda text: self.constr_QLE.setText(self.constr_QLE.text()+"."))
        b.clicked.connect(self.on_connection_toggle)

        # LED
        self.led = SaveyLED.SaveyLED()
        grid = self.findChild(QGridLayout, "LEDgridLayout_")
        grid.addWidget(self.led)

        # Menu
        m = self.findChild(QMenu, "menuSavey")
        info = QAction("Info", self)
        info.setShortcut("Ctrl+I")
        m.addAction(info)
        m.triggered[QAction].connect(self.show_info_dialog)

        # Find Combo/TREE VBoxLayout
        self.v_layout = self.findChild(QVBoxLayout, "TREEverticalLayout")

        # QComboBox
        combo = self.findChild(QComboBox, "DIRcomboBox")
        # if not self.sftp.result == None:
        #    for item in self.sftp.result:
        #        combo.addItem(item)
        combo.resize(200, 20)
        self.v_layout.addWidget(combo)
        combo.activated[str].connect(self.on_combo_changed)

        # Tree
        tree = SaveyTree.SaveyTree(self)
        tree.createTree()
        tree.tree.resize(300, 350)

        # self.current_files.clear()
        self.current_files = []

        # sfp list to Combo
        if sftp._sftp.is_connected():
            sftp._sftp.ls_path()
            if sftp._sftp.result is not None:
                for item in sftp._sftp.result:
                    # combo.addItem(item)
                    self.current_files.append(item)
                    # DBG: print(f"L item={item}")
        else:
            b = self.findChild(QPushButton, "aButton")
            b.setText("ERROR: Not connected")

        self.current_files.sort()
        for item in self.current_files:
            combo.addItem(item)
            # DBG: print(f"C item={item}")

        # Create QRegExp object for quicker processing of ImageMagick's identify results
        self.rx = QRegExp("([-_0-9a-zA-Z/\.]+)\s(\w+)\s(\d+)x(\d+)\s.*(\d+\.?\d+M?B)")

        # Assign
        self.tree = tree
        self.combo = combo

        # Show
        self.show()

    def on_trans_scaled(self):
        cb = self.findChild(QCheckBox, "TRANSSCALEDcheckBox")
        # cb = self.findChild(QCheckBox, "TRANSSCALEDcheckBox")
        # print(cb.checkState())
        globals()['transfer_inscale'] = cb.checkState()
        sb = self.findChild(QSpinBox, "TRANSSCALEDspinBox")
        # print(f"sb.value={sb.value()}")
        globals()['transfer_scale'] = sb.value()

    def on_combo_changed(self, text):
        # self.qlabel.setText(text)
        # self.qlabel.adjustSize()

        self.subdirectory = text

        sftp._sftp.ls_path(sftp._sftp.path+text)
        self.tree.clear()
        sorted_res = sftp._sftp.result
        sorted_res.sort()
        self.tree.update(sorted_res)
        # if not self.tree.filename == None:
        #    self.sftp.get(self.sftp.path+self.tree.filename, "/tmp/"+self.tree.filename)
        #    self.pixmap.load("/tmp/"+self.tree.filename)
        # else:
        #    print ("Pic not loaded")

    def show_info_dialog(self, menu_item):

        print(f"Menu item: {menu_item.text()} was triggered")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Information")
        msg.setText("<b>SSH Connection status</b>")
        msg.setInformativeText(f"<b>Hostname:</b> {conf.host_name} <br> <b>Port:</b> {conf.host_port} <br> <b>User:</b> {conf.user_name} <br> <b>Server's uname:</b> <br> {sftp._sftp.host_uname}")
        _client_ver = sftp._sftp.client_ssh_ver
        _host_ver = sftp._sftp.host_ssh_ver
        msg.setDetailedText(f"Server SSH (client program):\n{_host_ver}\nPython Client SSH (library): {_client_ver}\n\n\
Transfers done: {globals()['transfers_done']}\nBytes transferred: -1\nErrors: -1")
        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec_()
        #printf("value of pressed message box button: {retval}")

    def on_connection_toggle(self):
        print(f"sftp._sftp.is_connected={sftp._sftp.is_connected()}")
        if sftp._sftp.is_connected() is not None:
            if sftp._sftp.is_connected() is True:
                sftp._sftp.close_con()
                t = "Connect"
            else:
                sftp._sftp.close_con()
                sftp._sftp.con()
                t = "Disconnect"
        print(t)
        b = self.findChild(QPushButton, "aButton")
        b.setText(t)

    def cleanup_exit(self):
        # do clean: close connection etc
        # self._sftp.close_con()
        self.hide()
        # print("Ui: Hiding MainWindow; Emitting clean_up_signal!")
        self.clean_up_signal.emit("Clean Up Signal")
        QtWidgets.QApplication.processEvents()
        time.sleep(1)

    def closeEvent(self, event):
        self.cleanup_exit()
        print(f"Terminating {conf.script_name} (v. {conf.code_version})")

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()

    @QtCore.pyqtSlot(bool)
    def on_status_update(self, is_con):
        # print(is_con)

        if Ui.prev_con_stat != is_con:
            if is_con:
                self.led.setPixmap(self.led.pix_led_green)
                self.led.startAnimation()
                # print("setting LED green")
            else:
                self.led.setPixmap(self.led.pix_led_red)
                self.led.startAnimation()
                # print("setting LED red")

            Ui.prev_con_stat = is_con

    @QtCore.pyqtSlot(str)
    def on_filename_update(self, filename):
        print(f"{__file__}@on_file_name_update: filename={filename}")
        # sftp.getfo(remotepath, fl, callback=None, prefetch=True)
        print("F: " + sftp._sftp.path+filename + " | /tmp/test.jpg")

        # Bench the Download
        self.dnld_start = time.time()

        # Support Scaled Download
        _scale=globals()['transfer_scale']  # temp variable

        # Set path
        filename_no_ext=filename.split(".", 1)[0]
        filename_ext=filename.split(".", 1)[1]
        tgt_path = "/tmp"  # temporary path -> TODO!
        conv_path = "/tmp"  # temporary path -> TODO!
        self.cnv_tmp_path = (f"{conv_path}/{filename_no_ext}-{_scale}.{filename_ext}")
        tgt = (f"{tgt_path}/{filename_no_ext}-{_scale}.{filename_ext}")
        print(f"tgt: {tgt}")

        l = globals()['LOCAL_LIST']
        l.append(tgt)

        f = open(tgt, "wb")  # SFTP transfers all content in binary mode

        p = sftp._sftp.path + self.subdirectory + "/" + filename

        # Get the picture info by running ImageMagick's `identify' command on remote host
        pic_ident = sftp._sftp.file_info(p)
        # Process output
        if pic_ident != "ERROR":
            self.info_QLE.setText(pic_ident)
            self.process_pic_ident(pic_ident)

        if globals()['transfer_inscale'] > 0 and _scale != 100:

            print(f"{__file__}@on_file_name_update: path={p}; globals()['transfer_scale']={_scale}")
            res = sftp._sftp.c.run(f"convert -scale {_scale}% {p} {self.cnv_tmp_path}")
            print(res.stdout)
            sftp._sftp.s.getfo(self.cnv_tmp_path, f, callback=self.on_pic_dnld)
        else:
            sftp._sftp.s.getfo(p, f, callback=self.on_pic_dnld)

        f.close()

    def process_pic_ident(self, ident_line):
        # /tmp/test.jpg JPEG 274x365 274x365+0+0 8-bit sRGB 112348B 0.000u 0:00.000
        self.rx.indexIn(ident_line)
        _file = self.rx.cap(1); _format = self.rx.cap(2); _width = self.rx.cap(3); _height = self.rx.cap(4); _size = self.rx.cap(5)
        # print(f"file: {_file} format: {_format} width: {_width} height: {_height}")
        # Store size in Global hash using filename as key
        h = globals()['FILE_HASH']
        h[_file]=[_width, _height, _format, _size]
        # print(h)

    def on_pic_dnld(self, got, to_get):
        #
        # print(f"{__file__}@on_pic_dnld() {got}/{to_get}")
        #
        if got == to_get:
            # account
            globals()['transfers_done']+=1
            # progress bar
            self.progressbar.setValue(100)
            #
            # timing
            dnld_end = time.time()
            dnld_time = round(dnld_end - self.dnld_start, 2)
            scale_text = ""
            if globals()['transfer_inscale'] > 0 and globals()['transfer_scale'] != 100:
                scale_text = (f", scaled to {globals()['transfer_scale']}%")
                # Remove the temporary convert file self.cnv_tmp_path on remote (source) server

                #_res = sftp._sftp.s.remove(self.cnv_tmp_path)
                _res = sftp._sftp.remove(self.cnv_tmp_path)
            # Update status line with optional scale_text
            self.status_QLE.setText(f"Downloaded {got} bytes in {dnld_time}s{scale_text}.")

            # Load the newly written pic file

            # Find UI elements
            label = self.findChild(QLabel, "PIClabel")
            localstatus_QLE = self.findChild(QLineEdit, "LOCALSTATUS_lineEdit")

            # Get local files list and read last element
            l = globals()['LOCAL_LIST']
            _dnld_tgt = l[-1]
            print(f"_dnld_tgt:{_dnld_tgt}")
            # Update Stat
            # print(f"_dnld_tgt = {_dnld_tgt}")
            result = subprocess.run(["identify", _dnld_tgt], capture_output=True, text=True)
            print(f"stdout: {result.stdout}")
            rx = QRegExp("([-_0-9a-zA-Z/\.]+)\s(\w+)\s(\d+)x(\d+)\s.*(\d+\.?\d+M?B)")
            rx.indexIn(result.stdout)
            _file=rx.cap(1); _format=rx.cap(2); _width=rx.cap(3); _height=rx.cap(4); _size=rx.cap(5)
            localstatus_QLE.setText(f"{_file}, {_width}x{_height}, {_size}")

            # QImage
            i = QImage.load("_dnld_tgt", "jpeg")

            print(f"RES: {i.width}x{i.height}")

            # Create pixmap            
            #label.resize(274, 365)  # TODO
            #label.resize(int(_width), int(_height))  # TODO
            #pixmap = QPixmap(_dnld_tgt)
            pixmap = QPixmap(i)
            #Set new picture
            label.setPixmap(pixmap)
            # Alignment
            #label.setAlignment(Qt.AlignCenter)
            #if int(_height)>int(_width):
            #    label.move(50,20)
            #else:
            #    label.move(10,75)

            # update EXIF info
            #self.exif_QLV.


            # Create an empty model for the list's data
            #model = QStandardItemModel()
            #model.removeRows( 0, model.rowCount() )

            # for food in foods:
            # Create an item with a caption
            #item = QStandardItem(food)

            # Add a checkbox to it
            #item.setCheckable(True)

            # Add the item to the model
            #model.appendRow(item)

            #scr = self.findChild(QScrollArea, "PIC_scrollArea")
            #scr.setAlignment(Qt.AlignCenter)

            # pixmap_resized = pixmap.scaled(800, 600, QtCore.Qt.KeepAspectRatio)
            # label.setPixmap(pixmap_resized)
        else:
            percent = got * 100 / to_get
            self.progressbar.setValue(int(percent))
            self.status_QLE.setText(f"Downloading: {got} of {to_get} bytes...")


if __name__ == "__main__":

    # Check prerequisites: local ImageMagick - local ImageMagick is NOT really required :-)
    result = None
    try:
        result = subprocess.run(["identify", "-version"], capture_output=True, text=True)
        #example of result to process:
        #Version: ImageMagick 6.9.10-23 Q16 x86_64 20190101 https://imagemagick.org
    except Exception as err:
        print(f"NON-CRITICAL EXCEPTION: {err}")

    rx_v = ''
    if result is not None and result.returncode == 0:
        if platform.system == 'Linux':
            rx_v = QRegExp("Version: (ImageMagick.*\d{8})")
        elif platform.system == 'Darwin':
            rx_v = QRegExp("Version: (.*)https://imagemagick.org")
        else:
            print(f"Unsupported platform: {platform.system()}")
            rx_v = None

        if rx_v is not None:
            rx_v.indexIn(result.stdout)
            print(f"Found {rx_v.cap(1)}.")
        else:
            print("ImageMagick: version not checked.")
    else:
        print("No ImageMagick program found on local machine.")

    # Config
    conf = Settings("Linbedded", "Savey")
    # App
    app = QApplication(sys.argv)
    # SFTP object
    sftp = Savey_SFTP(conf)

    # MainWindow from Ui
    window = Ui(conf, sftp)
    globals()["window"] = window

    # Connect Signal
    sftp.connect_status_signal()

    # Update the Connect String
    sftp.set_widget(window.findChild(QLineEdit, "QLE_SSH_args"))

    if sftp._sftp.connected:
        str_SSH_args = conf.host_name +"@" + conf.user_name + ":" + conf.host_port + ":" + sftp._sftp.path
        sftp.update_label(str_SSH_args)
    else:
        sftp.update_label("Not connected")
        pass

    sys.exit(app.exec_())
