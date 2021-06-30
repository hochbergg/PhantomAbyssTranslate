from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json
import jinja2
import time
import re
import datetime

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '12w1foShEkiWhKd1ktgwWi8zJv9icKjuQVwRCe17_SVg'
RANGE_NAME = "'Glyph Handbook'!A1:X263"

def download_glyphs():
	"""Shows basic usage of the Sheets API.
	Prints values from a sample spreadsheet.
	"""
	creds = None
	# The file token.json stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists('token.json'):
		creds = Credentials.from_authorized_user_file('token.json', SCOPES)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				'credentials.json', SCOPES)
			creds = flow.run_local_server(port=0)
		# Save the credentials for the next run
		with open('token.json', 'w') as token:
			token.write(creds.to_json())

	service = build('sheets', 'v4', credentials=creds)

	# Call the Sheets API
	sheet = service.spreadsheets()
	result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
								range=RANGE_NAME).execute()
	values = result.get('values', [])

	glyphs = []
	for r in values[1:]:
		glyphs.append({
			"number": r[0],
			"glyph": r[1],
			"status": r[15],
			"meaning": r[16],
			"reason": r[17],
			"breakdown": r[12],
		})
	
	with open('sheet_glyphs.json','w') as f:
		f.write(json.dumps({
			"glyphs": glyphs,
			"at": datetime.datetime.utcnow().timestamp()
		}))

def load_glyphs():
	with open('sheet_glyphs.json','r') as f:
		return json.load(f)
		
		
from jinja2 import Environment, FunctionLoader, select_autoescape

def load_template(name):
	with open(f'templates/{name}','r') as f:
		return f.read()
		

def filter_replace_glyph_references(value):
	return re.sub('#([0-9]{3})', '<a href="#glyph_\\1" class="glyph-link">#\\1</a>', value)

jinja_env = Environment(
	loader=FunctionLoader(load_template),
	autoescape=select_autoescape(),
)
jinja_env.filters['replace_glyph_references'] = filter_replace_glyph_references

def render_template(name, vars):
	with open(f'dist/{name}','w') as f:
		template = jinja_env.get_template(name)
		f.write(template.render(**vars))
	
def render_glyphs_page(data):
	render_template('glyphs.html', {"glyphs": data['glyphs'], 'at': datetime.datetime.fromtimestamp(data['at'])})


if __name__ == '__main__':
	#main()
	download_glyphs()
	render_glyphs_page(load_glyphs())