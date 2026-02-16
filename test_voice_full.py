import asyncio
import edge_tts

async def list_all():
    voices = await edge_tts.list_voices()
    for v in voices:
        if v["Locale"].startswith("vi"):
            print(v)

asyncio.run(list_all())
