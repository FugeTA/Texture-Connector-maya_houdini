try:
    from PySide2 import QtWidgets,QtCore
except:
    from PySide6 import QtWidgets,QtCore
from .config import translation_dir  # 修正: config からインポート

class ErrorWindow(QtWidgets.QWidget):
    def __init__(self, eText, strings1, strings2, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.msgBox = QtWidgets.QMessageBox()  # メッセージボックス作成
        self.msgBox.setWindowTitle(self.tr("Error"))  # ウィンドウの名前
        self.msgBox.setObjectName("Error_window")  # ウィジェットとしての名前
        self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)  # アイコン
        # 各メッセージ
        messages = [self.tr('Not selected'),strings1+self.tr(' file not found.\nPlease check file path.\n"')+strings2+'"',self.tr('The image file and material name do not match.\n"'+strings1+'" is not applicable.')]
        self.msgBox.setText(messages[eText])  # メッセージ呼び出し
        self.ok = self.msgBox.addButton(QtWidgets.QMessageBox.Ok)  # ボタン作成
        self.clip = None # クリップボタンがない時用
    # クリップボードにコピー
    def toClipBoard(self,path):
        self.path = path
        self.clip = self.msgBox.addButton(self.tr('Copy to clipboard'),QtWidgets.QMessageBox.ActionRole)
    # 実行
    def openWindow(self):
        self.msgBox.exec()
        # クリップボードにコピーを選択したなら
        if self.msgBox.clickedButton() == self.clip:
            cb = QtWidgets.QApplication.clipboard()
            cb.setText(self.path)
        self.deleteLater() # オブジェクト削除

