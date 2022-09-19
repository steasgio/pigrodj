# applicazione web semplificata x test sui cloud richiede autenticazione su spotify e richiama api i cui risultati sono visualizzati in html

import tekore as tk
import pandas as pd
from flask import Flask, request, redirect, session
from flask import render_template

from wtforms import Form
from wtforms import StringField, SubmitField, RadioField, SelectField, SelectMultipleField, widgets
import logging

logging.basicConfig(level=logging.DEBUG)
# from wtforms.validators import Required

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


		res = spotify.playlist_add(playlist_id, lPlaylist)


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
		pp = spotify.playlist_items(playlist_id)

		tracks = []
		for t in pp.items:
			tracks.append([t.track.id, t.track.name, t.track.preview_url, t.track.duration_ms, t.track.popularity])
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

		logging.debug("++ test we are logging debug")
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
									   list_id=newPlaylistId)
			elif request.form['submit_button'] == 'split':
				logging.debug("**** split called")

			else:
				logging.debug("**** submit button ="+request.form['submit_button'])

		else:
			try:
				spotify = tk.Spotify(token)
				username = spotify.current_user().display_name
				userid = spotify.current_user().id
				firstplaylists = spotify.playlists(userid)

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
						"numberOfTracks": p.tracks.total

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
			return render_template('playlistsongs.html', dynamicText="eccoci" + "list_id=" + request.values['list_id'],
								   l1Results=_songs)
		# return render_template('results.html', dynamicText="eccoci" + uid )
		# return redirect('/', 307)

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
