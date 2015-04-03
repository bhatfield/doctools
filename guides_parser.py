#!/usr/bin/env python
#
# Copyright (c) 2012,2013 Appcelerator, Inc. All Rights Reserved.
# Licensed under the Apache Public License (version 2)

import os, shutil, json, sys, re, xml.dom.minidom, pprint, optparse, urllib
from BeautifulSoup import BeautifulSoup

parser = optparse.OptionParser()
parser.add_option("-i", "--input", dest="input",
	help="input", metavar="FILE")
parser.add_option("-o", "--output", dest="output",
	help="output", metavar="FILE")
parser.add_option("-s", "--show_edit_button",
	action="store_true", dest="showEditButton", default=False,
	help="suppress edit button")
(options, args) = parser.parse_args()
if options.output is None or options.input is None:
	print "please provide --input and --output "
	exit()
print options.input
dom = xml.dom.minidom.parse(options.input) # parse an XML file by name
topics = []

dest = os.path.join(options.output)
try:
	shutil.rmtree(dest)
except:
	pass

try:
	os.makedirs(dest)
except:
	pass

# load the whitelist -- wiki links which are *not* the result of errors
try: 
	f = open(os.path.join(os.path.dirname(__file__), 'guides_wiki_whitelist'), 'r')
	list = f.read()
	wiki_whitelist = list.split()
	f.close()
except Exception as e:
	print "Threw an exception" + str(e)
	pass

