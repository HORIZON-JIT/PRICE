Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' スクリプトのあるフォルダをカレントに
appDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = appDir

' venvが無ければinstall.batを先に実行
If Not fso.FolderExists(appDir & "\.venv") Then
    MsgBox "初回セットアップを実行します。" & vbCrLf & _
           "完了まで数分かかる場合があります。", vbInformation, "価格演算システム"
    WshShell.Run "cmd /c """ & appDir & "\install.bat""", 1, True
End If

' Streamlit起動 (コンソール非表示)
WshShell.Run "cmd /c """ & appDir & "\.venv\Scripts\activate.bat"" && streamlit run """ & appDir & "\src\price\app.py"" --server.headless true", 0, False

' 少し待ってからブラウザを開く
WScript.Sleep 3000
WshShell.Run "http://localhost:8501"
