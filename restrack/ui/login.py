import panel as pn
from restrack.ui.find_investigations import Find_investigations

class Login():

    def __init__(self):
        pn.extension(notifications=True)
        self.username= 'user1'#pn.state.user
        self.server=self.start_server()
       


    def login(self):
        logout = pn.widgets.Button(name="Log out")
        logout.js_on_click(code="""window.location.href = './logout'""")
        tag = pn.widgets.Button(name="Tag")
        tag.on_click(self.open_tagging)
        return pn.Column(f"Congrats `{pn.state.user}`. You got access!", logout,tag).servable()
    
    def open_tagging(self, args):
        my_investigations = Find_investigations(self.username)

    def start_server(self):
        app=self.login()
        server=pn.serve(app, title= 'login_app', basic_auth='././data/users.json', cookie_secret="my-super-secret-secret", oauth='optional')
        return server
    
    
