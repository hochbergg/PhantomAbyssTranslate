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
import html

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '12w1foShEkiWhKd1ktgwWi8zJv9icKjuQVwRCe17_SVg'
GLYPHS_RANGE_NAME = "'Proposed Definitions (Glyphs)'!A1:J264"
HUB_TEXTS_RANGE_NAME = "'Writings (Hub)'!A1:P28"
WALL_TEXTS_RANGE_NAME = "'Writings (Wall)'!A1:P68"

def download_sheet_data(range):
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
								range=range).execute()
	values = result.get('values', [])
	return values;

def download_glyphs(fname):
	values = download_sheet_data(GLYPHS_RANGE_NAME)
	glyphs = []
	for r in values[1:]:
		glyphs.append({
			"number": r[0],
			"glyph": r[1],
			"status": r[8],
			"meaning": r[4],
			"reason": r[5],
			"breakdown": r[3],
		})
	
	with open(fname,'w') as f:
		f.write(json.dumps({
			"glyphs": glyphs,
			"at": datetime.datetime.utcnow().timestamp()
		}))

def load_texts():
	with open('texts.json','r') as f:
		return json.load(f)
		
def download_texts(fname, range_str, text_data):
	values = download_sheet_data(range_str)
	texts = []
	for i in range(1,len(values[1:])):
		texts.append({
			"number": i,
			"text": text_data[str(i)],
			"status": values[i][11],
			"literal_translation": values[i][12],
			"translation": values[i][13],
		})
	
	with open(fname,'w') as f:
		f.write(json.dumps({
			"texts": texts,
			"at": datetime.datetime.utcnow().timestamp()
		}))

def load_json_file(fname):
	with open(fname,'r') as f:
		return json.load(f)
		
		
from jinja2 import Environment, FunctionLoader, select_autoescape

def load_template(name):
	with open(f'templates/{name}','r') as f:
		return f.read()
		

def filter_replace_glyph_references(value):
	global glyphs
	in_match = False;
	out = []
	
	glyph_table = {g['number']:g['glyph'] for g in glyphs['glyphs']}
	
	for m in re.split('[#]([0-9]{3})', value):
		if in_match:
			out.append(f'<a href="glyphs.html#glyph_{m}" class="glyph-link text-white ancient-language" onmousemove="glyphMouseMove(event)" onmouseout="glyphMouseOut(event)" data-number="{m}">{html.escape(glyph_table[m])}</a>')
			in_match = False
		else:
			out.append(m)
			in_match = True
			
		
	return ''.join(out)
	
	
def filter_replace_text_references(value):
	global glyphs
	in_match = False
	out = []
	
	#glyph_table = {g['number']:g['glyph'] for g in glyphs['glyphs']}
	
	for m in re.split('Wall ([0-9]{1,2})', value):
		if in_match:
			out.append(f'<a href="wall_texts.html#text_{m}" class="text-link text-white" onmousemove="wallMouseMove(event)" onmouseout="wallMouseOut(event)" data-number="{m}">Wall {m}</a>')
			in_match = False
		else:
			out.append(m)
			in_match = True
			
	text = ''.join(out)
	out = []
		
	in_match = False		
	for m in re.split('Hub ([0-9]{1,2})', text):
		if in_match:
			out.append(f'<a href="hub_texts.html#text_{m}" class="text-link text-white" onmousemove="hubMouseMove(event)" onmouseout="hubMouseOut(event)" data-number="{m}">Hub {m}</a>')
			in_match = False
		else:
			out.append(m)
			in_match = True
			
	return ''.join(out)
	
def filter_augment_glyphs(value):
	global glyphs
	in_match = False;
	out = []
	
	glyph_table = {g['glyph']:g['number'] for g in glyphs['glyphs']}
	
	for c in value:
		if c not in ' \n\r':
			out.append(f'<a href="glyphs.html#glyph_{glyph_table[c]}" class="glyph-link text-white ancient-language" onmousemove="glyphMouseMove(event)" onmouseout="glyphMouseOut(event)" data-number="{glyph_table[c]}">{html.escape(c)}</a>')
		else:
			out.append(c)
		
	return ''.join(out)

jinja_env = Environment(
	loader=FunctionLoader(load_template),
	autoescape=select_autoescape(),
)
jinja_env.filters['replace_glyph_references'] = filter_replace_glyph_references
jinja_env.filters['replace_text_references'] = filter_replace_text_references
jinja_env.filters['augment_glyphs'] = filter_augment_glyphs

def render_template(name, vars):
	with open(f'dist/{name}','w') as f:
		template = jinja_env.get_template(name)
		f.write(template.render(**vars))
	
def render_glyphs_page(hubs, walls, glyphs):
	render_template('glyphs.html', {"hubs": hubs['texts'], "walls": walls['texts'], "glyphs": glyphs['glyphs'], 'at': datetime.datetime.fromtimestamp(glyphs['at'])})

def render_hub_texts_page(hubs, walls, glyphs):
	render_template('hub_texts.html', {"hubs": hubs['texts'], "walls": walls['texts'], "glyphs": glyphs['glyphs'], "texts": hubs["texts"], 'at': datetime.datetime.fromtimestamp(hubs['at'])})
	
def render_wall_texts_page(hubs, walls, glyphs):
	render_template('wall_texts.html', {"hubs": hubs['texts'], "walls": walls['texts'], "glyphs": glyphs['glyphs'], "texts": walls['texts'], 'at': datetime.datetime.fromtimestamp(walls['at'])})
	
global glyphs
if __name__ == '__main__':
	#main()
	#texts = load_texts()
	#download_glyphs('glyphs.json')
	#download_texts('wall_texts.json', WALL_TEXTS_RANGE_NAME, texts['WallTexts'])
	#download_texts('hub_texts.json', HUB_TEXTS_RANGE_NAME, texts['HubTexts'])
	glyphs = load_json_file('glyphs.json')
	hubs = load_json_file('hub_texts.json')
	walls = load_json_file('wall_texts.json')
	render_hub_texts_page(hubs, walls, glyphs)
	render_wall_texts_page(hubs, walls, glyphs)
	render_glyphs_page(hubs, walls, glyphs)