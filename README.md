pyinstaller --noconfirm --onefile --name "VideoToCleanAudioTool" --add-binary "tools\ffmpeg.exe;bin" --add-data  "c:\users\spadicharayil\appdata\local\programs\python\python310\lib\site-packages\demucs;demucs" --add-binary "tools\yt-dlp.exe;bin" --hidden-import=torch --hidden-import=pysoundfile --hidden-import=diffq --hidden-import="yt_dlp" app.py
 
Copy ffmpeg.exe
     yt-dlp.exe in tools folder 

"https://qhowe1w8xd.execute-api.us-east-2.amazonaws.com/Prod/log"