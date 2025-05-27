from setuptools import setup, find_packages

setup(
    name='texture_connector',  # パッケージ名（pip listで表示される）
    version="0.0.1",  # バージョン
    description="TextureConnector for Maya and Houdini",  # 説明
    author='Fujita Tatsuki',  # 作者名
    packages=find_packages(include=["texture_connector", "texture_connector.*"]),
    package_data={
        "texture_connector": ["language/*.qm"],  # langage フォルダ内の .qm ファイルを含める
    },
    license='MIT',  # ライセンス
    classifiers=[  # 追加のメタデータ
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)