class MainWindow(QtWidgets.QWidget):
    def __init__(self, title=None, translator=None, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setWindowTitle(title)  # タイトル
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # deleteLater()の自動実行
        self.translator = translator  # 言語変更機能のため継承
        self.relativePath = False
        
        load = self.loadSettings()  # 設定の読み込み
        
        Mainlayout = QtWidgets.QVBoxLayout()  # メインのレイアウト
        # 言語選択
        layout2 = QtWidgets.QHBoxLayout()
        self.combobox1 = QtWidgets.QComboBox(self)
        self.combobox1.addItems(["日本語", "English"])
        self.combobox1.setCurrentIndex(load[2])
        self.combobox1.currentIndexChanged.connect(self.langSwitch)
        layout2.addWidget(self.combobox1)
        # リセットボタン
        self.button1 = QtWidgets.QPushButton(self.tr("reset"))
        self.button1.clicked.connect(self.pushed_button1)
        layout2.addWidget(self.button1)
        Mainlayout.addLayout(layout2)
        # マテリアル選択
        layout8 = QtWidgets.QHBoxLayout()
        self.combobox2 = QtWidgets.QComboBox(self)
        self.combobox2.addItems(["StandardSurface & aiStandardSurface", "RedShiftMaterial", "RedShiftStandardMaterial"])
        self.combobox2.setCurrentIndex(load[3])
        layout8.addWidget(self.combobox2)
        self.checkbox8 = QtWidgets.QCheckBox("UDIM")
        self.checkbox8.setChecked(load[0][7])
        layout8.addWidget(self.checkbox8)
        Mainlayout.addLayout(layout8)
        # テクスチャ選択
        layout3 = QtWidgets.QHBoxLayout()
        self.checkbox1 = QtWidgets.QCheckBox("BaseColor")
        self.checkbox1.setChecked(load[0][0])
        self.checkbox1.stateChanged.connect(self.disableButton)
        layout3.addWidget(self.checkbox1)
        self.checkbox2 = QtWidgets.QCheckBox("Metalness")
        self.checkbox2.setChecked(load[0][1])
        self.checkbox2.stateChanged.connect(self.disableButton)
        layout3.addWidget(self.checkbox2)
        self.checkbox3 = QtWidgets.QCheckBox("Roughness")
        self.checkbox3.setChecked(load[0][2])
        self.checkbox3.stateChanged.connect(self.disableButton)
        layout3.addWidget(self.checkbox3)
        Mainlayout.addLayout(layout3)
        # 改行
        layout4 = QtWidgets.QHBoxLayout()
        self.checkbox4 = QtWidgets.QCheckBox("Normal")
        self.checkbox4.setChecked(load[0][3])
        self.checkbox4.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox4)
        self.checkbox5 = QtWidgets.QCheckBox("Height")
        self.checkbox5.setChecked(load[0][4])
        self.checkbox5.stateChanged.connect(self.scaleVisible)
        self.checkbox5.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox5)
        self.checkbox6 = QtWidgets.QCheckBox("Emissive")
        self.checkbox6.setChecked(load[0][5])
        self.checkbox6.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox6)
        self.checkbox7 = QtWidgets.QCheckBox("Opacity")
        self.checkbox7.setChecked(load[0][6])
        self.checkbox7.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox7)
        Mainlayout.addLayout(layout4)
        # Heightスケール
        layout5 = QtWidgets.QHBoxLayout()
        self.textbox = QtWidgets.QLabel("Scale")
        self.textbox.setVisible(False)
        layout5.addWidget(self.textbox)
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.doubleSpinBox.setRange(0, 1)
        self.doubleSpinBox.setValue(load[4])
        self.doubleSpinBox.valueChanged.connect(self.setSliderV)
        self.doubleSpinBox.setSingleStep(0.1) 
        self.doubleSpinBox.setVisible(False)
        layout5.addWidget(self.doubleSpinBox)
        self.slider = QtWidgets.QSlider()
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.valueChanged.connect(self.setDSBV)
        self.slider.setVisible(False)
        layout5.addWidget(self.slider)
        Mainlayout.addLayout(layout5)
        # テクスチャパス
        layout6 = QtWidgets.QHBoxLayout()
        self.textbox2 = QtWidgets.QLineEdit("Texture Path")
        self.textbox2.setText(load[1])
        self.textbox2.editingFinished.connect(lambda: self.doRelativePath(self.textbox2.text()))
        layout6.addWidget(self.textbox2)
        self.button2 = QtWidgets.QPushButton("...")
        self.button2.clicked.connect(self.pushed_button2)
        layout6.addWidget(self.button2)
        Mainlayout.addLayout(layout6)
        # セパレーター
        self.spacerItem1 = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        Mainlayout.addItem(self.spacerItem1)
        self.frame = QtWidgets.QFrame()
        self.frame.setFrameShape(QtWidgets.QFrame.HLine)
        self.frame.setFrameShadow(QtWidgets.QFrame.Sunken)
        Mainlayout.addWidget(self.frame)
        # 実行ボタン
        layout7 = QtWidgets.QHBoxLayout()
        self.button3 = QtWidgets.QPushButton(self.tr("Connect"))
        self.button3.clicked.connect(self.pushed_button3)
        layout7.addWidget(self.button3)
        self.button4 = QtWidgets.QPushButton(self.tr("Close"))
        self.button4.clicked.connect(self.pushed_button4)
        layout7.addWidget(self.button4)
        Mainlayout.addLayout(layout7)

        self.setLayout(Mainlayout)
        
        self.disableButton()
        if load[0][4] == 1:
            self.scaleVisible(True)

    # 設定の読み込み
    def loadSettings(self):
        load = [[0,0,0,0,0,0,0,0],"",0,0,0.5]
        return load

    # 言語変更
    def langSwitch(self):
        if self.combobox1.currentIndex() == 0:
            qm_file = r"texCon_Jp.qm"
        else:
            qm_file = r"texCon_En.qm"
        self.translator.load(qm_file,directory=translation_dir)
        QtCore.QCoreApplication.installTranslator(self.translator)
        self.button1.setText(self.tr("reset"))
        self.button3.setText(self.tr("Connect"))
        self.button4.setText(self.tr("Close"))

    # リセット
    def reset(self):
        pass

    # ファイル選択
    def pushed_button2(self):
        chpath = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("Select Folder"))
        if not chpath:
            return()
        path2 = self.doRelativePath(chpath)
        self.textbox2.setText(path2)
    
    def doRelativePath(self,chpath):
        pass

    # 実行
    def pushed_button3(self):
        pass

    # 閉じる
    def pushed_button4(self):
        self.close()

    # ボックスからスライダーに
    def setSliderV(self):
        value = self.doubleSpinBox.value()*100
        self.slider.setValue(value)
    # スライダーからボックスに
    def setDSBV(self):
        value = self.slider.value()*0.01
        self.doubleSpinBox.setValue(value)

    # スケールの表示非表示
    def scaleVisible(self,bool):
        if bool:
            self.textbox.setVisible(True)
            self.doubleSpinBox.setVisible(True)
            self.slider.setVisible(True)
        else:
            self.textbox.setVisible(False)
            self.doubleSpinBox.setVisible(False)
            self.slider.setVisible(False)

    # 実行ボタンの表示変更
    def disableButton(self):
        if not self.checkbox1.isChecked() and not self.checkbox2.isChecked() and not self.checkbox3.isChecked() and not self.checkbox4.isChecked() and not self.checkbox5.isChecked() and not self.checkbox6.isChecked() and not self.checkbox7.isChecked():
            self.button3.setEnabled(False)
        else:
            self.button3.setEnabled(True)