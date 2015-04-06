import json

from polyline.codec import PolylineCodec as PC

def get_json(*paths):
    all_json = []
    for path in paths:
        with open(path, 'r') as f:
            data = f.read()
        j = json.loads(data)
        pc = PC()
        for item in j:
            item['path'] = pc.decode(item['path'])
        all_json.extend(j)
    return all_json
          
