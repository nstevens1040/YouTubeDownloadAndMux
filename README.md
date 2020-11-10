# YouTubeDownloadAndMux
Selects highest quality YouTube download formats for audio and video separately and then it will mux the audio and video together.  

This python script leverages **Youtube-DL** and **FFmpeg**.  
# Installation  
Simply use the requirements.txt file to install all needed dependencies.  
```
python -m pip install --upgrade pip
git clone "https://github.com/nstevens1040/YouTubeDownloadAndMux.git"
cd YouTubeDownloadAndMux
pip install -r requirements.txt
```  
# Usage  
```
python YouTubeDownloadAndMux.py "<string youtube link>"
```
Once you strike enter, the script will download both the highest quality audio and the highest quality video separately and then it will mux them together. Useful information (where the output file is being saved, etc.) is printed to the console window.  
