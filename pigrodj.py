# applicazione web semplificata x test sui cloud richiede autenticazione su spotify e richiama api i cui risultati sono visualizzati in html

import tekore as tk
import pandas as pd
from flask import Flask, request, redirect, session
from flask import render_template

from wtforms import Form
from wtforms import StringField, SubmitField, RadioField, SelectField, SelectMultipleField, widgets
import logging
import math
import operator

logging.basicConfig(level=logging.DEBUG)
# from wtforms.validators import Required

def numberToColorRgb(i):
	red = math.floor(255 - (255 * i / 100))
	green = math.floor(255 * i / 100)
	blue = 255
	return f'rgb({red},{green},{blue})'

def stringifyArtists(artists):
    tArtists = ""
    for a in artists:
        if (a.name is not None):
            if (not tArtists):
                tArtists=a.name
            else:tArtists = tArtists+"-"+a.name
    return tArtists

def find_max_list(list):
	''' returns the biggest item in a list'''
	list_len = [len(i) for i in list]
	print(max(list_len))
	return max(list_len)

def split_list(list, size):
	''' splits a list in many lists of a maximum size'''
	'''	usage example:
		l=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
		split_list(l,2)-->
		[[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]]
	'''
	# using list comprehension
	res = [list[i:i + size] for i in range(0, len(list), size)]
	return res


def mixListOfLists(lol):
	''' Takes a list of lists and return a single list built using one item from each input list
		If the input lists are not of the same size it also works
		Parameters
		---------
		lol : a list of list
		Returns
		-------
		r
			a list of items

	'''
	r = []
	_listLenghtMax = find_max_list(lol)
	for ct in range(_listLenghtMax):
		for l in lol:
			if (ct < len(l)):
				r.append(l[ct])
	return r
def splitPlaylistToSpotify(intPlaylistId,strPlaylistName, intMaxMinutes,  token ):
	songsList=retrieveAttributesOfSongsInAPlayslistFromSpotify(intPlaylistId,token)
	intMaxMinutes=intMaxMinutes*60000 #convert minutes in milliseconds
	listLength=0
	targetList=[]
	listCounter=1
	for s in songsList:
		targetList.append(s["id"])
		listLength=listLength+s["duration_ms"]
		if listLength > intMaxMinutes:
			savePlaylistToSpotify(strPlaylistName+"-"+str(listCounter),"by PigroDj",targetList,token)
			logging.debug("writing "+ strPlaylistName+"-"+str(listCounter))
			logging.debug(targetList)
			listCounter=listCounter+1
			targetList=[]
			listLength=0
	if len(targetList)>=1:
		''' create the last sub-list altough below the target length'''
		logging.debug("writing " + strPlaylistName + "-" + str(listCounter))
		logging.debug(targetList)
		savePlaylistToSpotify(strPlaylistName+"-"+str(listCounter),"by PigroDj",targetList,token)
	return "ok"

