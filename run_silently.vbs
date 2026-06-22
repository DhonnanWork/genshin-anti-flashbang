Set ObjShell = CreateObject("Wscript.Shell")
StrPath = createobject("Scripting.FileSystemObject").GetParentFolderName(Wscript.ScriptFullName)
ObjShell.CurrentDirectory = StrPath
ObjShell.Run "python genshin_window_checker.py", 0, False