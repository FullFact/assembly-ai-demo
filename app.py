import websockets
import asyncio
import base64
import json
from configure import auth_key
import subprocess
import os

FRAMES_PER_BUFFER = 3200
CHANNELS = 1
RATE = 16000


# the AssemblyAI endpoint we're going to hit
URL = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={RATE}"


async def send_receive(stream):
    print(f"Connecting websocket to url ${URL}")
    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", auth_key),),
        ping_interval=5,
        ping_timeout=20
    ) as _ws:
        await asyncio.sleep(0.1)
        print("Receiving SessionBegins ...")
        session_begins = await _ws.recv()
        print(session_begins)
        print("Sending messages ...")

        async def send():
            while True:
                try:
                    data = stream.read(FRAMES_PER_BUFFER)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    await _ws.send(json_data)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    print(e.code)
                except Exception:
                    assert False, "Not a websocket 4008 error"
                await asyncio.sleep(0.01)

            return True

        async def receive():
            while True:
                try:
                    result_str = await _ws.recv()
                    result = json.loads(result_str)
                    if result.get("message_type") == "FinalTranscript":
                        print(result["text"])
                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    print(e.code)
                except Exception:
                    assert False, "Not a websocket 4008 error"

        send_result, receive_result = await asyncio.gather(send(), receive())


YT_URL = "https://www.youtube.com/watch?v=cumJ1t7cCx4"

cmd_yt_dlp = ["yt-dlp", YT_URL, "-f", "wav/bestaudio/best", "-o", "-"]
cmd_ffmpeg = [
    "ffmpeg",
    "-re",  # realtime
    "-i",
    "pipe:",
    "-ac",
    str(CHANNELS),
    "-ar",
    str(RATE),
    "-f",
    "wav",
    "pipe:",
]

p_in, p_out = os.pipe()

with subprocess.Popen(cmd_yt_dlp, stdout=p_out, stderr=subprocess.DEVNULL):
    with subprocess.Popen(cmd_ffmpeg, stdin=p_in, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as stream:
        asyncio.run(send_receive(stream.stdout))
