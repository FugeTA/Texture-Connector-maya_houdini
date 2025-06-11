import hou
from PySide2 import QtWidgets, QtCore
import re
import os
from .texture_separator import namereplace
from .window import ErrorWindow, MainWindow

# メインウィンドウィジェットの継承
class HoudiniWindow(MainWindow):
    def __init__(self, title, translator=None):
        super().__init__(title, translator)
        self.setWindowTitle(title)
        self.setObjectName(objName(title))
        self.textbox2.setText(getWorkspace())
        self.langSwitch()
        self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)

    # リセット
    def pushed_button1(self):
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
    
    def pushed_button2(self):
        topFolder = re.sub(r'[^/]+/$', '', self.textbox2.text())
        chpath = hou.ui.selectFile(
            title=self.tr("Select Texture Folder"),
            start_directory=hou.text.expandString(topFolder),
            file_type=hou.fileType.Directory,
            chooser_mode=hou.fileChooserMode.Read
        )
        if not chpath:
            return()
        path2 = self.doRelativePath(chpath)
        self.textbox2.setText(path2)

    def doRelativePath(self,chpath):
        work = hou.text.expandString("$HIP")
        if work+"/" == chpath:
            return(chpath)
        path2 = re.sub(work,'',chpath)
        if not chpath == path2:
            self.relativePath = True
        else:
            self.relativePath = False
        return(path2)

    def pushed_button3(self):
        with hou.undos.group("textureConnect"):
            udim = '%(UDIM)d' if self.checkbox8.isChecked() else '' #?
            baseFolder = '$HIP'
            work = namereplace(self,udim,baseFolder,getWorkspace,nodecreate,checkSelect,getmaterialname,Sorttex,ErrorWindow)
            if not work:
                return
            checkSelect()[0].layoutChildren()

# ワークスペースの取得
def getWorkspace():
    workspace = hou.text.expandString("$HIP")
    if not workspace:
        return('')
    return(workspace)

def nodecreate(input):
    image = input.createNode('mtlximage')
    return([image,""])

# 選択されたノードの取得
def checkSelect():
    selected = hou.selectedNodes()
    if not selected:
        return([])
    selected = selected[0]
    if not selected.type().name() == 'subnet':
        selected = selected.parent()
        if not selected.type().name() == 'subnet':
            return([])
    return([selected])

# マテリアルノードの取得
def getmaterialname(selected):
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
    files.parm('file').set(str(imgPath))
    if f == 'Base':
        input.setInput(1,files,0)
        files.setName('base_color')
    elif f == 'Opacity':
        input.setInput(38,files,0)
        files.setName('opacity')

def normal(files,input,imgPath):
    files.parm('file').set(str(imgPath))
    files.parm('signature').set('Vector3')
    files.parm('filecolorspace').set('Raw')
    nMap = input.parent().createNode('mtlxnormalmap')
    nMap.setInput(0,files,0)
    input.setInput(40,nMap,0)
    files.setName('normal')

def height(files,inputSG,imgPath,hScale):
    disp = inputSG.node('mtlxdisplacement')
    files.parm('file').set(str(imgPath))
    files.parm('signature').set('Float')
    files.parm('filecolorspace').set('Raw')
    disp.setInput(0,files,0)
    disp.parm('scale').set(hScale)
    files.setName('height')

def othertex(f,files,input,imgPath):
    files.parm('file').set(str(imgPath))
    files.parm('signature').set('Float')
    files.parm('filecolorspace').set('Raw')
    if f == 'Metal':
        input.setInput(3,files,0)
        files.setName('metalness')
    elif f == 'Roughness':
        input.setInput(6,files,0)
        files.setName('roughness')
    elif f == 'Emissive':
        input.setInput(36,files,0)
        files.setName('emissive')

def closeOldWindow(title):
    app = QtWidgets.QApplication.instance()
    for widget in app.topLevelWidgets():
        if widget.objectName() == objName(title):
            widget.close()

def objName(title):
    return(title + "_window")

def openWindow():
    title = "Texture_Connect"
    closeOldWindow(objName(title))
    translator = QtCore.QTranslator()
    window = HoudiniWindow(title,translator)
    window.show()