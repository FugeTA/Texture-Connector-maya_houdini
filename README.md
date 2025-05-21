# texture-Connector-maya_houdini

![screenshot]()
## 概要
AdobeSubstancePainterで出力したテクスチャをMaya/Houdiniに簡単にアサインするツールです。  
モジュール共有バージョン  
## 要件
なし
## 使い方
1.Mayaのドキュメントの/scripts内か、プロジェクトフォルダの/scriptsにtexture_Connecterファイルとtexture_separatorファイルを移動する。  
2.以下のコマンドを実行する。
```
import (python/maya)_texture_Connecter
textureConnecter.openWindow()
```  
またはscriptEditor/PythonCommandEditor上で実行する。
## 説明
1.Substance PainterでArnoldテンプレートを使用し、テクスチャを出力する。  
2.ツール内でマテリアルを選択する。（作成時とマテリアル名をそろえること）  
3.画像ファイルの入っているフォルダを選択する。    
4."Connect" ボタンで実行できる。  
  
特にHoudiniでモジュールのインストールは難しいので、＄HIPのScriptsフォルダーを参照するようにしてあります。  
可能ならenv等を記入し、自由に場所を変更してください。その場合、7~13行目は不要です。  
## 作者
[Twitter](https://x.com/cotte_921)

## ライセンス
[MIT](LICENSE)
