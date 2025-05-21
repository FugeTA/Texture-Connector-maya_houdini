import maya.cmds as cmds
try:
    from PySide2 import QtWidgets,QtCore,QtGui
except:
    from PySide6 import QtWidgets,QtCore,QtGui
from maya.app.general import mayaMixin
import re
import pathlib
import sys
import os
import importlib
script_path = os.path.join(cmds.workspace(q=True, rootDirectory=True), 'scripts')
if script_path not in sys.path:
    sys.path.append(script_path)  # スクリプトのパスを追加
import texture_separator
importlib.reload(texture_separator)  # スクリプトのリロード
from texture_separator import namereplace


#  エラー用ダイアログ
class ErrorWindow(mayaMixin.MayaQWidgetBaseMixin,QtWidgets.QWidget):
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

#  ウィンドウの見た目と各機能
class MainWindow(mayaMixin.MayaQWidgetBaseMixin,QtWidgets.QWidget):
    def __init__(self,title,translator):
        super().__init__()
        self.setWindowTitle(title)  # タイトル
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # deleteLater()の自動実行
        self.setObjectName(objName(title))  # ウィジェットとしての名前
        self.translator = translator  # 言語変更機能のため継承
        load = loadvar()  # 前回の変数呼び出し
        self.relativePath = load[5]
        if load[0]:  # チャンネルボックスの情報があれば
            ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8 = load[0]
        else:  # 無ければ
            ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8 = [0,0,0,0,0,0,0,0]
        texpath = load[1]  # テクスチャパス読み込み
        
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
        self.textbox2.setText(texpath)
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
    def langSwitch(self):
        if self.combobox1.currentIndex() == 0:
            qm_file = r"texCon_Jp.qm"
        else:
            qm_file = r"texCon_En.qm"
        self.translator.load(qm_file,directory=cmds.workspace(q=True,rootDirectory=True)+'\\scripts\\i18n')
        QtCore.QCoreApplication.installTranslator(self.translator)
        self.button1.setText(self.tr("reset"))
        self.button3.setText(self.tr("Connect"))
        self.button4.setText(self.tr("Close"))
    # リセット
    def pushed_button1(self):
        resetvariable(self)
    # ファイル選択
    def pushed_button2(self):
        self.relativePath = False
        basepath = pathlib.Path(cmds.workspace(q=True,rootDirectory=True)+'\\sourceimages\\texture')
        if basepath.exists()==False:
            basepath = pathlib.Path(cmds.workspace(q=True,rootDirectory=True)+'\\sourceimages')
        chpath = QtWidgets.QFileDialog.getExistingDirectory()
        if not chpath:
            return()
        path2 = self.doRelativePath(chpath)
        self.textbox2.setText(path2)
    
    def doRelativePath(self,chpath):
        work = cmds.workspace(q=True,rootDirectory=True)
        path2 = re.sub(work,'',chpath)
        if not chpath == path2:
            self.relativePath = True
        else:
            self.relativePath = False
        return(path2)

    # 実行
    def pushed_button3(self):
        cmds.undoInfo(openChunk=True)
        udim = '<UDIM>' if self.checkbox8.isChecked() else ''
        baseFolder = ''
        namereplace(self,udim,baseFolder,getWorkspace,nodecreate,checkSelect,getmaterialname,Sorttex,ErrorWindow)
        cmds.undoInfo(closeChunk=True)
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
    def closeEvent(self,_):
        savevar(self)

# 接続
def baseColor(files,input,imgPath,udim):  # ベースカラー
    if udim:  # UDIMならタイリング変更
        cmds.setAttr((files+'.uvTilingMode'),3)
    cmds.connectAttr((files+'.outColor'),input,f=True)
    cmds.setAttr((files+'.fileTextureName'),imgPath,type='string')  # Fileノードに画像を設定

def normal(files,input,imgPath,rs,p2t,udim):  # ノーマル
    if udim:  # UDIMならタイリング変更
        cmds.setAttr((files+'.uvTilingMode'),3)
    if rs==0:
        normal = cmds.shadingNode('aiNormalMap', asUtility=True)  # aiノーマルマップ作成
        cmds.connectAttr(normal+'.outValue',input,f=True)
    else:
        cmds.delete(files)
        cmds.delete(p2t)
        normal = cmds.shadingNode('RedshiftNormalMap', asUtility=True)  # rsノーマルマップ作成
        cmds.connectAttr(normal+'.outDisplacementVector',input,f=True)
        cmds.setAttr(normal+'.tex0.set',imgPath,type='string')
        return()
    cmds.setAttr(files+'.ignoreColorSpaceFileRules',1)  # カラースペース変更、変更を固定
    cmds.setAttr(files+'.cs',"Raw",type='string')
    cmds.setAttr(files+'.alphaIsLuminance',1)  # アルファ値に輝度を使用
    cmds.connectAttr(files+'.outColor',normal+'.input',f=True)
    cmds.setAttr(files+'.fileTextureName',imgPath,type='string')  # Fileノードに画像を設定

