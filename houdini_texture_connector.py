import hou
import pathlib
from PySide2 import QtWidgets, QtCore
import re
import sys
import os
import importlib
script_path = os.path.join(hou.text.expandString("$HIP")+'/scripts')
if script_path not in sys.path:
    sys.path.append(script_path)  # スクリプトのパスを追加
import texture_separator
importlib.reload(texture_separator)  # スクリプトのリロード
from texture_separator import namereplace

class ErrorWindow(QtWidgets.QWidget):
    def __init__(self,eText,strings1,strings2):
        super().__init__()
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
    def __init__(self,title):
        super().__init__()
        self.setWindowTitle(title)  # タイトル
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # deleteLater()の自動実行
        self.setObjectName(objName(title))  # ウィジェットとしての名前
        self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
        self.relativePath = False
        ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8 = [0,0,0,0,0,0,0,0]
        
        Mainlayout = QtWidgets.QVBoxLayout()  # メインのレイアウト
        # 言語選択
        layout2 = QtWidgets.QHBoxLayout()
        self.combobox1 = QtWidgets.QComboBox(self)
        self.combobox1.addItems(["English"])
        self.combobox1.setCurrentIndex(0)
        layout2.addWidget(self.combobox1)
        # リセットボタン
        self.button1 = QtWidgets.QPushButton(self.tr("reset"))
        self.button1.clicked.connect(self.reset)
        layout2.addWidget(self.button1)
        Mainlayout.addLayout(layout2)
        # マテリアル選択
        layout8 = QtWidgets.QHBoxLayout()
        self.combobox2 = QtWidgets.QComboBox(self)
        self.combobox2.addItems(["StandardSurface & aiStandardSurface", "RedShiftMaterial", "RedShiftStandardMaterial"])
        self.combobox2.setCurrentIndex(0)
        layout8.addWidget(self.combobox2)
        self.checkbox8 = QtWidgets.QCheckBox("UDIM")
        self.checkbox8.setChecked(ch8)
        layout8.addWidget(self.checkbox8)
        Mainlayout.addLayout(layout8)
        # テクスチャ選択
        layout3 = QtWidgets.QHBoxLayout()
        self.checkbox1 = QtWidgets.QCheckBox("BaseColor")
        self.checkbox1.setChecked(ch1)
        self.checkbox1.stateChanged.connect(self.disableButton)
        layout3.addWidget(self.checkbox1)
        self.checkbox2 = QtWidgets.QCheckBox("Metalness")
        self.checkbox2.setChecked(ch2)
        self.checkbox2.stateChanged.connect(self.disableButton)
        layout3.addWidget(self.checkbox2)
        self.checkbox3 = QtWidgets.QCheckBox("Roughness")
        self.checkbox3.setChecked(ch3)
        self.checkbox3.stateChanged.connect(self.disableButton)
        layout3.addWidget(self.checkbox3)
        Mainlayout.addLayout(layout3)
        # 改行
        layout4 = QtWidgets.QHBoxLayout()
        self.checkbox4 = QtWidgets.QCheckBox("Normal")
        self.checkbox4.setChecked(ch4)
        self.checkbox4.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox4)
        self.checkbox5 = QtWidgets.QCheckBox("Height")
        self.checkbox5.setChecked(ch5)
        self.checkbox5.stateChanged.connect(self.scaleVisible)
        self.checkbox5.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox5)
        self.checkbox6 = QtWidgets.QCheckBox("Emissive")
        self.checkbox6.setChecked(ch6)
        self.checkbox6.stateChanged.connect(self.disableButton)
        layout4.addWidget(self.checkbox6)
        self.checkbox7 = QtWidgets.QCheckBox("Opacity")
        self.checkbox7.setChecked(ch7)
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
        self.doubleSpinBox.setValue(0.5)
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
        self.textbox2.setText(getWorkspace())
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
        if ch5 == 1:
            self.scaleVisible(True)

    # 言語変更

    # リセット
    def reset(self):
        self.combobox1.setCurrentIndex(0)
        self.combobox2.setCurrentIndex(0)
        self.checkbox1.setChecked(0)
        self.checkbox2.setChecked(0)
        self.checkbox3.setChecked(0)
        self.checkbox4.setChecked(0)
        self.checkbox5.setChecked(0)
        self.checkbox6.setChecked(0)
        self.checkbox7.setChecked(0)
        self.checkbox8.setChecked(0)
        self.textbox2.setText(getWorkspace())
        self.doubleSpinBox.setValue(0.5)
        self.slider.setValue(50)

    # ファイル選択
    def pushed_button2(self):
        chpath = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("Select Folder"))
        if not chpath:
            return()
        path2 = self.doRelativePath(chpath)
        self.textbox2.setText(path2)
    
    def doRelativePath(self,chpath):
        work = hou.text.expandString("$HIP")
        path2 = re.sub(work,'',chpath)
        if not chpath == path2:
            self.relativePath = True
        else:
            self.relativePath = False
        return(path2)
    # 実行
    def pushed_button3(self):
        with hou.undos.group("textureConnect"):
            udim = '%(UDIM)d' if self.checkbox8.isChecked() else '' #?
            baseFolder = '$HIP'
            namereplace(self,udim,baseFolder,getWorkspace,nodecreate,checkSelect,getmaterialname,Sorttex,ErrorWindow)
            checkSelect()[0].layoutChildren()
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
    # 終了時の処理

def getWorkspace():
    # ワークスペースの取得
    workspace = hou.text.expandString("$HIP")
    if not workspace:
        return('')
    return(workspace)

def nodecreate(input):
    image = input.createNode('mtlximage')
    return([image,""])

