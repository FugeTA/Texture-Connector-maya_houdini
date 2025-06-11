import maya.cmds as cmds
try:
    from PySide2 import QtWidgets,QtCore
except:
    from PySide6 import QtWidgets,QtCore
from maya.app.general import mayaMixin
import os
import re
from .texture_separator import namereplace
from .window import ErrorWindow, MainWindow

#  エラー用ダイアログ
class MayaErrorWindow(mayaMixin.MayaQWidgetBaseMixin, ErrorWindow):
    def __init__(self, eText, strings1, strings2, parent=None):
        super().__init__(parent=parent, eText=eText, strings1=strings1, strings2=strings2)

#  ウィンドウの見た目と各機能
class MayaMainWindow(mayaMixin.MayaQWidgetBaseMixin, MainWindow):
    def __init__(self, title, translator, parent=None):
        super().__init__(title=title, translator=translator, parent=parent)
        self.setWindowTitle(title)
        self.setObjectName(title + "_window")  # ウィジェットの名前
        self.textbox2.setText(self.doRelativePath(self.textbox2.text()))
        self.langSwitch()
        self.setWindowTitle(title)

    def loadSettings(self):
        load = loadvar()
        return load
    
    # リセット
    def pushed_button1(self):
        self.resetOption()
        self.checkbox1.setChecked(False)
        self.checkbox2.setChecked(False)
        self.checkbox3.setChecked(False)
        self.checkbox4.setChecked(False)
        self.checkbox5.setChecked(False)
        self.checkbox6.setChecked(False)
        self.checkbox7.setChecked(False)
        self.checkbox8.setChecked(False)
        self.textbox2.setText('sourceimages\\')
        self.combobox2.setCurrentIndex(0)
        self.doubleSpinBox.setValue(0.5)
    
    def resetOption(self):
        cmds.optionVar(ia=['checklist'])
        for i in range(8):
            cmds.optionVar(iva=['checklist',0])
        cmds.optionVar(sv=['texRelative',False])
        cmds.optionVar(sv=['texPath','sourceimages\\'])
        cmds.optionVar(iv=['texlanguage',1])
        cmds.optionVar(iv=['texmaterials',1])
        cmds.optionVar(fv=['texhScale',0.5])

    def pushed_button2(self):
        if (topFolder := self.textbox2.text()) != "sourceimages\\":
            topFolder = re.sub(r'[^/]+$', '', topFolder)
        currentPath = cmds.workspace(q=True, rootDirectory=True) + topFolder
        chpath = cmds.fileDialog2(
            dialogStyle = 2,  # Mayaのファイルダイアログスタイル
            fileMode = 3,  # ディレクトリ選択モード
            caption = self.tr("Select Texture Folder"),
            okCaption = self.tr("Select"),
            startingDirectory = currentPath,
        )
        if not chpath:
            return()
        path2 = self.doRelativePath(chpath[0])
        self.textbox2.setText(path2)

    def doRelativePath(self,chpath):
        work = cmds.workspace(q=True,rootDirectory=True)
        if work == chpath:
            return(chpath)
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
        namereplace(self,udim,baseFolder,getWorkspace,nodecreate,checkSelect,getmaterialname,Sorttex,MayaErrorWindow)
        cmds.undoInfo(closeChunk=True)

    # 終了時の処理
    def closeEvent(self,_):
        savevar(self)

# 接続
def baseColor(files,input,imgPath,udim):  # ベースカラー
    cmds.connectAttr((files+'.outColor'),input,f=True)
    cmds.setAttr((files+'.fileTextureName'),imgPath,type='string')  # Fileノードに画像を設定
    if udim:  # UDIMならタイリング変更
        cmds.setAttr((files+'.uvTilingMode'),3)

def normal(files,input,imgPath,rs,p2t,udim):  # ノーマル
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
    if udim:  # UDIMならタイリング変更
        cmds.setAttr((files+'.uvTilingMode'),3)

def height(files,input,inputSG,imgPath,rs,hScale,udim):  # ハイト
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
    if udim:  # UDIMならタイリング変更
        cmds.setAttr((files+'.uvTilingMode'),3)

def othertex(files,input,imgPath,udim):  # その他
    cmds.setAttr(files+'.ignoreColorSpaceFileRules',1)  # カラースペース変更、変更を固定
    cmds.setAttr(files+'.cs',"Raw",type='string')
    cmds.setAttr(files+'.alphaIsLuminance',1)  # アルファ値に輝度を使用
    cmds.connectAttr(files+'.outAlpha',input,f=True)
    cmds.setAttr(files+'.fileTextureName',imgPath,type='string')  # Fileノードに画像を設定
    if udim:  # UDIMならタイリング変更
        cmds.setAttr((files+'.uvTilingMode'),3)

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
    if self.textbox2.text() != 'sourceimages\\':  # テクスチャフォルダパスの保存
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
        texpath = 'sourceimages\\'
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



#  ウィンドウがすでに起動していれば閉じる
def closeOldWindow(title):
    title = title + "_window"
    if cmds.window(title, q=True, ex=True):  # ウィジェットの名前で削除
        cmds.deleteUI(title)
        
#  アプリの実行と終了
def openWindow():
    title = "Texture_Connect"
    closeOldWindow(title)
    app = QtWidgets.QApplication.instance()
    translator = QtCore.QTranslator(app)
    QtCore.QCoreApplication.installTranslator(translator)
    window = MayaMainWindow(title,translator)
    window.show()
    try:
        app.exec()  #Pyside6
    except:
        app.exec_()  #Pyside2