def height(files,input,inputSG,imgPath,rs,hScale,udim):  # ハイト
    if udim:  # UDIMならタイリング変更
        cmds.setAttr((files+'.uvTilingMode'),3)
    cmds.setAttr(files+'.ignoreColorSpaceFileRules',1)  # カラースペース変更、変更を固定
    cmds.setAttr(files+'.cs',"Raw",type='string')
    cmds.setAttr(files+'.alphaIsLuminance',1)  # アルファ値に輝度を使用
    if rs==0:
        disp = cmds.shadingNode('displacementShader', asUtility=True)  # Heightマップ用のディスプレイスメントを作成
        cmds.connectAttr(files+'.outAlpha',disp+'.displacement',f=True)
        cmds.connectAttr(disp+'.displacement',inputSG+'.displacementShader',f=True)
    else:
        disp = cmds.shadingNode('RedshiftDisplacement', asUtility=True)
        cmds.connectAttr(files+'.outColor',disp+'.texMap',f=True)
        cmds.connectAttr(disp+'.out',inputSG+'.displacementShader',f=True)
    cmds.setAttr(disp+'.scale',hScale)
    cmds.setAttr(files+'.fileTextureName',imgPath,type='string')  # Fileノードに画像を設定

def othertex(files,input,imgPath,udim):  # その他
    if udim:  # UDIMならタイリング変更
        cmds.setAttr((files+'.uvTilingMode'),3)
    cmds.setAttr(files+'.ignoreColorSpaceFileRules',1)  # カラースペース変更、変更を固定
    cmds.setAttr(files+'.cs',"Raw",type='string')
    cmds.setAttr(files+'.alphaIsLuminance',1)  # アルファ値に輝度を使用
    cmds.connectAttr(files+'.outAlpha',input,f=True)
    cmds.setAttr(files+'.fileTextureName',imgPath,type='string')  # Fileノードに画像を設定

# 画像の分類
def Sorttex(f,files,input,nodeName,inputSG,imgPath,rs,p2t,hScale,udim):
    input = input+'.'+nodeName
    if(f in ['Base','Color','Opacity']):  # colorで接続
        baseColor(files,input,imgPath,udim)
        return
    if(f == 'Normal'):  #vector3で接続
        normal(files,input,imgPath,rs,p2t,udim)
        return
    if(f in ['Height','Displace']):  # floatでdisplacementに接続
        height(files,input,inputSG,imgPath,rs,hScale,udim)
        return
    if(f in ['Emissive','Metal','Roughness']):  # floatで接続
        othertex(files,input,imgPath,udim)

# ノード作成
def nodecreate(input):
    files = cmds.shadingNode('file', asTexture=True,isColorManaged=True)  # Fileノード作成
    p2t = cmds.shadingNode('place2dTexture', asUtility=True)  # P2Tノード作成
    cmds.defaultNavigation(connectToExisting=True, source=p2t, destination=files, f=True)  # 上記のノード接続
    return(files,p2t)

# -------------------------------pythonの機能なので、流用可能-------------------------------


# -------------------------------mayaの機能なので、流用不可能-------------------------------

# shapeノードからSGノードを取得
def parent(sel,names):
    chl = cmds.listRelatives(sel, c=True)
    if not chl:
        return()
    for i in chl:
        if not cmds.objectType(i,isType='mesh'):  # シェイプノードでなければ
            parent(chl,names)
        else:
            if not (name := cmds.listConnections(i+'.instObjGroups',s=False)):
                name = cmds.listConnections(i+'.instObjGroups[0].objectGroups',s=False)  # SGを取得
            if not name:
                continue
            names += name
    return(names)

# 選択の確認
def checkSelect():
    s = cmds.ls(sl=True)
    sg = []
    if not s:
        return()
    for sel in s:
        if cmds.objectType(sel,isType='transform'):
            names = []
            sg += parent(sel,names)
        elif cmds.objectType(sel,isType='mesh'):
            if not (name := cmds.listConnections(sel+'.instObjGroups',s=False)):
                name = cmds.listConnections(sel+'.instObjGroups[0].objectGroups',s=False)  # SGを取得
            sg += name
        elif cmds.objectType(sel,isType='standardSurface') or cmds.objectType(sel,isType='aiStandardSurface') :
            sg += cmds.listConnections(sel+'.outColor',s=False)
    return(sg)