def checkSelect():
    # 選択されたノードの取得
    selected = hou.selectedNodes()
    if not selected:
        return([])
    selected = selected[0]
    if not selected.type().name() == 'subnet':
        selected = selected.parent()
        if not selected.type().name() == 'subnet':
            return([])
    return([selected])

def getmaterialname(selected):
    # マテリアルノードの取得
    mat = selected.name()
    return([mat,selected])

def Sorttex(f,files,input,nodeName,inputSG,imgPath,rs,p2t,hScale,udim):
    input = input.node('mtlxstandard_surface')
    if(f in ['Base','Color','Opacity']):  # colorで接続
        baseColor(f,files,input,imgPath)
        return
    if(f == 'Normal'):  #vector3で接続
        normal(files,input,imgPath)
        return
    if(f in ['Height','Displace']):  # floatでdisplacementに接続
        height(files,inputSG,imgPath,hScale)
        return
    if(f in ['Emissive','Metal','Roughness']):  # floatで接続
        othertex(f,files,input,imgPath)

def baseColor(f,files,input,imgPath):
    files.parm('file').set(str(imgPath))  # baseColorfile
    if f == 'Base':
        input.setInput(1,files,0)  # baseColor
        files.setName('base_color')
    elif f == 'Opacity':
        input.setInput(38,files,0)  # opacity
        files.setName('opacity')

def normal(files,input,imgPath):
    files.parm('file').set(str(imgPath))  # normalfile
    files.parm('signature').set('Vector3')  # vector3Type
    files.parm('filecolorspace').set('Raw')  # colorSpace
    input.setInput(40,files,0)  # normal
    files.setName('normal')

def height(files,inputSG,imgPath,hScale):
    disp = inputSG.node('mtlxdisplacement')
    files.parm('file').set(str(imgPath))  # heightfile
    files.parm('signature').set('Float')  # flortType
    files.parm('filecolorspace').set('Raw')  # colorSpace
    disp.setInput(0,files,0)  # height
    disp.parm('scale').set(hScale)  # heightScale
    files.setName('height')

def othertex(f,files,input,imgPath):
    files.parm('file').set(str(imgPath))  # otherfile
    files.parm('signature').set('Float')  # floatType
    files.parm('filecolorspace').set('Raw')  # colorSpace
    if f == 'Metal':
        input.setInput(3,files,0)  # othertex
        files.setName('metalness')
    elif f == 'Roughness':
        input.setInput(6,files,0)
        files.setName('roughness')
    elif f == 'Emissive':
        input.setInput(36,files,0)
        files.setName('emissive')

# main
def texCon(folder):
    fileType = ['BaseColor','Metalness','Roughness','Opacity','Emission','Normal','Height']
    filename = [getFiles(folder,t) for t in fileType]
    if not any(filename):
        ErrorWindow("Texture file not found")
        return()
    mat,disp,height,image = makeNodes(filename)
    fileSetting(filename,image,height,disp)
    connectNode(filename,mat,image,disp,height)

# getFiles
def getFiles(folder,texType):
    #フォルダからファイルを取り出す
    #選択されたフォルダがあるかどうか
    path = pathlib.Path(folder)
    if not path.exists():
        return(False)
    # フォルダ内に特定のファイルがあるか
    for i in path.iterdir():
        if i.suffix in ["tx","rat"]:
            continue
        if texType in str(i) :
            if re.search(r'_\d+\.',str(i)):
                i = re.sub(r'_\d+\.',r'_%(UDIM)d.',str(i))
                return(i)
            return(i)
    else:
        return(False)   

# getNode
def makeNodes(filename):
    h = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    mat = hou.selectedItems()[0]
    disp = hou.selectedItems()[0].outputs()[0].input(1)
    image = hou.node((h.pwd().path())).createNode('hmtlxpbrtextureset','hmtlxpbrtextureset1')
    height = False
    if filename[6]:
        height =  hou.node((h.pwd().path())).createNode('mtlximage','mtlximage1')
    return(mat,disp,height,image)

# setFilesParm
def fileSetting(filename,image,height,disp):
    hParm = ['base_color_file','metalness_file','specular_roughness_file','opacity_file','emission_color_file','bump_normal_file','Height_file']
    for i,f in enumerate(filename):
        # heightがあれば
        if i == 6 and f:
            height.parm('file').set(str(f))  # heightfile
            height.parm('signature').set('Float')  # flortType
            height.parm('filecolorspace').set('Raw')  # colorSpace
            disp.parm('scale').set(0.5)  # heightScale
            continue
        # 基本
        if f:
            image.parm(hParm[i]).set(str(f))
        # normalがあれば
        if i == 5 and f:
            image.parm('bump_style').set(1)  # RawSpace
            image.parm('bump_scale').set(1)  # normalScale
    
# connect
def connectNode(filename,mat,image,disp,height):
    if filename[0]:
        mat.setInput(1,image,0)  # baseColor
    if filename[1]:
        mat.setInput(3,image,1)  # metalness
    if filename[2]:
        mat.setInput(6,image,3)  # roughness
    if filename[3]:
        mat.setInput(38,image,10)  # opacity
    if filename[4]:
        mat.setInput(36,image,8)  # emission
    if filename[5]:
        mat.setInput(40,image,11)  # normal
    if filename[6]:
        disp.setInput(0,height,0)  # height
# outputNode:inputParmNum,inputNode,outputParmNum


def closeOldWindow(title):
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if title == widget.windowTitle():
            widget.deleteLater()
            widget.close()

def objName(title):
    return(title + "_window")

def main():
    title = "Texture_Connect"
    closeOldWindow(objName(title))
    window = MainWindow(title)
    window.show()

main()