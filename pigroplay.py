#applicazione web richiede autenticazione su spotify e richiama api i cui risultati sono visualizzati in html

import tekore as tk
import pandas as pd
from flask import Flask, request, redirect, session
from flask import render_template

from wtforms import Form
from wtforms import StringField, SubmitField, RadioField, SelectField, SelectMultipleField,widgets
#from wtforms.validators import Required

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class T1Form(Form):
    name = StringField('What is your name?')
    example = RadioField('Label', choices=[('value', 'Falcao'), ('value_two', 'Cerezo')])
    team = SelectMultipleField("as roma",choices=[(1,'tancredi'),(2,'nela'),(3,'maldera')])
    team2 = MultiCheckboxField('Ita', choices=[(1,'zoff'),(2,'gentile'),(3,'cabrini')])
    language = SelectField(u'Programming Language', choices=[('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')])
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

    @app.route("/execute1",methods=['GET','POST'])
    def execute1():
        form=T1Form()
        result="something to show"
        for i in   form.team.choices:
            result=result+i
        return result
    @app.route('/', methods=['GET','POST'])
    def main():

        user = session.get('user', None)
        token = users.get(user, None)

        # Return early if no login or old session
        if user is None or token is None:
            session.pop('user', None)
            return f'User ID: None<br>{login_msg}'

        page = f'User ID: {user}<br>{login_msg}'
        if token.is_expiring:
            token = cred.refresh(token)
            users[user] = token
        if request.method == 'POST':
            print ("debugging 1")
            print (request.form)
            print ( request.form.get('name', request.args.get('name')))
            print("debugging 2")
            myForm = T1Form(formdata=request.form)
            print (myForm.team.data)
            print(myForm.team2.data)
            print(myForm.language.data)
            print(myForm.example.data)
            print(myForm.name.data)
        try:
            '''
                with spotify.token_as(token):
                    playback = spotify.playback_currently_playing()
    
                item = playback.item.name if playback else None
                page += f'<br>Now playing: {item}'
            '''

            dynamicText = ""
            playlists = df.groupby("playlist-name")["playlist-name"].count()

            # dynamicText= dynamicText+ dfPlaylists.to_html(header="true", table_id="table", escape=False)

            showTables = []
            dfRunnable = df[(df.danceability > 0.5) & (df.energy > 0.5)]
            dfRunnable.drop_duplicates(subset="id",inplace=True)


            dfRunnableTop = dfRunnable.sort_values(by=['energy'], inplace=False, ascending=False)

            showTables.append({"heading": "Runnable Top 30", "dataframe": dfRunnableTop.head(30)})
            dfRunnableBottom = dfRunnable.sort_values(by=['energy'], inplace=False, ascending=True)
            showTables.append({"heading": "Runnable Bottom 10", "dataframe": dfRunnableBottom.head(10)})

            # print(df[(df.danceability>0.5)&(df.energy>0.5)].count())
            # dff=df[(df.danceability>0.5)&(df.energy>0.5)].head(100)
            # return render_template('home-pandas.html', mytable=dff)
            myForm = T1Form()

            ''' not working
            pls = df.pivot_table(index=['playlist-name'],
                                   values=['playlist-name','playlist-name'],
                                   aggfunc='count')
            '''
            q = df.groupby(['playlist-name'])['playlist-name'].agg('count').to_frame('c').reset_index()
            q.sort_values(by=['c'],ascending=False, inplace=True )
            q['c']=q['playlist-name']+" "+q['c'].astype(str)
            #pls.sort_values(ascending=False)
            myForm.team2.choices = q.values.tolist()

            #myForm.team2.choices=dfRunnable[['playlist-name','playlist-name']].values.tolist()
            #myForm.team2.choices=[(1,'oriali'),(2,'collovati')]
            return render_template('home-pandas.html', dynamicText=dynamicText, mytables=showTables, form=myForm)
        except tk.HTTPError:
            page += '<br>Error in retrieving now playing!'

        return page

    @app.route('/login', methods=['GET'])
    def login():
        if 'user' in session:
            return redirect('/', 307)

        scope = tk.scope.user_read_currently_playing
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

    return app




if __name__ == '__main__':
    application = app_factory()
    #application.run('localhost', 8000)
    df = pd.read_csv("mysongs.csv")
    application.run(host="localhost", port=8000, debug=True)