def node2obj(node):
	if node.nodeType != 1:
		return

	if node.getAttribute('href').find('#') !=-1:
		return

	global topics, dest
	shortname = re.sub('(.*)\.html', '\\1', node.getAttribute('href'))
	dirname = shortname

	dir = os.path.join(dest, 'guides', dirname)
	try:
		os.makedirs(dir)
	except:
		pass
	shutil.copyfile(os.path.join(os.path.dirname(options.input), shortname+'.html'), os.path.join(dir, 'README.html'))

	# do some convertion for imported guides
	f = open(os.path.join(dir, 'README.html'), 'r')
	soup = BeautifulSoup(f.read())
	f.close()

	# process all hyperlinks
	for tag in soup.findAll('a'):
		if not tag.has_key('href'):
			continue

		href = tag['href']

		if href.find('http://') == 0 or href.find('https://') == 0:
			# APIDoc links are included as full URLs
			if re.search('apidoc/mobile/latest/', href):
				# replace links to documentation
				if re.search('apidoc/mobile/latest/.*-method?(\.html)?', href):
					# method - http://developer.appcelerator.com/apidoc/mobile/latest/Titanium.Locale.getString-method.html
					# #!/api/Titanium.UI.Button-method-getBackgroundGradient
					tag['href'] = re.sub('.*/(.*)\.(.*)-method?(\.html)?', '#!/api/\\1-method-\\2', href)
				elif re.search('apidoc/mobile/latest/.*-property?(\.html)?', href):
					# property - http://developer.appcelerator.com/apidoc/mobile/latest/Titanium.Locale.getString-property.html
					# #!/api/Titanium.UI.Button-property-backgroundGradient
					tag['href'] = re.sub('.*/(.*)\.(.*)-property?(\.html)?', '#!/api/\\1-property-\\2', href)
				elif re.search('apidoc/mobile/latest/.*-event?(\.html)?', href):
					# event - http://developer.appcelerator.com/apidoc/mobile/latest/Titanium.Locale.getString-event.html
					# #!/api/Titanium.UI.Button-event-click
					tag['href'] = re.sub('.*/(.*)\.(.*)-event?(\.html)?', '#!/api/\\1-event-\\2', href)
				elif re.search('apidoc/mobile/latest/.*', href):
					# http://developer.appcelerator.com/apidoc/mobile/latest/Titanium.XML.DOMDocument-object.html
					tag['href'] = re.sub(r'.*/([\w\.]*)(\-(module|object))?(\.html)?', '#!/api/\\1', href)
				else:
					print "Unprocessed " + href
					pass

			# Rewrite any absolute links to http://docs.appcelerator.com/titanium into local 
			# links to avoid page reloads.  At present, we ignore any version in the URL and 
			# assume that any links  are indented to link to the current version of the doc.
			#           
			# The wiki export is now urlencoding the fragment, so we need to decode it first.
			elif re.search('http://docs.appcelerator.com/titanium/.*#.*', href):
				fragment = re.sub('http://docs.appcelerator.com/titanium/.*#', '', href)
				fragment = urllib.unquote(fragment)
				if fragment.startswith('!'):
					tag['href'] = '#' + fragment

			elif re.search('http://docs.appcelerator.com/cloud/latest/.*#.*', href):
				fragment = re.sub('http://docs.appcelerator.com/cloud/latest/.*#', '', href)
				fragment = urllib.unquote(fragment)
				if fragment.startswith('!'):
					tag['href'] = '/arrowdb/latest/#' + fragment

			elif re.search('http://docs.appcelerator.com/arrowdb/latest/.*#.*', href):
				fragment = re.sub('http://docs.appcelerator.com/arrowdb/latest/.*#', '', href)
				fragment = urllib.unquote(fragment)
				if fragment.startswith('!'):
					tag['href'] = '/arrowdb/latest/#' + fragment

			elif re.search('http://docs.appcelerator.com/platform/latest/.*#.*', href):
				fragment = re.sub('http://docs.appcelerator.com/platform/latest/.*#', '', href)
				fragment = urllib.unquote(fragment)
				if fragment.startswith('!'):
					tag['href'] = '#' + fragment

			## HACK: Need a better way to handle this
			elif href.startswith('https://wiki.appcelerator.org/display/guides2/Installing+Platform+SDKs'):
				tag['href'] = 'platform/latest/#!/guide/Installing_Platform_SDKs'

			# In general, any link back to the wiki is a bad link.
			# There are a very few exceptions, such as the community wiki.
			elif href.startswith('https://wiki.appcelerator.org'):
				whitelisted = False
				for url in wiki_whitelist:
					if href.startswith(url):
						whitelisted = True
				if not whitelisted:
					print 'Warning: unconverted wiki link (' + href + ') while processing ' + dir
			else:
				# open external links in new windows/tabs
				tag['target'] = '_blank'
				tag['href'] = urllib.unquote(href)
				pass
		# otherwise, we're looking at an internal guides link.
		else:
			if href.find(' '):
				# no matter what kind of link it is, replace spaces
				href = href.replace(' ', '_')
				tag[href] = href
			if re.search('.*?\.html#', href):
				# replace links to other guides with hash anchors
				# removing hashes because they break jsduck navigation
				tag['href'] = re.sub('(.*?)\.html#(.*)', '#!/guide/\\1-section-\\2', href)
			elif re.search('.*?\.html', href):
				# replace links to other guides
				# removing hashes because they break jsduck navigation
				tag['href'] = re.sub('(.*?)\.html(.*)', '#!/guide/\\1', href)
			else:
				#print href
				pass

	for tag in soup.findAll('link'):
		if not tag.has_key('href'):
			continue;
		del tag['href']	

	if (options.showEditButton):
		content = soup.find("div", {"class":"content"})
		if (content and dir.find('Release_Notes') == -1):
			id = content['id']
			wiki_url = 'https://wiki.appcelerator.org/pages/editpage.action?pageId=' + id
			button = BeautifulSoup('<a id="editButton" href = "' + wiki_url + '"><span>Edit</span></a>')
			content.insert(0, button)
	f = open(os.path.join(dir, 'README.html'), 'w')
	f.write(soup.renderContents())
	f.close()

	res = {
		"name": dirname,
		"title": node.getAttribute('label'),
		"items": []
	}

	for node in node.childNodes:
		res['items'].append(node2obj(node))

	res['items'] = filter(None, res['items'])

	if len(res['items']) == 0:
		del res['items']


	return res


for node in dom.documentElement.childNodes:
	if node.nodeType != 1:
		continue
	obj = node2obj(node)
	if obj == None:
		continue
	topics.append(obj)

# Ok, we've parsed document tree into tree structure.
f = open(os.path.join(dest, 'guides.json'), 'w')
f.write(json.dumps(topics, indent=4))
f.close()
