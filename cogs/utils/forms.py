from flask_wtf import Form
from wtforms import StringField, SubmitField


class GuildForm(Form):
	prefix = StringField("prefix")
	submit = SubmitField('Save')
