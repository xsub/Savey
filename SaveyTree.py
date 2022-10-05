# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

class SaveyTree(QWidget):

    filename_updated_signal = QtCore.pyqtSignal(str)

    def __init__(self, MainWindow):
        super().__init__()
        self.tree = QTreeWidget(MainWindow)
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.filename = None
        MainWindow.v_layout.addWidget(self.tree)

        # Signal to MainWindow
        self.filename_updated_signal.connect(MainWindow.on_filename_update)

    def clear(self):
        self.tree.clear()

    def update(self, result):
        root = QTreeWidgetItem(self.tree)
        root.setText(0, 'root')
        for item in result:
            child = QTreeWidgetItem(root)
            child.setText(0, item)
        self.tree.addTopLevelItem(root)

    def createTree(self):
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabel("Filenames")

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def on_item_clicked(self, it, col):
        self.filename = it.text(col)
        self.filename_updated_signal.emit(self.filename)
        print(f"{__file__}@on_item_clicked: filename={self.filename}")

    @QtCore.pyqtSlot(QWidget, list)
    def on_tree_hanged(self, result):
            #self.qlabel.setText(text)
            #self.qlabel.adjustSize()
            #result=self.sftp.ls_path(self.sftp.path+text)
            self.tree.clear()
            self.tree.update(result)
            ##if not self.tree.filename == None:
                ##self.sftp.get(self.sftp.path+self.tree.filename, "/tmp/"+self.tree.filename)
                ##self.pixmap.load("/tmp/"+self.tree.filename)
            ##else:
                ##print ("Pic not loaded")
