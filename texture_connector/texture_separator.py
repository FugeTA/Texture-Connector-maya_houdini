import pathlib
import itertools
import re

def checkPath(fullPath,input):
    path = pathlib.Path(fullPath)  # ファイルパスを分解
    t = path.stem
    t = t.split('_')  # アンダーバーで分割
    for i in range(len(t)):
        l=itertools.combinations(t, i)  # 分解された文字列を接続
        for j in l:
            if input == str('_'.join(j)):  # マテリアル名のファイルがあるかチェック
                return(True)
    return(False)

# テクスチャフォルダパスの調整
def projpath(project,baseFolder,relative,nodeName,fileName,texPath,input,udim,ErrorWindow):
    if not project in texPath and relative:  # プロジェクトフォルダが含まれていなければ
        texPath = (project+texPath)  # プロジェクトフォルダ+テクスチャパス
    texPath = str(texPath.replace('/','\\'))

    p = pathlib.Path(texPath)
    rex = '*'+fileName+'*'
    fullPath = []
    for i in p.glob(rex):  # 目的のファイルネームがついたファイルを探す
        if i.suffix in '.tx':  # txファイル（キャッシュ）ならスルー
            continue
        else:
            fullPath.append(str(i))
    if fullPath == []:  # 設定されたパスに画像がなければ
        errorDialog = ErrorWindow(1,nodeName,texPath)  # エラー
        errorDialog.toClipBoard(texPath)
        errorDialog.openWindow()
        return (False)
    for i in fullPath:  # マテリアルの名前が入っているか
        ch = checkPath(i,str(input))
        if ch==True:
            fullPath=i
            break
    else:  # 無ければ
        errorDialog = ErrorWindow(2,str(input),'')  # エラー
        errorDialog.openWindow()
        return(False)
    if udim == '%(UDIM)d':  # houdiniのUDIM形式なら
        fullPath = re.sub(r'\.\d+\.',f'.{udim}.',fullPath)# Udim名
    project = project.replace('/', '\\')  # スラッシュに変換
    imgPath = str(re.sub(re.escape(project),baseFolder,fullPath))  # 相対パスに省略
    return(fullPath,imgPath)


def texplace(checkSelect,getmaterialname,ErrorWindow):
    shadingEngine = list(set(checkSelect()))
    if not shadingEngine:  # 選択されていなければ
        errorDialog = ErrorWindow(0,'','')  # エラー
        errorDialog.openWindow()
        return(False)
    returns = []
    for i in shadingEngine:
        inputSG = i
        input = getmaterialname(i) # マテリアルノード名
        returns.append([input,inputSG])
    return(returns)  # マテリアルノード名、シェーディングエンジン名のリストを返す

# ノード作成と接続
def connects(nodecreate,project,baseFolder,relative,nodeName,fileName,texPath,udim,input,ErrorWindow):
    returns = []
    for i,f in enumerate(fileName):
        path = projpath(project,baseFolder,relative,nodeName[i],fileName[i],texPath,input[0],udim,ErrorWindow)  # 画像ファイルの選択
        if path==False:  # 画像ファイルがなければ
            return(False)
        nodes = nodecreate(input[1])  # 接続用のノード作成
        returns.append([i,f,path,nodes])
    return(returns)  # ノード名、ファイル名、ノード、パス

#マテリアルごとのノード、ファイル名
def materialNodeNames(v):
    if v==0:
        #ss&aiss
        names1 = ['baseColor','metalness','specularRoughness','normalCamera','displacementShader','emission','opacity']
        names2 = ['Base','Metal','Roughness','Normal','Height','Emissive','Opacity']
    elif v==1:
        #rsm
        names1 = ['diffuse_color','metalness','refl_roughness','bump_input','displacementShader','emission_color','opacity_color']
        names2 = ['Color','Metal','Roughness','Normal','Displace','Emissive','Opacity']
    elif v==2:
        #rssm
        names1 = ['base_color','metalness','refl_roughness','bump_input','displacementShader','emission_color','opacity_color']
        names2 = ['Color','Metal','Roughness','Normal','Displace','Emissive','Opacity']
    return([names1,names2])

# ノード接続用の名前変更
def namereplace(self,udim,baseFolder,getWorkspace,nodecreate,checkSelect,getmaterialname,Sorttex,ErrorWindow):
    names = materialNodeNames(self.combobox2.currentIndex())
    nodeName=[]
    fileName=[]
    chlist=[]
    chlist.extend([int(checkbox.isChecked()) for checkbox in [
    self.checkbox1, self.checkbox2, self.checkbox3, self.checkbox4,
    self.checkbox5, self.checkbox6, self.checkbox7
    ]])
    for i, ch in enumerate(chlist):
        if ch == 1:
            nodeName.append(names[0][i])
            fileName.append(names[1][i])
    texPath = self.textbox2.text()
    rs = self.combobox2.currentIndex()
    hScale = self.doubleSpinBox.value()
    relative = self.relativePath
    project = getWorkspace()
    inputs = texplace(checkSelect,getmaterialname,ErrorWindow)  # マテリアルノード名、シェーディングエンジン名のリストを返す
    if not inputs:  # マテリアルがなければ
        return(False)
    for input,inputSG in inputs:
        con = connects(nodecreate,project,baseFolder,relative,nodeName,fileName,texPath,udim,input,ErrorWindow)
        if con == False:
            return(False)
        for i,f,path,nodes in con:
            Sorttex(f,nodes[0],input[1],nodeName[i],inputSG,path[1],rs,nodes[1],hScale,udim)
    return(True)