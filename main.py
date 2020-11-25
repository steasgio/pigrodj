# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
# added pandas
import csv
import time

import tekore as tk
import pandas as pd


def stringifyArtists(artists):
    tArtists = ""
    for a in artists:
        if (a.name is not None):
            if (not tArtists):
                tArtists=a.name
            else:tArtists = tArtists+"-"+a.name
    return tArtists

client_id = 'd14941ce1cb34c0a916d3d24785ec690'
client_secret = '68a390c3cfee4c5da8557af1801d9012'

app_token = tk.request_client_token(client_id, client_secret)

spotify = tk.Spotify(app_token)

redirect_uri = 'http://localhost:8888/callback'

user_token = tk.prompt_for_user_token(
    client_id,
    client_secret,
    redirect_uri,
    scope=tk.scope.every


)

spotify.token = user_token

userid=spotify.current_user().id
#print("userid="+spotify.current_user().id)

def retrieveSongs(myplaylists):
    ct = 0
    result=[]
    try:
        for p in myplaylists.items:
            # print(p.name, p.tracks.total)
            if (ct>1): # for debug , gestiamo solo la prima playlist
                break

            pp = spotify.playlist_items(p.id)
            for myTrack in pp.items:
                #https://tekore.readthedocs.io/en/stable/reference/models.html#tekore.model.FullTrack
                ct = ct + 1
                if (myTrack is not None and myTrack.track is not None and myTrack.track.id is not None):
                    features = spotify.track_audio_features(myTrack.track.id)
                    #https://tekore.readthedocs.io/en/stable/reference/models.html#tekore.model.AudioFeatures
                    tArtists = stringifyArtists(myTrack.track.artists)

                    # print(ct, p.name, tArtists, myTrack.track.name, features.danceability, features.energy)
                    r = {}
                    r["counter"] = ct
                    r["playlist-name"] = p.name
                    
                    r["artist"] = tArtists
                    r["track.name"] = myTrack.track.name
                    r["acousticness"] = features.acousticness
                    r["danceability"] = features.danceability
                    r["energy"] = features.energy
                    r["instrumentalness"] = features.instrumentalness
                    r["liveness"] = features.liveness
                    r["loudness"] = features.loudness
                    r["speechiness"] = features.speechiness
                    r["valence"] = features.valence
                    r["tempo"] = features.tempo
                    r["liveness"] = features.liveness
                    r["id"] = myTrack.track.id
                    r["album"] = myTrack.track.album.name
                    r["duration_ms"] = myTrack.track.duration_ms
                    r["href"] = myTrack.track.href
                    r["preview_url"] = myTrack.track.preview_url
                    # r["audio_preview_url"]=myTrack.track.audio_preview_url
                    r["uri"] = myTrack.track.uri
                    # r["language"]=myTrack.track.language
                    if (ct == 1):
                        # print column names
                        for i in r.keys():
                            print(i, end=";")
                        print("")
                        #writer.writerow(r.keys())

                    for i in r.keys():
                        print(r[i], end=";")
                        # print(r[i],sep=";",end=";")
                    print("")
                    time.sleep(0.2)
                    #writer.writerow(r.values())
                    result.append(r)
        return result
    except tk.BadRequest as ex:
        print("sssssss.........Bad request")
        print(str(ex))
        print(ex.request)
        print(ex.response)
        return result

    except tk.HTTPError as ex:
        print("sssssss.........Http error")
        print(str(ex))
        print(ex.request)
        print(ex.response)
        return result

firstplaylists=spotify.playlists(userid)
#myplaylists=spotify.all_items(firstplaylists)
print("-----playlists---")

#idPlaylistRunAutore="4Ji5tCz5D6g2sFTkOOdcWF"
#debugpl={'items': [{'id':"4Ji5tCz5D6g2sFTkOOdcWF"}]}
songs= retrieveSongs(firstplaylists)
print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
print(songs)

df=pd.DataFrame(songs)
df.head(10)
print("..")
print(df.head(10))
print("..")

print(df.mean)
print("..")

print(df.mean)
def writeCSVofSongs(filename,songs):
    csvFile = open(filename, 'w+')
    try:
        writer = csv.writer(csvFile)
        ct=0
        for s in songs:
            if (ct==0):
                writer.writerow(s.keys())
                ct=1
            else:
                writer.writerow(s.values())
    finally:
        csvFile.close()

writeCSVofSongs("dbgsongs.csv",songs)
