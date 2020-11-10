import youtube_dl
import re
import requests
import ctypes, sys
import os
import colorama
from colorama import Fore,Back,Style,init
from tqdm import tqdm
import asyncio
import concurrent.futures
import ffmpeg
from sanitize_filename import sanitize
import shutil
import os.path
from os import path
import tempfile
from ffprobe import FFProbe

init()
print(Style.BRIGHT)

def get_size(url):
    response = requests.head(url)
    size = int(response.headers['Content-Length'])
    return size

def check_update():
    current=youtube_dl.version.__version__
    latest=re.compile("\((.+)\)").search(requests.get("https://youtube-dl.org/").text).group(1).replace('v','')
    print(Fore.YELLOW + "Current youtube-dl version:", end='')
    for i in list(range(0,(32 - len("Current youtube-dl version: ")))):
        print(" ",end='')
    print(Fore.GREEN + current)
    print(Fore.YELLOW + "Latest youtube-dl version:", end='')
    for i in list(range(0,(32 - len("Latest youtube-dl version: ")))):
        print(" ",end='')
    print(Fore.GREEN + latest)
    if not current == latest:
        print(Fore.WHITE + "    Update needed!")
        if sys.platform == 'win32':
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "C:\Program Files (x86)\Python38-32\Scripts\pip.exe", " install --upgrade youtube-dl", None, 1)
        else:
            os.system("sudo pip install --upgrade youtube-dl")

def select_bestaudio(formats):
    aformats = []
    def sort_abr(val):
        return val['abr']
    for i in list(range(0,len(formats['formats']))):
        if re.search("audio only",str(formats['formats'][i]['format'])):
            aformats.append({'format_id': str(formats['formats'][i]['format_id']), 'abr': int(formats['formats'][i]['abr'])})
    aformats.sort(key=sort_abr, reverse=True)
    a_selection = aformats[0]['format_id']
    for i in list(range(0,len(formats['formats']))):
        if formats['formats'][i]['format_id'] == a_selection:
            aformat = formats['formats'][i]
    print(Fore.YELLOW + "Best audio format id: ", end='')
    for i in list(range(0,(32 - len("Best audio download id:")))):
        print(" ",end='')
    print(Fore.GREEN + a_selection)
    return aformat

def select_bestvideo(formats):
    vformats = []
    def sort_tbr(val):
        return val['tbr']
    for i in list(range(0,len(formats['formats']))):
        if not re.search("audio only",str(formats['formats'][i]['format'])):
            vformats.append({'format_id': str(formats['formats'][i]['format_id']), 'tbr': int(formats['formats'][i]['tbr'])})
    vformats.sort(key=sort_tbr, reverse=True)
    v_selection = vformats[0]['format_id']
    for i in list(range(0,len(formats['formats']))):
        if formats['formats'][i]['format_id'] == v_selection:
            vformat = formats['formats'][i]
    print(Fore.YELLOW + "Best video format id: ", end='')
    for i in list(range(0,(32 - len("Best video download id:")))):
        print(" ",end='')
    print(Fore.GREEN + v_selection)
    return vformat


def download_range(url, start, end, filename,file_size):
    headers = {'Range': f'bytes={start}-{end}'}
    response = requests.get(url, headers=headers)
    with open(filename, 'wb') as f:
        for part in response.iter_content(1024):
            f.write(part)


async def download_file(executor, url, filename, file_size, chunk_size=262144):
    name = filename.split('/')[(len(audio_filename.split('/')) - 1)]
    chunks = range(0, file_size, chunk_size)
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(
            executor,
            download_range,
            url,
            start,
            start + chunk_size - 1,
            f'{tempfolder}/{name}.part{i}',
            file_size
        )
        for i, start in enumerate(chunks)
    ]
    try:
        await asyncio.wait(tasks)
    except:
        ERRCATCH = 1
    else:
        ERRCATCH = 0
    while not ERRCATCH == 0:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    executor,
                    download_range,
                    url,
                    start,
                    start + chunk_size - 1,
                    f'{filename}.part{i}',
                    file_size
                )
                for i, start in enumerate(chunks)
            ]
            try:
                await asyncio.wait(tasks)
            except:
                ERRCATCH = 1
            else:
                ERRCATCH = 0
    with tqdm(total=file_size, unit='B',unit_scale=True,unit_divisor=1024,desc=name,initial=0,ascii=True,miniters=1,leave=False,file=sys.stdout) as pbar:
        with open(filename, 'wb') as o:
            for i in range(len(chunks)):
                chname = filename.split('/')[(len(filename.split('/')) - 1)]
                chunk_path = f'{tempfolder}/{chname}.part{i}'
                with open(chunk_path, 'rb') as s:
                    current = s.read()
                    o.write(current)
                    pbar.update(len(current))
                os.remove(chunk_path)