def getmaterialname(i):
    name = cmds.listConnections(i+'.surfaceShader',d=False)[0]
    return(name,name)

def getWorkspace():
    workspace = cmds.workspace(q=True,fn=True)  # プロジェクトフォルダの取得
    workspace = str(workspace.replace('/','\\')+'\\')
    return(workspace)

# -------------------------------mayaの機能なので、流用不可能-------------------------------


# 変数の記憶
def savevar(self):
    chlist = []
    cmds.optionVar(ia='checklist')
    chlist.extend([int(checkbox.isChecked()) for checkbox in [
    self.checkbox1, self.checkbox2, self.checkbox3, self.checkbox4,
    self.checkbox5, self.checkbox6, self.checkbox7, self.checkbox8
    ]])
    for i in range(len(chlist)):
        cmds.optionVar(iva=['checklist',chlist[i]])  # データをuserPrefs.melに保存
    if self.textbox2.text() != 'sourceimages/texture/':  # テクスチャフォルダパスの保存
        cmds.optionVar(sv=['texPath',self.textbox2.text()])  # データをuserPrefs.melに保存
    lan = int(self.combobox1.currentIndex())  # 言語設定
    cmds.optionVar(iv=['texlanguage',lan])  # データをuserPrefs.melに保存
    mat = int(self.combobox2.currentIndex())  # マテリアル設定
    cmds.optionVar(iv=['texmaterials',mat])  # データをuserPrefs.melに保存
    scl = self.doubleSpinBox.value()  # ハイトのスケール
    cmds.optionVar(fv=['texhScale',scl])  # データをuserPrefs.melに保存
    relative = self.relativePath
    cmds.optionVar(iv=['texRelative',relative])  # データをuserPrefs.melに保存

# 変数の呼び出し
def loadvar():
    if cmds.optionVar(ex='checklist'):  # 前回の設定読み込みまたは新規で作成
        chlist = cmds.optionVar(q='checklist')
    else:
        chlist = [0,0,0,0,0,0,0,0]
    if cmds.optionVar(ex='texPath'):
        texpath = cmds.optionVar(q='texPath')
    else:
        texpath = 'sourceimages\\texture\\'
    if cmds.optionVar(ex='texlanguage'):
        lan = cmds.optionVar(q='texlanguage')
    else:
        lan = 1
    if cmds.optionVar(ex='texmaterials'):
        mat = cmds.optionVar(q='texmaterials')
    else:
        mat = 1
    if cmds.optionVar(ex='texhScale'):
        hScale = cmds.optionVar(q='texhScale')
    else:
        hScale = 0.5
    if cmds.optionVar(ex='texRelative'):
        relative = cmds.optionVar(q='texRelative')
    else:
        relative = False
    return [chlist,texpath,lan,mat,hScale,relative]

# 入力リセット
def resetvariable(self):
    cmds.optionVar(ia=['checklist'])
    cmds.optionVar(sv=['texPath','sourceimages\\texture\\'])
    cmds.optionVar(iv=['texlanguage',1])
    cmds.optionVar(iv=['texmaterials',1])
    cmds.optionVar(fv=['texhScale',0.5])
    self.checkbox1.setChecked(False)
    self.checkbox2.setChecked(False)
    self.checkbox3.setChecked(False)
    self.checkbox4.setChecked(False)
    self.checkbox5.setChecked(False)
    self.checkbox6.setChecked(False)
    self.checkbox7.setChecked(False)
    self.checkbox8.setChecked(False)
    self.textbox2.setText('sourceimages\\texture\\')
    self.combobox2.setCurrentIndex(0)
    self.doubleSpinBox.setValue(0.5)

#  ウィンドウがすでに起動していれば閉じる
def closeOldWindow(title):
    if cmds.window(title, q=True, ex=True):  # ウィジェットの名前で削除
        cmds.deleteUI(title)

def objName(title):
    return(title + "_window")

#  アプリの実行と終了
def openWindow():
    title = "Texture_Connect"
    closeOldWindow(objName(title))
    app = QtWidgets.QApplication.instance()
    if cmds.optionVar(q='texlanguage') == 0:
        qm_file = r"texCon_Jp.qm"
    else:
        qm_file = r"texCon_En.qm"
    translator = QtCore.QTranslator(app)
    translator.load(qm_file,directory = cmds.workspace(q=True,rootDirectory=True)+'\\scripts\\i18n')
    QtCore.QCoreApplication.installTranslator(translator)
    window = MainWindow(title,translator)
    window.show()
    try:
        app.exec()  #Pyside6
    except:
        app.exec_()  #Pyside2

if __name__ == "__main__":
    openWindow()