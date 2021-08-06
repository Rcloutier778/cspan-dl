@echo off
set mypath=%cd%
:checkForFFMPEG
echo "Checking for ffmpeg"
IF exist "%mypath%\ffmpeg.exe" (
    echo "Found ffmpeg.exe"
) ELSE (
    echo "ffmpeg.exe not detected!"
    echo "Please download ffmpeg, and place ffmpeg.exe in this directory."
    echo "It may be found at https://github.com/BtbN/FFmpeg-Builds/releases"
    set /p=Press any key to continue
    goto checkForFFMPEG
)

:checkForYoutubeDL
if exist "%mypath%\youtube-dl.exe" (
    echo "Found youtube-dl.exe"
) else (
    echo "Missing youtube-dl.exe!"
    echo "Please get it from http://ytdl-org.github.io/youtube-dl/download.html "
    set /p=Press any key to continue
    goto checkForYoutubeDL
)

:checkForPython
python --version 2>NUL
if %errorlevel% == 1 (
    echo "Please install python 3.* (3.7 preferred)"
    set /p=Please exit and restart the installer after python is installed
    goto EOF
)

python -m pip install -U pip setuptools
pip install -r requirements.txt


:EOF
echo "Done"