def execute_download(uri,filename, file_size):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=16)
    if asyncio.get_event_loop().is_closed():
        loop = asyncio.new_event_loop()
    else:
        loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            download_file(executor, uri, filename, file_size)
        )
    finally:
        loop.close()

def info_extract(uri):
    try:
        info=ytdl.extract_info(uri,False)
    except:
        count = 0
        retcode = 1
        while not retcode == 0 | count < 10:
            count = count + 1
            try:
                info=ytdl.extract_info(uri,False)
            except:
                retcode = 1
            try:
                info
            except:
                retcode = 1
            else:
                retcode = 0
        if count > 10:
            print(Fore.RED + "Trying running the script again.")
    return info


check_update()
ytdl = youtube_dl.YoutubeDL()
print(Fore.WHITE)
info = info_extract(sys.argv[1])

a_selection = select_bestaudio(info)
v_selection = select_bestvideo(info)

if sys.platform == 'win32':
    homefolder = os.environ['userprofile'].replace("\\","/")
else:
    homefolder = os.environ.get("HOME")

audio_filename = homefolder + "/Desktop/temp_audio." + a_selection['ext']
video_filename = homefolder + "/Desktop/temp_video." + v_selection['ext']
tempfolder = tempfile.NamedTemporaryFile().name
if not os.path.isdir(tempfolder):
    os.mkdir(tempfolder)
print(Fore.YELLOW + "Audio filename:", end='')
for i in list(range(0,(32 - len("Audio filename: ")))):
    print(" ",end='')
print(Fore.GREEN + audio_filename)

print(Fore.YELLOW + "video filename:", end='')
for i in list(range(0,(32 - len("video filename: ")))):
    print(" ",end='')
print(Fore.GREEN + video_filename)

asize = get_size(a_selection['url'])
aname = audio_filename.split('/')[(len(audio_filename.split('/')) - 1)]

vsize = get_size(v_selection['url'])
vname = video_filename.split('/')[(len(audio_filename.split('/')) - 1)]

execute_download(a_selection['url'],audio_filename, asize)
print("audio download complete")

execute_download(v_selection['url'],video_filename, vsize)
print("video download complete")

aprobe = FFProbe(audio_filename)
adec = aprobe['streams'][0]['codec_name']
abr = aprobe['format']['bit_rate']
asr =  aprobe['streams'][0]['sample_rate']

vprobe = FFProbe(video_filename)
vdec = vprobe['streams'][0]['codec_name']
vbr = vprobe['format']['bit_rate']

if adec == 'opus':
    temp_audio = homefolder + "/Desktop/intermediate_audio_.m4a"
    print(Fore.GREEN + "Audio codec is:", end='')
    for i in list(range(0,(32 - len("Audio codec is: ")))):
        print(" ",end='')
    print(Fore.YELLOW + adec)
    print(Fore.WHITE + "    Need to transcode audio from " + adec + " to aac (.m4a)")
    print(Fore.GREEN + "    Intermediate audio file:", end='')
    for i in list(range(0,(32 - len("    Intermediate audio file: ")))):
        print(" ",end='')
    print(Fore.YELLOW + temp_audio)
    ERRCATCH = 0
    try:
        ffmpeg.run(ffmpeg.output(ffmpeg.input(audio_filename,acodec=adec),temp_audio,audio_bitrate=abr,acodec='aac'),capture_stdout=True, capture_stderr=True, input=None, quiet=True, overwrite_output=True)
    except:
        ERRCATCH = 1
    if ERRCATCH == 0:
        os.remove(audio_filename)
        audio_filename = temp_audio
        aprobe = FFProbe(audio_filename)
        adec = aprobe['streams'][0]['codec_name']
        abr = aprobe['format']['bit_rate']
        asr =  aprobe['streams'][0]['sample_rate']
        print(Fore.WHITE + "        Transcoding succeeded!")

print(Fore.GREEN + "\nMuxing media:")
print(Fore.WHITE + "    video:",end='')
for i in list(range(0,(32 - len("    video: ")))):
    print(" ",end='')
print(Fore.YELLOW + video_filename)
print(Fore.WHITE + "        bitrate:",end='')
for i in list(range(0,(32 - len("        bitrate: ")))):
    print(" ",end='')
print(Fore.YELLOW + vbr)
print(Fore.WHITE + "        codec:",end='')
for i in list(range(0,(32 - len("        codec: ")))):
    print(" ",end='')
