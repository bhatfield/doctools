import json, re, sys

solr_category = "arrowdb"

# Helper function to convert unicode string to ASCII
def u2a(str):
	if isinstance(str, unicode):
		return str.encode('ascii', 'ignore')
	else:
		return str

# Helper to strip HTML tags and replace new lines with spaces
from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    t = s.get_data()
    t = " ".join(t.split("\n"))
    return t

def dict_has_non_empty_member(d, member_name):
        return member_name in d and d[member_name] is not None and len(d[member_name]) > 0

def parse_params(params):
	new_params = ""

	for elem in params:
		new_elem = ""
		new_elem = new_elem + " " + elem["name"]
		new_elem = new_elem + " " + elem["doc"]
		new_params = new_params + " " + u2a(new_elem)

	return new_params

def parse_examples(examples):
	new_examples = ""

	for elem in examples:
		new_elem = ""
		new_elem += " " + elem["platform"]
		new_elem += " " + elem["doc"]
		new_examples += " " + u2a(new_elem)

	return new_examples


def parse_members(members):
	new_members = []
	for api in members:
		extra_desc = ""
		new_api = {}
		new_api["id"] = u2a(api["owner"] + "-" + api["tagname"] + "-" + api["name"] + "-" + solr_category)
		new_api["url"] = u2a(api["owner"] + "-" + api["tagname"] + "-" + api["name"])
		new_api["type"] = solr_category
		new_api["name"] = u2a(api["owner"] + "." + api["name"])

		if api["tagname"] == "property":
			extra_desc += u2a(api["type"]) + " " + extra_desc

		if api["tagname"] == "method":
			extra_desc += " " + u2a(api["httpMethod"]) + " " + u2a(api["url"]);
			if dict_has_non_empty_member(api, "params"):
				extra_desc = extra_desc + " " + parse_params(api["params"])
			returnz = {}
			if api["return"] is not None:
				returnz["type"] = u2a(api["return"]["type"])
				if returnz["type"] == "undefined":
					extra_desc = extra_desc + " return void"
				else:
					extra_desc = extra_desc + " return " + returnz["type"]
					parse_dict = u2a(api["return"]["doc"])
					if re.sub(r'[^\s]', '', parse_dict) is not None:
						 extra_desc = extra_desc + " " + parse_dict

			if dict_has_non_empty_member(api, "examples"):
				extra_desc = extra_desc + " " + parse_examples(api["examples"])

		new_api["content"] = u2a(api["doc"]) + " " + u2a(extra_desc)
		new_api["content"] = strip_tags(new_api["content"])

		new_members.append(new_api)
	return new_members


if len(sys.argv) < 3 or re.search("help", sys.argv[1]):
	print "jsduck2json.py <input_file.json> <output_file.json>"
	sys.exit(0)

input_file = sys.argv[1]
output_file = sys.argv[2]

json_data=open(input_file)
data = json.load(json_data)
export_data = []
for obj in data:
	if obj["tagname"] == "class":
		new_obj = {}
		new_obj["name"] = u2a(obj["name"])
		new_obj["id"] = u2a(obj["name"] + "-" + solr_category)
		new_obj["url"] = u2a(obj["name"])
		new_obj["type"] = solr_category
		new_obj["content"] = strip_tags(u2a(obj["doc"]))

		export_data.append(new_obj)

		properties = parse_members(obj["members"]["property"])
		if properties is not None:
			for property in properties:
				if property is not None:
					export_data.append(property)

		methods = parse_members(obj["members"]["method"])
		if methods is not None:
			for method in methods:
				if method is not None:
					export_data.append(method)

json_data.close()

file=open(output_file, 'w')
json.dump(export_data, file, indent=4, separators=(',', ': '))
file.close()
