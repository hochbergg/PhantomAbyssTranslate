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
import shutil
from pyquery import PyQuery as pq

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '12w1foShEkiWhKd1ktgwWi8zJv9icKjuQVwRCe17_SVg'
GLYPHS_RANGE_NAME = "'Proposals (Glyphs)'!A1:J271"
HUB_TEXTS_RANGE_NAME = "'Hub (Writings)'!A1:P28"
WALL_TEXTS_RANGE_NAME = "'Wall (Writings)'!A1:P68"

def download_sheet_data(range):
	"""Shows basic usage of the Sheets API.
	Prints values from a sample spreadsheet.
	"""
	creds = None
	# The file token.json stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists('credentials/token.json'):
		creds = Credentials.from_authorized_user_file('credentials/token.json', SCOPES)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				'credentials/credentials.json', SCOPES)
			creds = flow.run_local_server(port=0)
		# Save the credentials for the next run
		with open('credentials/token.json', 'w') as token:
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
	for i in range(1,len(values)):
		texts.append({
			"number": i,
			"text": text_data[str(i)],
			"status": values[i][13] if len(values[i]) > 13 else '',
			"literal_translation": values[i][9]  if len(values[i]) > 9 else '',
			"translation": values[i][10]  if len(values[i]) > 10 else '',
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
	with open(f'docs/{name}','w') as f:
		template = jinja_env.get_template(name)
		f.write(template.render(**vars))
	
def render_glyphs_page(hubs, walls, glyphs):
	render_template('glyphs.html', {"hubs": hubs['texts'], "walls": walls['texts'], "glyphs": glyphs['glyphs'], 'at': datetime.datetime.fromtimestamp(glyphs['at'])})

def render_hub_texts_page(hubs, walls, glyphs):
	render_template('hub_texts.html', {"hubs": hubs['texts'], "walls": walls['texts'], "glyphs": glyphs['glyphs'], "texts": hubs["texts"], 'at': datetime.datetime.fromtimestamp(hubs['at'])})
	
def render_wall_texts_page(hubs, walls, glyphs):
	render_template('wall_texts.html', {"hubs": hubs['texts'], "walls": walls['texts'], "glyphs": glyphs['glyphs'], "texts": walls['texts'], 'at': datetime.datetime.fromtimestamp(walls['at'])})

def copy_file_to_dist(fname):
	shutil.copy(fname, 'docs/')

def copy_dir_to_dist(dirname, targetname):
	if os.path.isdir('docs/'+targetname):
		shutil.rmtree('docs/'+targetname)
	shutil.copytree(dirname, 'docs/'+targetname)	

def parse_style(style):
	stm = {a.strip(): b.strip() for (a,b) in (x.split(':') for x in style.split(';') if len(x.strip()) > 0)}
	return stm
	
def parse_grammar_guide_html(tag):
	if tag.is_('body'):
		out = []
		for c in tag.children():
			p = parse_grammar_guide_html(pq(c))
			if p['type'] != 'skip':
				out.append(p)
		return {'type': 'body', 'contents': out}
	
	elif tag.is_('h1'):
		return {'type': 'h1', 'text': tag.text(), 'class': tag.attr('class')}
		
	elif tag.is_('h2'):
		return {'type': 'h1', 'text': tag.text(), 'class': tag.attr('class')}
		
	elif tag.is_('h3'):
		return {'type': 'h3', 'text': tag.text(), 'class': tag.attr('class')}
		
	elif tag.is_('h4'):
		return {'type': 'h4', 'text': tag.text(), 'class': tag.attr('class')}
			
	elif tag.is_('p'):
		out = []
		for c in tag.children():
			p = parse_grammar_guide_html(pq(c))
			if p['type'] != 'skip':
				out.append(p)
		if len(out) > 0:
			return {'type': 'paragraph', 'contents': out, 'class': tag.attr('class')}
		else:
			return {'type': 'skip'}
		
	elif tag.is_('ul'):
		out = []
		for c in tag.children():
			out.append(parse_grammar_guide_html(pq(c)))
		return {'type': 'bullet-list', 'contents': out, 'class': tag.attr('class')}
		
	elif tag.is_('li'):
		out = []
		for c in tag.children():
			out.append(parse_grammar_guide_html(pq(c)))
		return {'type': 'list-item', 'contents': out, 'class': tag.attr('class')}
		
	elif tag.is_('span'):
		image = tag.children('img')
		if len(image) == 0:
			txt = tag.text().strip()
			if len(txt) > 0:
				return {'type': 'text', 'text': tag.text(), 'class': tag.attr('class')}
			else:
				return {'type': 'skip'}
		else:
			style = parse_style(image.attr['style'])
			return {'type': 'image', 'url': image.attr['src'], 'width': style['width'], 'height': style['height'], 'class': tag.attr('class')}
	
	else:
		# 'tagname': tag.prop('tagname'), 
		print("Unknown Tag", tag.outer_html())
		return {'type': 'unknown', 'html': tag.outer_html()}
	
def import_grammar_guide():
	with open('Phantom Abyss Grammar/PhantomAbyssGrammar.html','r') as f:
		d = pq(f.read())
		
	b = d("body")
	p = parse_grammar_guide_html(b)
	
	return p['contents']
			
	
FILES_TO_COPY = ['AncientLanguage.otf', 'hovers.js', 'solar.bootstrap.min.css', 'tool.html']

global glyphs
if __name__ == '__main__':
	texts = load_texts()
	download_glyphs('tmp/glyphs.json')
	download_texts('tmp/wall_texts.json', WALL_TEXTS_RANGE_NAME, texts['WallTexts'])
	download_texts('tmp/hub_texts.json', HUB_TEXTS_RANGE_NAME, texts['HubTexts'])
	glyphs = load_json_file('tmp/glyphs.json')
	hubs = load_json_file('tmp/hub_texts.json')
	walls = load_json_file('tmp/wall_texts.json')
	render_hub_texts_page(hubs, walls, glyphs)
	render_wall_texts_page(hubs, walls, glyphs)
	render_glyphs_page(hubs, walls, glyphs)
	render_template('index.html', {'glyphs': glyphs['glyphs']})
	render_template('about.html', {'glyphs': glyphs['glyphs']})
	render_template('grammar.html', {'glyphs': glyphs['glyphs']})
	
	render_template('grammar.html', {'grammar_body': import_grammar_guide(), 'glyphs': glyphs['glyphs']})
	copy_dir_to_dist('Phantom Abyss Grammar/images','images')
	
	
	#for f in FILES_TO_COPY:
		#copy_file_to_dist(f)