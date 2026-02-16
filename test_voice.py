import edge_tts
import asyncio

async def list_voices():
    voices = await edge_tts.list_voices()
    vi_voices = [v for v in voices if v["Locale"].startswith("vi")]
    for v in vi_voices:
        print(f"{v['ShortName']:30s} {v['Gender']:8s} {v['FriendlyName']}")

asyncio.run(list_voices())