print(Fore.YELLOW + vdec)

print(Fore.WHITE + "    audio:",end='')
for i in list(range(0,(32 - len("    audio: ")))):
    print(" ",end='')
print(Fore.YELLOW + audio_filename)
print(Fore.WHITE + "        bitrate:",end='')
for i in list(range(0,(32 - len("        bitrate: ")))):
    print(" ",end='')
print(Fore.YELLOW + abr)
print(Fore.WHITE + "        codec:",end='')
for i in list(range(0,(32 - len("        codec: ")))):
    print(" ",end='')
print(Fore.YELLOW + adec)
print(Fore.WHITE + "        sample rate:",end='')
for i in list(range(0,(32 - len("        sample rate: ")))):
    print(" ",end='')
print(Fore.YELLOW + asr)

fname = sanitize(info['title'] + ".mp4")
outfile = homefolder + "/Desktop/" + fname

print(Fore.GREEN + "Muxed video will be saved to:",end='')
for i in list(range(0,(32 - len("Muxed video will be saved to: ")))):
    print(" ",end='')
print(Fore.YELLOW + outfile)
ERRCATCH = 0
try:
    (
        ffmpeg
        .input(audio_filename,acodec=adec)
        .output(outfile)
        .global_args(
            "-hide_banner",
            "-hwaccel","cuda",
            "-c:v",vdec,
            "-i",video_filename,
            "-c:v", "h264_nvenc",
            "-c:a",adec,
            "-b:a",abr,
            "-b:v",vbr,
            "-ar",asr
        )
        .run(
            capture_stdout=True, 
            capture_stderr=True, 
            input=None, 
            quiet=True, 
            overwrite_output=True
        )
    )
except Exception as e:
    ERRCATCH = 1
    last_error = e


if ERRCATCH == 0:
    probef = FFProbe(outfile)
    for i in probef['streams']:
        if i['codec_name'] == vdec:
            vbr=i['bit_rate']
            vdec=i['codec_name']
        if i['codec_name'] == adec:
            abr=i['bit_rate']
            asr=i['sample_rate']
            adec=i['codec_name']
    tbr = probef['format']['bit_rate']
    print(Fore.WHITE + "    Muxing succeeded!")
    print(Fore.GREEN + "Output video details:")
    print(Fore.WHITE + "    Total bitrate:",end='')
    for i in list(range(0,(32 - len("    Total bitrate: ")))):
        print(" ",end='')
    print(Fore.YELLOW + tbr)
    print(Fore.WHITE + "    Audio:")
    print(Fore.WHITE + "        bitrate:",end='')
    for i in list(range(0,(32 - len("        bitrate: ")))):
        print(" ",end='')
    print(Fore.YELLOW + abr)
    print(Fore.WHITE + "        codec:",end='')
    for i in list(range(0,(32 - len("        codec: ")))):
        print(" ",end='')
    print(Fore.YELLOW + adec)
    print(Fore.WHITE + "        sample rate:",end='')
    for i in list(range(0,(32 - len("        sample rate: ")))):
        print(" ",end='')
    print(Fore.YELLOW + asr)
    print(Fore.WHITE + "    Video:")
    print(Fore.WHITE + "        bitrate:",end='')
    for i in list(range(0,(32 - len("        bitrate: ")))):
        print(" ",end='')
    print(Fore.YELLOW + vbr)
    print(Fore.WHITE + "        codec:",end='')
    for i in list(range(0,(32 - len("        codec: ")))):
        print(" ",end='')
    print(Fore.YELLOW + vdec)
    print(Fore.WHITE + "\nDeleting unnecessary files")
    print(Fore.RED + "    deleting:",end='')
    for i in list(range(0,(32 - len("    deleting: ")))):
        print(" ",end='')
    print(Fore.YELLOW + audio_filename)
    print(Fore.RED + "    deleting:",end='')
    for i in list(range(0,(32 - len("    deleting: ")))):
        print(" ",end='')
    print(Fore.YELLOW + video_filename)
    os.remove(audio_filename)
    os.remove(video_filename)
    shutil.rmtree(tempfolder)

"""
    #$mux = cmd /c "ffmpeg 
    "-hide_banner",
    "-hwaccell","cuda",
    "-c:a", adec,
    "-c:v","h264_cuvid",
    "-i",audio_filename,
    "-i",video_filename,
    "-c:v", "h264_nvenc",
    "-c:a",adec,
    "-b:a",abr,
    "-b:v",vbr,
    "-ar",asr
"""
