#applicazione web semplificata x test sui cloud richiede autenticazione su spotify e richiama api i cui risultati sono visualizzati in html

import tekore as tk
import pandas as pd
from flask import Flask, request, redirect, session
from flask import render_template

from wtforms import Form
from wtforms import StringField, SubmitField, RadioField, SelectField, SelectMultipleField,widgets
#from wtforms.validators import Required
def find_max_list(list):
    list_len = [len(i) for i in list]
    print(max(list_len))
    return max(list_len)

def mixListOfLists(lol):
    r = []
    _listLenghtMax=find_max_list(lol)
    for ct in range(_listLenghtMax):
        for l in lol:
            if (ct < len(l)):
                r.append(l[ct])
    return r


def buildPlaylist(strPlaylistName, strDestription, songslist, token):
    trackIds = []
    try:
        #print("userid in buildplaylist 1"+user)
        spotify = tk.Spotify(token)
        userid = spotify.current_user().id
        myPlaylist = spotify.playlist_create(
            userid,
            strPlaylistName,
            public=False,
            description=strDestription
        )
        playlist_id = myPlaylist.id
        lPlaylist = []
        for s in songslist:
            uri = "spotify:track:" + s
            print(uri)
            lPlaylist.append(uri)

        res=spotify.playlist_add(playlist_id, lPlaylist)
        if (res is not None):
            return playlist_id
        else:
            print("error creating playlist")
            return "error creating playlist"
    except tk.BadRequest as ex:
        print("sssssss.........Bad request")
        print(str(ex))
        print(ex.request)
        print(ex.response)
        return "bad request"

    except tk.HTTPError as ex:
        print("sssssss.........Http error")
        print(str(ex))
        print(ex.request)
        print(ex.response)
        return "Http error"

def retrieveSongs(playlist_id,token):
    ct = 0
    trackIds = []
    try:
        spotify = tk.Spotify(token)
        p=spotify.playlist(playlist_id)
        # print(p.name, p.tracks.total)
        #    break

        pp = spotify.playlist_items(playlist_id)

        trackIds=[]
        for t in pp.items:
            trackIds.append(t.track.id)

        return trackIds
    except tk.BadRequest as ex:
        print("sssssss.........Bad request")
        print(str(ex))
        print(ex.request)
        print(ex.response)
        return trackIds

    except tk.HTTPError as ex:
        print("sssssss.........Http error")
        print(str(ex))
        print(ex.request)
        print(ex.response)
        return trackIds

def retrieveSongsIDNames(playlist_id,token):
    ct = 0
    tracks = []
    try:
        spotify = tk.Spotify(token)
        p=spotify.playlist(playlist_id)
        # print(p.name, p.tracks.total)
        #    break

        pp = spotify.playlist_items(playlist_id)

        tracks=[]
        for t in pp.items:
            tracks.append([t.track.id,t.track.name])

        return tracks
    except tk.BadRequest as ex:
        print("sssssss.........Bad request")
        print(str(ex))
        print(ex.request)
        print(ex.response)
        return tracks

    except tk.HTTPError as ex:
        print("sssssss.........Http error")
        print(str(ex))
        print(ex.request)
        print(ex.response)
        return tracks


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class T1Form(Form):
    #name = StringField('What is your name?')
    #example = RadioField('Label', choices=[('value', 'Falcao'), ('value_two', 'Cerezo')])
    #team = SelectMultipleField("as roma",choices=[(1,'tancredi'),(2,'nela'),(3,'maldera')])
    #team2 = MultiCheckboxField('Ita', choices=[(1,'zoff'),(2,'gentile'),(3,'cabrini')])
    myLists = MultiCheckboxField('Ita', choices=[(1, 'zoff'), (2, 'gentile'), (3, 'cabrini')])

    #language = SelectField(u'Programming Language', choices=[('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')])
    #submit = SubmitField('Submit')


conf = tk.config_from_file("ppapp.cfg")

cred = tk.Credentials(*conf)
spotify = tk.Spotify()

auths = {}  # Ongoing authorisations: state -> UserAuth
users = {}  # User tokens: state -> token (use state as a user ID)

in_link = '<a href="/login">login</a>'
out_link = '<a href="/logout">logout</a>'
login_msg = f'You can {in_link} or {out_link}'