def cutPlaylistToSpotify(intPlaylistId,strPlaylistName, intMaxMinutes,  token ):
	songsList=retrieveAttributesOfSongsInAPlayslistFromSpotify(intPlaylistId,token)
	intMaxMinutes=intMaxMinutes*60000 #convert minutes in milliseconds
	listLength=0
	targetList=[]

	for s in songsList:
		targetList.append(s["id"])
		listLength=listLength+s["duration_ms"]
		if listLength > intMaxMinutes:
			savePlaylistToSpotify(strPlaylistName+"-"+str(intMaxMinutes//60000),"by PigroDj",targetList,token)
			logging.debug("writing "+ strPlaylistName+"-"+str(intMaxMinutes//60000))
			logging.debug(targetList)
			break

	return "ok"

def filterFTRPlaylistToSpotify(intPlaylistId,strPlaylistName, intMinFTR,  token ):
	songsList=retrieveAttributesOfSongsInAPlayslistFromSpotify(intPlaylistId,token)
	listLength=0
	targetList=[]

	for s in songsList:
		danceability=s["danceability"]
		energy=s["energy"]
		if (danceability is not None and energy is not None):
			if ((danceability>=(intMinFTR/100)) and (energy>=(intMinFTR/100))):
				targetList.append(s["id"])
				listLength=listLength+1
	if listLength > 0:
		savePlaylistToSpotify(strPlaylistName+"-FTR"+str(intMinFTR),"by PigroDj",targetList,token)
		logging.debug("writing "+ strPlaylistName+"-"+str(intMinFTR))
		logging.debug(targetList)

	return "ok"
'''
dfRunnable = df[(df.danceability > 0.5) & (df.energy > 0.5)]
dfRunnableTop = dfRunnable.sort_values(by=['energy'], inplace=False, ascending=False)
dfRunnableTop.drop_duplicates(subset="name",inplace=True)
'''
def sortPlaylistToSpotify(intPlaylistId, strPlaylistName, strDirection, strSortParameter, token):
	songsList=retrieveAttributesOfSongsInAPlayslistFromSpotify(intPlaylistId,token)
	listLength=0
	targetList=[]
	'''
		for s in songsList:
			danceability=s["danceability"]
			energy=s["energy"]
			if (danceability is not None and energy is not None):
				if ((danceability>=(intMinFTR/100)) and (energy>=(intMinFTR/100))):
					targetList.append(s["id"])
					listLength=listLength+1
		if listLength > 0:
			savePlaylistToSpotify(strPlaylistName+"-FTR"+str(intMinFTR),"by PigroDj",targetList,token)
			logging.debug("writing "+ strPlaylistName+"-"+str(intMinFTR))
			logging.debug(targetList)
	'''
	bolReverse=True
	if strDirection=="ASC":
		bolReverse=False
	songsList.sort(key=operator.itemgetter(strSortParameter),reverse=bolReverse)
	for s in songsList:
		targetList.append(s["id"])
	savePlaylistToSpotify(strPlaylistName + "-" + strDirection, "by PigroDj", targetList, token)
	return "ok"
def savePlaylistToSpotify(strPlaylistName, strDestription, songslist, token):
	''' writes a playslist in the Spotify account
	Parameters:
		strPlaylistName: the name with which to save the playlist
		strDestription: stored in Spotify as well
		songslist: a list f songs id
		token: Spotify token needed to retrieve the user logged in Spotify and to authorize the saving
	'''
	trackIds = []
	try:
		# print("userid in buildplaylist 1"+user)
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
			#logging.debug(uri)
			lPlaylist.append(uri)

		splittedPlay=split_list(lPlaylist,100)
		res=[]
		for subl in splittedPlay:
			res = spotify.playlist_add(playlist_id, subl)


		#logging.debug("res=" + res)
		if (res is not None):
			#logging.debug("res is not None")
			#logging.debug(playlist_id)
			return playlist_id
		else:
			logging.error("Unexpected error creating playlist")
			return "error creating playlist"
	except tk.BadRequest as ex:
		logging.error("Bad request.. writing a playlist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)
		return "bad request"

	except tk.HTTPError as ex:
		logging.error("Http error ...writing a playlist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)
		return "Http error"

def renameSpotifyPlaylist(playlist_id, playlist_newname,token):
	try:
		spotify = tk.Spotify(token)
		spotify.playlist_change_details(playlist_id, playlist_newname)
		#spotify.playlist_change_details(playlist_id:playlist_id,name:playlist_newname,description:aDescription)
		return "ok"
	except tk.BadRequest as ex:
		logging.error("Bad request .. renaming playlist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)
		return "ko"

	except tk.HTTPError as ex:
		logging.error("Http error renaming playlist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)
		return "ko"

def deleteSpotifyPlaylist(playlist_id,token):
	'''
	Delete the specified playlist from spotifiy
	:param playlist_id:
	:param token:
	:return: "Ok" if deleted, "ko" if removed

	NB: Spotify api does not allow to delete an api but only to unfollow it (as other users might be following it ) .. so in principle you could recover it
	'''
	try:
		spotify = tk.Spotify(token)
		spotify.playlist_unfollow(playlist_id)
		return "ok"
	except tk.BadRequest as ex:
		logging.error("Bad request .. deleting playlist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)
		return "ko"

	except tk.HTTPError as ex:
		logging.error("Http error deleting playlist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)

def retrievePlaylistSongsFromSpotify(playlist_id, token):
	''' retrieve from Spotify the songs contained in a specified playlist
	Parameters:
		playlist_id: id of the playlist
		token: the Spotify token needed to authorize the request

	Returns:
		A list of track id
	'''

	trackIds = []
	try:
		spotify = tk.Spotify(token)
		pp = spotify.playlist_items(playlist_id)
		trackIds = []
		for t in pp.items:
			trackIds.append(t.track.id)
		return trackIds

	except tk.BadRequest as ex:
		logging.error("Bad request .. retrieving playlist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)
		return trackIds

	except tk.HTTPError as ex:
		logging.error("Http error retrieving playlist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)
		return trackIds


def retrieveAttributesOfSongsInAPlayslistFromSpotify(playlist_id, token):
	''' retrieve from Spotify the songs contained in a specified playlist
	Parameters:
		playlist_id: id of the playlist
		token: the Spotify token needed to authorize the request

	Returns:
		A list of track id, track name, track preview url
	'''

	tracks = []
	try:
		spotify = tk.Spotify(token)
		#the following line retrieve the first 100 item
		p = spotify.playlist_items(playlist_id)
		#the following line paginates until the and (useful method of Tekore)
		pp= spotify.all_items(p)

		listOfId=[]
		'''
		pp2=pp.copy()
		for t1 in pp2:
			listOfId.append(t1.track.id)
			print (t1.track.id)
		'''
		'''
		f = spotify.tracks_audio_features(listOfId)
		#features=spotify.all_items(f)
		count=0
		for ff in f:
			count=count+1
			print(count,ff.id)
		'''
		tracks = []
		for t in pp:
			listOfId.append(t.track.id)
			trackProperties={}
			trackProperties["id"]=t.track.id
			trackProperties["name"] = t.track.name
			trackProperties["preview_url"] = t.track.preview_url
			trackProperties["duration_ms"] = t.track.duration_ms
			trackProperties["popularity"] = t.track.popularity
			trackProperties["artist"] = stringifyArtists(t.track.artists)
			tracks.append(trackProperties)
			#tracks.append([t.track.id, t.track.name, t.track.preview_url, t.track.duration_ms, t.track.popularity])
		subListsOfId=split_list(listOfId,100)
		print(subListsOfId)
		#count=0
		features=[] #list of feature objects (one for each song)
		for i in subListsOfId:
			#count=count+1
			f = spotify.tracks_audio_features(i)
			features=features +f
		#print(len(features))	#print(count, f)

		for c in range(len(tracks)):
			#print(tracks[c]["name"])
			tracks[c]["danceability"] = features[c].danceability
			tracks[c]["energy"] = features[c].energy
			tracks[c]["acousticness"] = features[c].acousticness
			tracks[c]["instrumentalness"] = features[c].instrumentalness
			tracks[c]["liveness"] = features[c].liveness
			tracks[c]["loudness"] = features[c].loudness
			tracks[c]["speechiness"] = features[c].speechiness
			tracks[c]["valence"] = features[c].valence
			tracks[c]["tempo"] = features[c].tempo
			tracks[c]["liveness"] = features[c].liveness

			tracks[c]["funtorun"] = (features[c].energy+features[c].danceability)*100//2
			tracks[c]["isfuntorun"] = (features[c].energy >0.5) and (features[c].danceability>0.5)
		return tracks
	except tk.BadRequest as ex:
		logging.error("Bad request.. retrieving songs in playslist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)
		return tracks

	except tk.HTTPError as ex:
		logging.error("Http error..retrieving songs in a playlist")
		logging.error(str(ex))
		logging.error(ex.request)
		logging.error(ex.response)
		return tracks


class MultiCheckboxField(SelectMultipleField):
	widget = widgets.ListWidget(prefix_label=False)
	option_widget = widgets.CheckboxInput()


class T1Form(Form):
	# name = StringField('What is your name?')
	# example = RadioField('Label', choices=[('value', 'Falcao'), ('value_two', 'Cerezo')])
	# team = SelectMultipleField("as roma",choices=[(1,'tancredi'),(2,'nela'),(3,'maldera')])
	# team2 = MultiCheckboxField('Ita', choices=[(1,'zoff'),(2,'gentile'),(3,'cabrini')])
	myLists = MultiCheckboxField('Ita', choices=[(1, 'zoff'), (2, 'gentile'), (3, 'cabrini')])

	# language = SelectField(u'Programming Language', choices=[('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')])
	# submit = SubmitField('Submit')


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



	@app.route('/', methods=['GET', 'POST'])
	def main():
		''' displays different templates: splash-dj.html if the user is not logged, home-dj.html when logged, playlist_created after a submit '''

		user = session.get('user', None)
		token = users.get(user, None)

		# Return early if no login or old session
		if user is None or token is None:
			session.pop('user', None)
			# return f'User ID: None<br>{login_msg}'
			return render_template('splash-dj.html')

		page = f'User ID: {user}<br>{login_msg}'
		if token.is_expiring:
			token = cred.refresh(token)
			users[user] = token
		if request.method == 'POST':
			# mix(request)
			logging.debug("debugging 1")
			myForm = T1Form(formdata=request.form)
			logging.debug(myForm.myLists.data)
			myForm.myLists.choices = myForm.myLists.data

			myplaylists = myForm.myLists.data
			if myplaylists is None or len(myplaylists)<2:
				return render_template("results.html",dynamicText="Select at least 2 playslists")
			if request.form['submit_button'] == 'mix':
				_playlistWData = []
				for playlist_id in myplaylists:
					# logging.debug("----- playlist ")
					songs = retrievePlaylistSongsFromSpotify(playlist_id, token)
					# logging.debug("*****songs****")
					# logging.debug(songs)
					_playlistWData.append(songs)
					# logging.debug("_playlistWData")
					# logging.debug(_playlistWData)

				_mixedList = mixListOfLists(_playlistWData)

				# logging.debug("@@@@ mixed list")
				# logging.debug(_mixedList)
				# logging.debug("user" + user)
				newPlaylistName = "PigroDj"
				newPlaylistId = savePlaylistToSpotify(newPlaylistName, "Playlist by PigroDJ", _mixedList, token)

				return render_template('playlist_created.html', dynamicText="Playlist " + newPlaylistName + " mixed !",
									   list_id=newPlaylistId,list_name=newPlaylistName)
			elif request.form['submit_button'] == 'join':
				''' concatenate two playlists '''

				_playlistWData = []
				for playlist_id in myplaylists:
					songs = retrievePlaylistSongsFromSpotify(playlist_id, token)
					_playlistWData= _playlistWData+songs
				_mixedList = _playlistWData
				newPlaylistName = "PigroDj"
				newPlaylistId = savePlaylistToSpotify(newPlaylistName, "Playlist by PigroDJ", _mixedList, token)

				return render_template('playlist_created.html', dynamicText="Playlist " + newPlaylistName + " joined !",
									   list_id=newPlaylistId)
			else:
				logging.debug("**** submit button ="+request.form['submit_button'])

		else:
			try:
				''' Home page after login'''
				spotify = tk.Spotify(token)
				username = spotify.current_user().display_name
				userid = spotify.current_user().id
				firstplaylists = spotify.playlists(userid)

				# NOT WORKING : firstplaylists = spotify.followed_playlists(userid,20)

				# for ct, p in enumerate(firstplaylists.items):
				# 	logging.debug(ct, p.id, p.name)
				# logging.debug("And now ..")
				myplaylists = spotify.all_items(firstplaylists)
				_options = []
				_plists_details = {}
				for ct, p in enumerate(myplaylists):
					# logging.debug(ct, p.id,p.name,p.images[0].url)
					#logging.debug(p.name, p.type) --> sempre type="playlist"
					_options.append((p.id, p.name))
					_dictP = {
						#"image": p.images[0].url,
						"image":"",
						"numberOfTracks": p.tracks.total,
						"name":p.name,
						"id":p.id,
						"color4numberOfTracks":numberToColorRgb(p.tracks.total)

					}
					_plists_details[p.id] = _dictP

					# _plists_details.append(p)
					#logging.debug(p.name)
					#logging.debug(p.images[0].url)
					##logging.debug(p.images[1].url)
					##logging.debug(p.images[2].url)

					#logging.debug(p.tracks.total)
					#logging.debug(p.images)

				dynamicText = "Welcome " + username

				myForm = T1Form()
				# myLists = MultiCheckboxField('Ita', choices=[(1, 'zoff'), (2, 'gentile'), (3, 'cabrini')])
				myForm.myLists.choices = [(1, 'tancredi'), (2, 'nela'), (3, 'maldera')]

				myForm.myLists.choices = _options
				# myForm.myLists.choices = q.values.tolist()
				# return render_template('home-dj.html', dynamicText=dynamicText, mytables=showTables, form=myForm)ƒ
				return render_template('home-dj.html', dynamicText=dynamicText, form=myForm,
									   playListsDetails=_plists_details)


			except tk.BadRequest as ex:
				page += '<br>Error in retrieving data'
				logging.error("Bad request retrieving home page playlists")
				logging.error(str(ex))
				logging.error(ex.request)
				logging.error(ex.response)

			except tk.HTTPError as ex:
				page += '<br>Error in retrieving data'
				logging.error("Http error retrieving home page playlists")
				logging.error(str(ex))
				logging.error(ex.request)
				logging.error(ex.response)

			return page

	@app.route('/login', methods=['GET'])
	def login():
		if 'user' in session:
			return redirect('/', 307)

		# scope = tk.scope.user_read_currently_playing
		scope = tk.scope.every
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

	@app.route('/playlistsongs', methods=['GET', 'POST'])
	def playslistsongs():
		''' displays to users the songs contained in a playlist whose id is in the param list_id within the http request '''
		user = session.get('user', None)
		token = users.get(user, None)
		if user is not None and request.values['list_id'] is not None:
			_songs = retrieveAttributesOfSongsInAPlayslistFromSpotify(request.values['list_id'], token)
			logging.debug(_songs)
			lengthOfPlaylist=0
			for s in _songs:
				lengthOfPlaylist=lengthOfPlaylist+s["duration_ms"]
			lengthOfPlaylist =lengthOfPlaylist//60000
			#logging.debug("list_name"+request.values['list_name'])
			return render_template('playlistsongs.html', dynamicText="eccoci" + "list_id=" + request.values['list_id'],
								   l1Results=_songs,lengthOfPlaylist=lengthOfPlaylist, list_name= request.values['list_name'], list_id=request.values['list_id'], fNumberToColorRgb=numberToColorRgb)
		# return render_template('results.html', dynamicText="eccoci" + uid )
		# return redirect('/', 307)

	@app.route('/playlistrename', methods=['GET', 'POST'])
	def playslistrename():
		user = session.get('user', None)
		token = users.get(user, None)
		if user is not None and request.values['rename_list_id'] is not None and request.values['newPlaylistName'] is not None:
			res=renameSpotifyPlaylist(request.values['rename_list_id'],request.values['newPlaylistName'],token)
			if res=="ok":
				return render_template('results.html', dynamicText="Playlist renamed to " + request.values['newPlaylistName']+ "  id="+request.values['rename_list_id'])
			else:
				return render_template('results.html', dynamicText="Error renaming playlist to " + request.values[
					'newPlaylistName'] + "  id=" + request.values['rename_list_id'])

	@app.route('/playlistsplit', methods=['GET', 'POST'])
	def playslistsplit():
		user = session.get('user', None)
		token = users.get(user, None)
		if user is not None and request.values['split_list_id'] is not None and request.values['maxMinutes'] is not None:

			res=splitPlaylistToSpotify(request.values['split_list_id'],request.values['split_list_name'],int(request.values['maxMinutes']),  token )
			if res=="ok":
				return render_template('results.html',
									   dynamicText="Playlist successfully split in sublists with max  length of  " +request.values['maxMinutes'] + " minutes")
			else:
				return render_template('results.html',
									   dynamicText="Error splitting " + request.values[
										   'split_list_id'] + "  minutes=" +
												   request.values['maxMinutes'])
#			res=renameSpotifyPlaylist(request.values['rename_list_id'],request.values['newPlaylistName'],token)
#			if res=="ok":
#				return render_template('results.html', dynamicText="Playlist renamed to " + request.values['newPlaylistName']+ "  id="+request.values['rename_list_id'])
#			else:
#				return render_template('results.html', dynamicText="Error renaming playlist to " + request.values[
#					'newPlaylistName'] + "  id=" + request.values['rename_list_id'])


	@app.route('/playlistcut', methods=['GET', 'POST'])
	def playslistcut():
		user = session.get('user', None)
		token = users.get(user, None)
		if user is not None and request.values['cut_list_id'] is not None and request.values['maxMinutes'] is not None:

			res=cutPlaylistToSpotify(request.values['cut_list_id'],request.values['cut_list_name'],int(request.values['maxMinutes']),  token )
			if res=="ok":
				return render_template('results.html',
									   dynamicText="Playlist successfully cut in sublists with max  length of  " +request.values['maxMinutes'] + " minutes")
			else:
				return render_template('results.html',
									   dynamicText="Error cutting " + request.values[
										   'cut_list_id'] + "  minutes=" +
												   request.values['maxMinutes'])


	@app.route('/playlistfilterFTR', methods=['GET', 'POST'])
	def playslistfilterFTR():
		user = session.get('user', None)
		token = users.get(user, None)
		if user is not None and request.values['filterFTR_list_id'] is not None and request.values['minFTR'] is not None:

			res=filterFTRPlaylistToSpotify(request.values['filterFTR_list_id'],request.values['filterFTR_list_name'],int(request.values['minFTR']),  token )
			if res=="ok":
				return render_template('results.html',
									   dynamicText="Playlist successfully filtered wuth min   " +request.values['minFTR'] + " FunToRun")
			else:
				return render_template('results.html',
									   dynamicText="Error cutting " + request.values[
										   'cut_list_id'] + "  FTR=" +
												   request.values['minFTR'])

	@app.route('/playlistsortup', methods=['GET', 'POST'])
	def playslistsortup():
		user = session.get('user', None)
		token = users.get(user, None)
		if user is not None and request.values['sortUp_list_id'] is not None :

			res=sortPlaylistToSpotify(request.values['sortUp_list_id'], request.values['sortUp_list_name'], "ASC", "funtorun", token)
			if res=="ok":
				return render_template('results.html',
									   dynamicText="Playlist successfully sorted   " )
			else:
				return render_template('results.html',
									   dynamicText="Error sorting " + request.values[
										   'sortUp_list_id'] )


	@app.route('/playlistsortdown', methods=['GET', 'POST'])
	def playslistsortdown():
		user = session.get('user', None)
		token = users.get(user, None)
		if user is not None and request.values['sortDown_list_id'] is not None :

			res=sortPlaylistToSpotify(request.values['sortDown_list_id'], request.values['sortDown_list_name'], "DESC", "funtorun", token)
			if res=="ok":
				return render_template('results.html',
									   dynamicText="Playlist successfully sorted   " )
			else:
				return render_template('results.html',
									   dynamicText="Error sorting " + request.values[
										   'sortDown_list_id'] )

	@app.route('/playlistdelete', methods=['GET', 'POST'])
	def playslistdelete():
		user = session.get('user', None)
		token = users.get(user, None)
		'''
		return render_template('results.html',
							   dynamicText="Playlist deleted " + request.values['deletePlaylistName'] + "  id=" +
										   request.values['delete_list_id'])
		'''
		if user is not None and request.values['delete_list_id'] is not None and request.values['deletePlaylistName'] is not None:
			res=deleteSpotifyPlaylist(request.values['delete_list_id'],token)
			if res=="ok":
				return render_template('results.html', dynamicText="Playlist deleted:  " + request.values['deletePlaylistName']+ "  id="+request.values['delete_list_id'])
			else:
				return render_template('results.html', dynamicText="Error deleting playlist  " + request.values[
					'deletePlaylistName'] + "  id=" + request.values['delete_list_id'])

#rename_list_id
	# @app.route('/mix', methods=['GET', 'POST'])
	def mix(request):
		''' not used any more '''
		logging.debug("debugging 2")
		# logging.debug (request.form)
		# logging.debug ( request.form.get('name', request.args.get('name')))
		# logging.debug("debugging 2")
		myForm = T1Form(formdata=request.form)
		logging.debug(myForm.myLists.data)
		myForm.myLists.choices = myForm.myLists.data
		# return render_template('home-pandas.html', dynamicText=dynamicText, mytables=showTables, form=myForm)
		dynamicText = "Providing results (way2):"
		# for x in range(myForm.myLists.data):

		return render_template('results.html', dynamicText=dynamicText, l1Results=myForm.myLists.data)

	return app


application = app_factory()

if __name__ == '__main__':
	application.run(host="localhost", port=8000, debug=True)
