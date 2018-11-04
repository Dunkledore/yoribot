from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField


class GuildForm(FlaskForm):
	submit = SubmitField('Save')
	guildID = HiddenField()

