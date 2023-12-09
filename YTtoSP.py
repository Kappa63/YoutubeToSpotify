import requests
import difflib
import dotenv
import base64
import os
import re

checkSimilarity = lambda original, match: difflib.SequenceMatcher(None, original, match).ratio()

def processBadStrings(s):
    badStrings = "(Audio)|(Official Lyric Video)|(Official Music Video)|(Lyrics)|(Official Audio)"
    return re.sub(badStrings, "", s, flags=re.IGNORECASE)

env = dotenv.find_dotenv()
dotenv.load_dotenv(env)

ytClientID = os.environ["YT_CLIENT_ID"]
ytClientSecret = os.environ["YT_CLIENT_SECRET"]
ytAccessToken = os.environ["YT_ACCESS_TOKEN"]
ytRefreshToken = os.environ["YT_REFRESH_TOKEN"]
authYtHeadGet = {"Authorization": "Bearer "+ytAccessToken}

spClientID = os.environ["SP_CLIENT_ID"]
spClientSecret = os.environ["SP_CLIENT_SECRET"]
b64SpAuth = "Basic "+base64.b64encode(f"{spClientID}:{spClientSecret}".encode("ascii")).decode("utf-8")
spAccessToken = os.environ["SP_ACCESS_TOKEN"]
spRefreshToken = os.environ["SP_REFRESH_TOKEN"]
authSpHeadGet = {"Authorization": "Bearer "+spAccessToken}
authSpHeadPost = {**authSpHeadGet, "Content-Type": "application/json"}

def getNewSpAccessToken():
    global spAccessToken

    a = requests.post("https://accounts.spotify.com/api/token", data={"grant_type":"refresh_token", "refresh_token":spRefreshToken}, headers={"Authorization":b64SpAuth, "Content-Type":"application/x-www-form-urlencoded"})

    spAccessToken = a.json()["access_token"]
    dotenv.set_key(env, "SP_ACCESS_TOKEN", spAccessToken)

def getNewYtAccessToken():
    global ytAccessToken

    a = requests.post("https://oauth2.googleapis.com/token", data={"client_id":ytClientID, "client_secret":ytClientSecret, "refresh_token":ytRefreshToken, "grant_type":"refresh_token"})

    ytAccessToken = a.json()["access_token"]
    dotenv.set_key(env, "YT_ACCESS_TOKEN", ytAccessToken)

def getYtPlaylistItems(pageToken = None):
    y = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params={"part":"snippet", "playlistId":"PLN1bBakaGaHqIZ2-wSGu0nifl7PxINdzk", "maxResults":100, "pageToken":pageToken}, headers=authYtHeadGet)
    
    print(y.status_code)
    if(y.status_code == 401):
        print("Creating New Youtube Access Token & Trying Again")
        getNewYtAccessToken()
        return getYtPlaylistItems(pageToken)
    
    res = y.json()
    return [i["snippet"]["title"] for i in res["items"]] + (getYtPlaylistItems(res["nextPageToken"]) if "nextPageToken" in res else [])

def getUser():
    u = requests.get("https://api.spotify.com/v1/me", headers=authSpHeadGet)

    print(u.status_code)
    if(u.status_code == 401):
        print("Creating New Spotify Access Token & Trying Again")
        getNewSpAccessToken()
        return getUser()

    return u.json()["id"]

def getTrack(searchQ):
    x = requests.get("https://api.spotify.com/v1/search", params={"q":searchQ, "type":"track", "limit":2}, headers=authSpHeadGet)

    print(x.status_code)
    if(x.status_code == 401):
        print("Creating New Spotify Access Token & Trying Again")
        getNewSpAccessToken()
        return getTrack(searchQ)

    return x.json()["tracks"]["items"][0]["uri"]

def createPlaylist(uID, name:str, public = True, description = ""):
    p = requests.post(f"https://api.spotify.com/v1/users/{uID}/playlists", data='{"name": "'+name+'", "description": "'+description+'", "public": '+str(public).lower()+'}', headers=authSpHeadPost)

    print(p.status_code)
    if(p.status_code == 401):
        print("Creating New Spotify Access Token & Trying Again")
        getNewSpAccessToken()
        return createPlaylist(name, public, description)

    return p.json()["id"]

def addToSpPlaylist(playlistID, URIs):
    t = requests.post(f"https://api.spotify.com/v1/playlists/{playlistID}/tracks", data='{"uris":['+URIs+']}', headers=authSpHeadPost)
    
    print(t.status_code)
    if(t.status_code == 401):
        print("Creating New Spotify Access Token & Trying Again")
        getNewSpAccessToken()
        return addToSpPlaylist(playlistID, URIs)

    return t.json()

user = getUser()

pID  = createPlaylist(user, "Faggotry", public=False, description="Music Fit for a Faggot.")
x = [processBadStrings(i) for i in getYtPlaylistItems()]
trackURIs = ",".join(f'"{getTrack(i)}"' for i in x)

print(addToSpPlaylist(pID, trackURIs))