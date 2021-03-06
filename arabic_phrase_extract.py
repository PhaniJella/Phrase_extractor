# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import networkx as nx
import PETRgraph
import sys


def run():
	events = read_xml_input(filepaths)
	updated_events = extract_phrases(events)
	write_phrases(updated_events)

def _format_ud_parsed_str(parsed_str):
    
    parsed = parsed_str.split('\n')
    cleanparsed=[]
    for p in parsed:
    	if len(p.split("\t"))==8:
    		cleanparsed.append(p)
    	else:
    		print("number of field is not 8"+p)


    treestr = '\n'.join(cleanparsed)
    return treestr

def read_xml_input(filepaths, parsed=False):
	
	eventdict = {}

	for path in filepaths:
		tree = ET.iterparse(path)

		for event, elem in tree:
			if event == "end" and elem.tag == "Sentence":
				story = elem

				# Check to make sure all the proper XML attributes are included
				attribute_check = [key in story.attrib for key in ['date', 'id', 'sentence', 'source']]
				if not attribute_check:
					print('Need to properly format your XML...')
					break

				if parsed:
					parsed_content = story.find('Parse').text
					parsed_content = _format_ud_parsed_str(parsed_content)
				#print(parsed_content) # add graph
				else:
					parsed_content = ''

				if story.attrib['sentence'].lower() == 'true':
					entry_id =  story.attrib['id'][0:story.attrib['id'].rindex('_')]
					sent_id = story.attrib['id'][story.attrib['id'].rindex('_')+1:]

					text = story.find('Text').text
					text = text.replace('\n', ' ').replace('  ', ' ')
					sent_dict = {'content': text, 'parsed': parsed_content}
					meta_content = {'date': story.attrib['date'],
					'source': story.attrib['source']}
					content_dict = {'sents': {sent_id: sent_dict},
					'meta': meta_content}
				else:
					entry_id = story.attrib['id']

					text = story.find('Text').text
					text = text.replace('\n', ' ').replace('  ', ' ')
					#split_sents = _sentence_segmenter(text)
			
					# TODO Make the number of sents a setting
					sent_dict = {}
					#for i, sent in enumerate(split_sents[:7]):
					#	sent_dict[i] = {'content': sent, 'parsed':
					#	parsed_content}

					#	meta_content = {'date': story.attrib['date']}
					#	content_dict = {'sents': sent_dict, 'meta': meta_content}

				if entry_id not in eventdict:
					eventdict[entry_id] = content_dict
				else:
					eventdict[entry_id]['sents'][sent_id] = sent_dict

				elem.clear()

	return eventdict



def extract_phrases(event_dict):
	NStory = 0
	NSent = 0

	for key, val in sorted(event_dict.items()):
		NStory += 1
		print('\n\nProcessing story {}'.format(key))
		StoryDate = event_dict[key]['meta']['date']

		for sent in val['sents']:
			NSent += 1
			print('Processing sentence ' + sent)
			if 'parsed' in event_dict[key]['sents'][sent]:
				SentenceText = event_dict[key]['sents'][sent]['content']
				SentenceParsed = event_dict[key]['sents'][sent]['parsed']
				SentenceDate = event_dict[key]['sents'][sent]['date'] if 'date' in event_dict[key]['sents'][sent] else StoryDate
				Date = SentenceDate
				sentence = PETRgraph.Sentence(SentenceParsed,SentenceText,Date)
				#print(sentence.udgraph.node[1]['pos'])
				#print(sentence.udgraph.edges())
				#print(nx.dfs_successors(sentence.udgraph,6))

				sentence.get_phrases()
				print('verbs:')
				for v in sentence.metadata['verbs']: print(v)
				print('nouns:')
				for n in sentence.metadata['nouns']: print(n)
				print('triplets:')
				for triple in sentence.metadata['triplets']: print("s: "+triple[0]+"\tt: "+triple[1]+"\tv: "+triple[2]+"\to: "+(" ").join(triple[3])+"\n")
						
				event_dict[key]['sents'][sent]['phrase_dict'] = sentence.metadata

			#raw_input("Press Enter to continue...")

	return event_dict


def write_phrases(event_dict,outputfile):
	output=[]
	output.append("<Sentences>\n")
	for key, val in sorted(event_dict.items()):
		
		StoryDate = event_dict[key]['meta']['date']

		for sent in val['sents']:
			#source = key[0:key.index('_')]
			output.append("<Sentence date = \""+StoryDate+"\" id=\""+key+"_"+sent+"\" source = \""+key+"\" sentence = \"True\">\n")
			output.append("<Text>"+event_dict[key]['sents'][sent]['content']+"</Text>\n")
			output.append("<Parse>\n"+event_dict[key]['sents'][sent]['parsed']+"\n</Parse>\n")
			output.append("<Verbs>\n")
			for v in event_dict[key]['sents'][sent]['phrase_dict']['verbs']:
				output.append(v+"\n")
			output.append("</Verbs>\n")

			output.append("<Nouns>\n")
			for n in event_dict[key]['sents'][sent]['phrase_dict']['nouns']:
				output.append(n+"\n")
			output.append("</Nouns>\n")

			output.append("<Tuples>\n")
			for triple in event_dict[key]['sents'][sent]['phrase_dict']['triplets']:
				output.append("source: "+triple[0]+"\ttarget: "+triple[1]+"\tverb: "+triple[2]+"\tother_noun: "+(" ").join(triple[3])+"\n")
			output.append("</Tuples>\n")

			output.append("</Sentence>\n")

	output.append("</Sentences>\n")



	ofile = open(outputfile,'w')
	for line in output:
		ofile.write(line.encode('utf8'))
	ofile.close()



inputFile=sys.argv[1].replace(".xml","")+"_parsed.xml"
outputFile = inputFile.replace(".xml","")+"_phrase.xml"
events = read_xml_input([inputFile], True)
updated_events = extract_phrases(events)
write_phrases(updated_events,outputFile)
