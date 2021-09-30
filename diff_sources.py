import myers
import json

def load_texts(fname):
	with open(fname,'r', encoding="utf8") as f:
		return json.load(f)
		
		
new_texts = load_texts('texts.json')
old_texts = load_texts('texts_old.json')

def print_diff(a,b):
	out = []
	d = myers.diff(a,b)
	for k,c in d:
		if k == myers.KEEP:
			out.append(c)
		elif k == myers.INSERT:
			out.append('[+'+c+']')
		elif k == myers.REMOVE:
			out.append('[-'+c+']')
		elif k == myers.OMIT:
			out.append('[?'+c+']')
	return ','.join(out)
	
# for i in range(len(new_texts['WallTexts'].values())):
# 	print(i+1)
# 	print(print_diff(old_texts['WallTexts'][str(i+1)]['text'], new_texts['WallTexts'][str(i+1)]['text']))

def generate_diffs(tl1, tl2):
	if len(tl1.values()) != len(tl2.values()):
		raise Exception('Input dicts not of same length')
		
	out = {}
	for i in range(len(tl1.values())):
		num = str(i+1)
		t1 = tl1[num]
		t2 = tl2[num]
		out[num] = {'where': t1['where'], 'index': i+1, 'diff': myers.diff(t1['text'], t2['text'])}
	return out

with open('diffs.json','w') as f:
	json.dump({
		'WallTexts': generate_diffs(old_texts['WallTexts'],new_texts['WallTexts']),
		'HubTexts': generate_diffs(old_texts['HubTexts'],new_texts['HubTexts']),
        'SecretTexts': {str(i+1): {'where': new_texts['SecretTexts'][str(i+1)]['where'], 'index': i+1, 'diff': [['i', c] for c in new_texts['SecretTexts'][str(i+1)]['text']]} for i in range(len(new_texts['SecretTexts'].values()))}
	}, f)
