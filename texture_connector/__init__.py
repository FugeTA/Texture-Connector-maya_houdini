from .config import translation_dir  # 修正: config からインポート

# Python のインストールディレクトリからフォルダ名を取得
dcc_tool = ""
try:
    import maya.cmds as cmds
    dcc_tool = "maya"
except ImportError:
    pass

try:
    import hou
    dcc_tool = "houdini"
except ImportError:
    pass

# DCC ツールに応じて適切なモジュールをインポート
if dcc_tool == "maya":
    from .maya_texture_Connecter import openWindow as openWindow
elif dcc_tool == "houdini":
    from .houdini_texture_connector import openWindow as openWindow
else:
    raise RuntimeError("Unsupported DCC tool detected. Please run this script in Maya or Houdini.")

# windowを起動
openWindow()