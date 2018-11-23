from discord.ext import commands
from .utils import checks
import aiohttp
from discord import Embed



class Weather:
	"""Get the weather"""

	def __init__(self, bot):
		self.bot = bot
		self.category = "tools"
		self.key = None
		self.bot.loop.create_task(self.update_key())
		self.countries = {'AF': 'Afghanistan', 'AL': 'Albania', 'DZ': 'Algeria', 'AS': 'American Samoa',
		                  'AD': 'Andorra', 'AO': 'Angola', 'AI': 'Anguilla', 'AQ': 'Antarctica',
		                  'AG': 'Antigua and Barbuda', 'AR': 'Argentina', 'AM': 'Armenia', 'AW': 'Aruba',
		                  'AU': 'Australia', 'AT': 'Austria', 'AZ': 'Azerbaijan', 'BS': 'Bahamas', 'BH': 'Bahrain',
		                  'BD': 'Bangladesh', 'BB': 'Barbados', 'BY': 'Belarus', 'BE': 'Belgium', 'BZ': 'Belize',
		                  'BJ': 'Benin', 'BM': 'Bermuda', 'BT': 'Bhutan', 'BO': 'Bolivia, Plurinational State of',
		                  'BQ': 'Bonaire, Sint Eustatius and Saba', 'BA': 'Bosnia and Herzegovina', 'BW': 'Botswana',
		                  'BV': 'Bouvet Island', 'BR': 'Brazil', 'IO': 'British Indian Ocean Territory',
		                  'BN': 'Brunei Darussalam', 'BG': 'Bulgaria', 'BF': 'Burkina Faso', 'BI': 'Burundi',
		                  'KH': 'Cambodia', 'CM': 'Cameroon', 'CA': 'Canada', 'CV': 'Cape Verde',
		                  'KY': 'Cayman Islands', 'CF': 'Central African Republic', 'TD': 'Chad', 'CL': 'Chile',
		                  'CN': 'China', 'CX': 'Christmas Island', 'CC': 'Cocos (Keeling) Islands', 'CO': 'Colombia',
		                  'KM': 'Comoros', 'CG': 'Congo', 'CD': 'Congo, the Democratic Republic of the',
		                  'CK': 'Cook Islands', 'CR': 'Costa Rica', 'Code': 'Country name', 'HR': 'Croatia',
		                  'CU': 'Cuba', 'CW': 'Curaçao', 'CY': 'Cyprus', 'CZ': 'Czech Republic', 'CI': "Côte d'Ivoire",
		                  'DK': 'Denmark', 'DJ': 'Djibouti', 'DM': 'Dominica', 'DO': 'Dominican Republic',
		                  'EC': 'Ecuador', 'EG': 'Egypt', 'SV': 'El Salvador', 'GQ': 'Equatorial Guinea',
		                  'ER': 'Eritrea', 'EE': 'Estonia', 'ET': 'Ethiopia', 'FK': 'Falkland Islands (Malvinas)',
		                  'FO': 'Faroe Islands', 'FJ': 'Fiji', 'FI': 'Finland', 'FR': 'France', 'GF': 'French Guiana',
		                  'PF': 'French Polynesia', 'TF': 'French Southern Territories', 'GA': 'Gabon', 'GM': 'Gambia',
		                  'GE': 'Georgia', 'DE': 'Germany', 'GH': 'Ghana', 'GI': 'Gibraltar', 'GR': 'Greece',
		                  'GL': 'Greenland', 'GD': 'Grenada', 'GP': 'Guadeloupe', 'GU': 'Guam', 'GT': 'Guatemala',
		                  'GG': 'Guernsey', 'GN': 'Guinea', 'GW': 'Guinea-Bissau', 'GY': 'Guyana', 'HT': 'Haiti',
		                  'HM': 'Heard Island and McDonald Islands', 'VA': 'Holy See (Vatican City State)',
		                  'HN': 'Honduras', 'HK': 'Hong Kong', 'HU': 'Hungary', '(.uk)': 'ISO 3166-2:GB',
		                  'IS': 'Iceland', 'IN': 'India', 'ID': 'Indonesia', 'IR': 'Iran, Islamic Republic of',
		                  'IQ': 'Iraq', 'IE': 'Ireland', 'IM': 'Isle of Man', 'IL': 'Israel', 'IT': 'Italy',
		                  'JM': 'Jamaica', 'JP': 'Japan', 'JE': 'Jersey', 'JO': 'Jordan', 'KZ': 'Kazakhstan',
		                  'KE': 'Kenya', 'KI': 'Kiribati', 'KP': "Korea, Democratic People's Republic of",
		                  'KR': 'Korea, Republic of', 'KW': 'Kuwait', 'KG': 'Kyrgyzstan',
		                  'LA': "Lao People's Democratic Republic", 'LV': 'Latvia', 'LB': 'Lebanon', 'LS': 'Lesotho',
		                  'LR': 'Liberia', 'LY': 'Libya', 'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg',
		                  'MO': 'Macao', 'MK': 'Macedonia, the former Yugoslav Republic of', 'MG': 'Madagascar',
		                  'MW': 'Malawi', 'MY': 'Malaysia', 'MV': 'Maldives', 'ML': 'Mali', 'MT': 'Malta',
		                  'MH': 'Marshall Islands', 'MQ': 'Martinique', 'MR': 'Mauritania', 'MU': 'Mauritius',
		                  'YT': 'Mayotte', 'MX': 'Mexico', 'FM': 'Micronesia, Federated States of',
		                  'MD': 'Moldova, Republic of', 'MC': 'Monaco', 'MN': 'Mongolia', 'ME': 'Montenegro',
		                  'MS': 'Montserrat', 'MA': 'Morocco', 'MZ': 'Mozambique', 'MM': 'Myanmar', 'NA': 'Namibia',
		                  'NR': 'Nauru', 'NP': 'Nepal', 'NL': 'Netherlands', 'NC': 'New Caledonia', 'NZ': 'New Zealand',
		                  'NI': 'Nicaragua', 'NE': 'Niger', 'NG': 'Nigeria', 'NU': 'Niue', 'NF': 'Norfolk Island',
		                  'MP': 'Northern Mariana Islands', 'NO': 'Norway', 'OM': 'Oman', 'PK': 'Pakistan',
		                  'PW': 'Palau', 'PS': 'Palestine, State of', 'PA': 'Panama', 'PG': 'Papua New Guinea',
		                  'PY': 'Paraguay', 'PE': 'Peru', 'PH': 'Philippines', 'PN': 'Pitcairn', 'PL': 'Poland',
		                  'PT': 'Portugal', 'PR': 'Puerto Rico', 'QA': 'Qatar', 'RO': 'Romania',
		                  'RU': 'Russian Federation', 'RW': 'Rwanda', 'RE': 'Réunion', 'BL': 'Saint Barthélemy',
		                  'SH': 'Saint Helena, Ascension and Tristan da Cunha', 'KN': 'Saint Kitts and Nevis',
		                  'LC': 'Saint Lucia', 'MF': 'Saint Martin (French part)', 'PM': 'Saint Pierre and Miquelon',
		                  'VC': 'Saint Vincent and the Grenadines', 'WS': 'Samoa', 'SM': 'San Marino',
		                  'ST': 'Sao Tome and Principe', 'SA': 'Saudi Arabia', 'SN': 'Senegal', 'RS': 'Serbia',
		                  'SC': 'Seychelles', 'SL': 'Sierra Leone', 'SG': 'Singapore',
		                  'SX': 'Sint Maarten (Dutch part)', 'SK': 'Slovakia', 'SI': 'Slovenia',
		                  'SB': 'Solomon Islands', 'SO': 'Somalia', 'ZA': 'South Africa',
		                  'GS': 'South Georgia and the South Sandwich Islands', 'SS': 'South Sudan', 'ES': 'Spain',
		                  'LK': 'Sri Lanka', 'SD': 'Sudan', 'SR': 'Suriname', 'SJ': 'Svalbard and Jan Mayen',
		                  'SZ': 'Swaziland', 'SE': 'Sweden', 'CH': 'Switzerland', 'SY': 'Syrian Arab Republic',
		                  'TW': 'Taiwan, Province of China', 'TJ': 'Tajikistan', 'TZ': 'Tanzania, United Republic of',
		                  'TH': 'Thailand', 'TL': 'Timor-Leste', 'TG': 'Togo', 'TK': 'Tokelau', 'TO': 'Tonga',
		                  'TT': 'Trinidad and Tobago', 'TN': 'Tunisia', 'TR': 'Turkey', 'TM': 'Turkmenistan',
		                  'TC': 'Turks and Caicos Islands', 'TV': 'Tuvalu', 'UG': 'Uganda', 'UA': 'Ukraine',
		                  'AE': 'United Arab Emirates', 'GB': 'United Kingdom', 'US': 'United States',
		                  'UM': 'United States Minor Outlying Islands', 'UY': 'Uruguay', 'UZ': 'Uzbekistan',
		                  'VU': 'Vanuatu', 'VE': 'Venezuela, Bolivarian Republic of', 'VN': 'Viet Nam',
		                  'VG': 'Virgin Islands, British', 'VI': 'Virgin Islands, U.S.', 'WF': 'Wallis and Futuna',
		                  'EH': 'Western Sahara', 'YE': 'Yemen', 'ZM': 'Zambia', 'ZW': 'Zimbabwe',
		                  'AX': 'Åland Islands'}

	async def update_key(self):
		query = "SELECT key FROM weather"
		key = await self.bot.pool.fetchval(query)
		self.key = key
		return key

	@commands.command(aliases=['temp', 'temperature'])
	@commands.guild_only()
	async def weather(self, ctx, *, location: str):
		"""Get the weather"""
		if not self.key:
			await ctx.send(embed=self.bot.error("No API key set"))
			return

		async with aiohttp.ClientSession() as cs:
			payload = {'q': location, 'appid': self.key}
			url = 'http://api.openweathermap.org/data/2.5/weather?'
			async with cs.get(url, params=payload) as r:
				data = await r.json()

			if data['cod'] != 200:
				await ctx.send(embed=self.bot.error("Location Not Found"))
				return

			celsius = data['main']['temp']-273
			fahrenheit = celsius*9/5+32
			humidity = data['main']['humidity']
			pressure = data['main']['pressure']
			wind_kmh = data['wind']['speed']*3.6
			wind_mph = wind_kmh*0.621371
			clouds = data['weather'][0]['description'].title()
			icon = f"https://openweathermap.org/img/w/{data['weather'][0]['icon']}.png"
			place = data['name']
			country = self.countries.get(data['sys']['country'], '')
			city_id = data['id']

			embed = Embed(color=ctx.message.author.color,
			                      title=f"{clouds} in {place}, {country}",
			                      url=f"https://openweathermap.org/city/{city_id}")
			embed.add_field(name="**Temperature**",
			                value=f"{celsius:.1f}°C\n{fahrenheit:.1f}°F")
			embed.add_field(name="**Wind Speed**",
			                value=f"{wind_kmh:.1f} km/h\n{wind_mph:.1f} mph")
			embed.add_field(name="**Pressure**",
			                value=f"{pressure} hPa")
			embed.add_field(name="**Humidity**",
			                value=f"{humidity}%")
			embed.set_image(url=f"https://openweathermap.org/img/w/{icon}.png")
			embed.set_footer(text='Weather data provided by OpenWeatherMap',
			                 icon_url='http://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/icons/logo_16x16.png')
			await ctx.send(embed=embed)

	@commands.command(hidden=True)
	@checks.is_developer()
	async def weatherkey(self, ctx, key: str):
		"""Acquire a key from  http://openweathermap.org/"""
		query = "DELETE FROM weather"
		insertquery = "INSERT INTO weather (key) VALUES ($1)"
		await self.bot.pool.execute(query)
		await self.bot.pool.execute(insertquery, key)
		await self.update_key()
		await ctx.send(embed=self.bot.success("Key saved! It might take a minute or ten before the key is active if you just registered it."))


def setup(bot):
	bot.add_cog(Weather(bot))