def app_factory() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'aliens'


    @app.route('/', methods=['GET','POST'])
    def main():

        user = session.get('user', None)
        token = users.get(user, None)

        # Return early if no login or old session
        if user is None or token is None:
            session.pop('user', None)
            #return f'User ID: None<br>{login_msg}'
            return render_template('splash-dj.html')

        page = f'User ID: {user}<br>{login_msg}'
        if token.is_expiring:
            token = cred.refresh(token)
            users[user] = token
        if request.method == 'POST':
            #mix(request)
            print ("debugging 1")
            myForm = T1Form(formdata=request.form)
            print (myForm.myLists.data)
            myForm.myLists.choices = myForm.myLists.data
            dynamicText= "Providing results:"
            myplaylists=myForm.myLists.data
            _playlistWData=[]
            for playlist_id in myplaylists:
                print("----- playlist ")
                songs=retrieveSongs(playlist_id,token)
                print("*****songs****")
                print(songs)
                _playlistWData.append(songs)
                print("_playlistWData")
                print(_playlistWData)


            _mixedList=mixListOfLists(_playlistWData)

            print("@@@@ mixed list")
            print(_mixedList)
            print("user"+user)
            newPlaylistName="PigroDj"
            newPlaylistId=buildPlaylist(newPlaylistName,"Playlist by PigroDJ",_mixedList, token)


            return render_template('playlist_created.html', dynamicText="Playlist "+newPlaylistName+" mixed !", list_id=newPlaylistId)
        else:
            try:
                spotify = tk.Spotify(token)
                username=spotify.current_user().display_name
                userid=spotify.current_user().id
                firstplaylists = spotify.playlists(userid)


                for ct, p in enumerate(firstplaylists.items):
                    print(ct, p.id,p.name)
                print("And now ..")
                myplaylists=spotify.all_items(firstplaylists)
                _options=[]
                _plists_details={}
                for ct, p in enumerate(myplaylists):
                    #print(ct, p.id,p.name,p.images[0].url)
                    _options.append((p.id,p.name))
                    _dictP={
                        "image":p.images[0].url,
                        "numberOfTracks":p.tracks.total
                    }
                    _plists_details[p.id]=_dictP

                    #_plists_details.append(p)
                    print(p.name)
                    print(p.images[0].url)
                    ##print(p.images[1].url)
                    ##print(p.images[2].url)


                    print(p.tracks.total)
                    print(p.images)


                dynamicText = "Welcome "+username

                myForm = T1Form()
                #myLists = MultiCheckboxField('Ita', choices=[(1, 'zoff'), (2, 'gentile'), (3, 'cabrini')])
                myForm.myLists.choices = [(1, 'tancredi'), (2, 'nela'), (3, 'maldera')]


                myForm.myLists.choices =_options
                #myForm.myLists.choices = q.values.tolist()
                # return render_template('home-dj.html', dynamicText=dynamicText, mytables=showTables, form=myForm)ƒ
                return render_template('home-dj.html', dynamicText=dynamicText, form=myForm, playListsDetails=_plists_details)


            except tk.BadRequest as ex:
                page += '<br>Error in retrieving data'
                print("sssssss.........Bad request")
                print(str(ex))
                print(ex.request)
                print(ex.response)

            except tk.HTTPError as ex:
                page += '<br>Error in retrieving data'
                print("sssssss.........Http error")
                print(str(ex))
                print(ex.request)
                print(ex.response)

            return page

    @app.route('/login', methods=['GET'])
    def login():
        if 'user' in session:
            return redirect('/', 307)

        #scope = tk.scope.user_read_currently_playing
        scope=tk.scope.every
        auth = tk.UserAuth(cred, scope)
        auths[auth.state] = auth
        return redirect(auth.url, 307)

    @app.route('/callback', methods=['GET'])
    def login_callback():
        code = request.args.get('code', None)
        state = request.args.get('state', None)
        auth = auths.pop(state, None)

        if auth is None:
            return 'Invalid state!', 400

        token = auth.request_token(code, state)
        session['user'] = state
        users[state] = token
        return redirect('/', 307)

    @app.route('/logout', methods=['GET'])
    def logout():
        uid = session.pop('user', None)
        if uid is not None:
            users.pop(uid, None)
        return redirect('/', 307)


    @app.route('/playlistsongs', methods=['GET','POST'])
    def playslistsongs():

        user = session.get('user', None)
        token = users.get(user, None)
        if user is not None and request.values['list_id'] is not None:
            _songs=retrieveSongsIDNames(request.values['list_id'],token)
            print(_songs)
            return render_template('playlistsongs.html', dynamicText="eccoci"+ "list_id="+request.values['list_id'], l1Results= _songs)
        #return render_template('results.html', dynamicText="eccoci" + uid )
        #return redirect('/', 307)


    #@app.route('/mix', methods=['GET', 'POST'])
    def mix(request):
        print("debugging 2")
        # print (request.form)
        # print ( request.form.get('name', request.args.get('name')))
        # print("debugging 2")
        myForm = T1Form(formdata=request.form)
        print(myForm.myLists.data)
        myForm.myLists.choices = myForm.myLists.data
        # return render_template('home-pandas.html', dynamicText=dynamicText, mytables=showTables, form=myForm)
        dynamicText = "Providing results (way2):"
        # for x in range(myForm.myLists.data):

        return render_template('results.html', dynamicText=dynamicText, l1Results=myForm.myLists.data)
    return app




if __name__ == '__main__':
    application = app_factory()

    application.run(host="localhost", port=8000, debug=True)
