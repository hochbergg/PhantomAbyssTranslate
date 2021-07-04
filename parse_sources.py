import json

def parse_texts(fname):
	current_text = []
	out = []
	with open(fname, 'r') as f:
		for l in f:
			ll = l.replace('\n','')
			if len(ll) == 0:
				out.append('\n'.join(current_text))
				current_text = []
			else:
				current_text.append(ll)
	
	if len(current_text) != 0:
		out.append('\n'.join(current_text))
		
	return out
			
wall_texts = parse_texts('sources/WallsText.txt')
hub_texts = parse_texts('sources/HubText.txt')

extra_data = {
	"conceptSeparators": ["Ē","ĕ",">","»","Á","Ñ","Ò","ò","Ć","ē","Ĕ","ĕ","Ė","ě","Ĝ","ĝ","ı","Ĳ","ĳ","Ĵ","œ","\n"],
	"verbSignifers": ["Ē","ē","Ĕ","ě","Ĝ","ĝ","ı","Ĳ","ĳ"],
	"ignoredGlyphs": ["Ɗ","Ɨ","Ƌ"," "],
	"nameOrDateStart": ["Ɗ","Ɨ","Ƌ"],
	"nameOrDateEnd": [" "]
}

with open('texts.json','w') as f:
	d = {
		'WallTexts': {str(i+1): {'where': 'Wall', 'index': i+1, 'text': wall_texts[i]} for i in range(len(wall_texts))},
		'HubTexts': {str(i+1): {'where': 'Hub', 'index': i+1, 'text': hub_texts[i]} for i in range(len(hub_texts))},
	}
	
	all_glyphs = []
	for t in d['WallTexts'].values():
		all_glyphs.extend(list(t['text']))
		
	for t in d['HubTexts'].values():
		all_glyphs.extend(list(t['text']))
	
	all_glyphs = set(all_glyphs)
	all_glyphs.remove('\n')
	all_glyphs.remove(' ')
	all_glyphs = sorted(list(all_glyphs))
	
	print(all_glyphs)
	
	d['allGlyphs'] = all_glyphs
	
	d.update(extra_data)
	
	f.write(json.dumps(d, indent=4))
	