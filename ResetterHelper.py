#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author Gaining AkA Jonathan Soivilus


from PyQt5 import QtCore, QtGui, QtWidgets
import subprocess
import sys
import os
import lsb_release
import pwd
import platform


class ResetterHelper(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(ResetterHelper, self).__init__(parent)
        self.setWindowTitle("Resetter Helper v1.2")
        self.os_info = lsb_release.get_distro_information()
        os_information = '{} {}'.format(self.os_info['ID'], self.os_info['RELEASE'])
        os_info_label = QtWidgets.QLabel(os_information)
        self.lbl2 = QtWidgets.QLabel("File1")
        self.lbl3 = QtWidgets.QLabel("File2")
        self.lbl4 = QtWidgets.QLabel("")
        self.btnCreateManifest = QtWidgets.QPushButton("Make Manifest")
        self.btnCreateUserlist = QtWidgets.QPushButton("Make Userlist")
        self.btnOpen1 = QtWidgets.QPushButton("Open First File")
        self.btnOpen2 = QtWidgets.QPushButton("Open Second File")
        self.btnCompare = QtWidgets.QPushButton("Compare Files")
        self.listView = QtWidgets.QListView(self)
        self.model = QtGui.QStandardItemModel(self.listView)
        self.msg = QtWidgets.QMessageBox(self)
        self.euid = os.geteuid()
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.blue)
        self.lbl4.setPalette(palette)
        horizontalLayout = QtWidgets.QHBoxLayout()
        horizontalLayout2 = QtWidgets.QHBoxLayout()
        horizontalLayout.addWidget(self.btnOpen1)
        horizontalLayout.addWidget(self.btnOpen2)
        horizontalLayout2.addWidget(self.lbl2)
        horizontalLayout2.addWidget(self.lbl3)

        verticalLayout = QtWidgets.QVBoxLayout(self)
        verticalLayout.addWidget(os_info_label)
        verticalLayout.addWidget(self.btnCreateManifest)
        verticalLayout.addWidget(self.btnCreateUserlist)
        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addLayout(horizontalLayout2)
        verticalLayout.addWidget(self.btnCompare)
        verticalLayout.addWidget(self.lbl4)
        verticalLayout.addWidget(self.listView)
        self.setLayout(verticalLayout)
        self.btnCreateManifest.clicked.connect(self.generateManifest)
        self.btnCreateUserlist.clicked.connect(self.generateUserlist)
        self.btnOpen1.clicked.connect(self.openFile1)
        self.btnOpen2.clicked.connect(self.openFile2)
        self.btnCompare.clicked.connect(self.compareFiles)
        self.file1 = None
        self.file2 = None
        if 'PKEXEC_UID' in os.environ:
            self.user = pwd.getpwuid(int(os.environ['PKEXEC_UID'])).pw_name
        elif self.euid == 0 and 'PKEXEC_UID' not in os.environ:
            self.user = os.environ['SUDO_USER']
        else:
            self.user = os.environ.get('USER')


    def checkForApt(self):
        apt_locations = ('/usr/bin/apt', '/usr/lib/apt', '/etc/apt', '/usr/local/bin/apt')
        if not any(os.path.exists(f) for f in apt_locations):
            self.showMessage("Apt Not Found",
                             "Apt could not be found, your distro does not appear to be Debian based.",
                             QtWidgets.QMessageBox.Warning)

    def generateManifest(self):
        try:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            p1 = subprocess.check_output(['dpkg', '--get-selections'])
            manifest = '_'.join((self.os_info['ID'], self.os_info['RELEASE'], \
                                 os.environ.get('XDG_CURRENT_DESKTOP'), platform.architecture()[0], ".manifest"))
            with open(manifest, 'w') as output:
                for line in p1.splitlines():
                    output.write(line.decode().split('\t', 1)[0] + '\n')
        except subprocess.CalledProcessError:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.showMessage("Error",
                             "an error has occured while generating manifest",
                             QtWidgets.QMessageBox.Critical)
        else:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.showMessage("Success",
                             "Your generated manifest can be found at {}".format(os.path.abspath(output.name)),
                             QtWidgets.QMessageBox.Information)

    def generateUserlist(self):
        try:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            cmd = subprocess.check_output(['bash', '-c', 'compgen -u'])
            userlist = '_'.join((self.os_info['ID'], self.os_info['RELEASE'], 'default-userlist',\
            os.environ.get('XDG_CURRENT_DESKTOP'), platform.architecture()[0]))

            with open(userlist, 'w') as output:
                for line in cmd.splitlines():
                    line = line.decode()
                    if not self.user in line:
                        output.writelines(line + '\n')
        except subprocess.CalledProcessError as e:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.showMessage("Error",
                             "an error has occured while getting users",
                             QtWidgets.QMessageBox.Critical, str(e))
        else:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.showMessage("Success",
                             "Your distro's userlist can be found at {}".format(os.path.abspath(output.name)),
                             QtWidgets.QMessageBox.Information)

    def openFile1(self):
        file1, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*)")
        if file1:
            self.file1 = file1
            self.lbl2.setText(str(file1).split('/')[-1])

    def openFile2(self):
        file2, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*)")
        if file2:
            self.file2 = file2
            self.lbl3.setText(str(file2).split('/')[-1])

    def compareFiles(self):
        self.model.clear()
        try:
            with open('difference', 'w') as output, open(self.file1, 'r') as file1, \
                    open(self.file2, 'r') as file2:
                diff = sorted(set(file1).difference(file2))
                if len(diff) > 0:
                    self.lbl4.setText("These are not found in {}".format(str(file2.name).split('/')[-1]))
                for line in diff:
                    output.writelines(line)
                    item = QtGui.QStandardItem(line.strip())
                    self.model.appendRow(item)
                self.listView.setModel(self.model)

        except Exception as e:
            pass

    def showMessage(self, title, message, icon, detail=None):
        self.msg = QtWidgets.QMessageBox()
        self.msg.setIcon(icon)
        self.msg.setWindowTitle(title)
        self.msg.setText(message)
        if detail is not None:
            self.msg.setDetailedText(detail)
        self.msg.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    screen = ResetterHelper()
    screen.show()
    screen.checkForApt()
    sys.exit(app.exec_())
