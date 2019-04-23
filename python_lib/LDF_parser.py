from lark import Lark
from lark import Transformer

def ParseIntOrHex(x):
    try:
        return (int(x))
    except ValueError:
        return (int(x,16)) 

class LDF:
    def __init__(self,nodes, frames, signals):
        self.nodes = nodes
        self.frames = frames
        self.signals = signals


class TreeToJson(Transformer):
    def ldf_node_name(self,s):
        return s[0][0:]
    def signal_name(self, s):
        return s[0][0:]
    def signal_size(self, s):
        return ParseIntOrHex(s[0])
    def signal_bit_offset(self, s):
        return ParseIntOrHex(s[0])
    def ldf_node_master(self,s):
        return s[0][0:]
    def ldf_node_slaves(self,s):
        return s[0][0:]

    def ldf_nodes(self,s):
        return {'nodes':s}
    def ldf_signals(self,s):
        return {'signals': s}
    def ldf_frames(self,s):
        return {'frames': s}
   
    # ldf_container = dict
    def ldf_container(self,s):
        return s

    def ldf_signal(self,s):
        return {'signal_name':s[0], 'size_bits':s[1], 'default_val': s[2], 'publisher': s[3], 'subscriber': s[4]}
    def ldf_frame(self,s):
        return {'frame_name':s[0], 'frame_id':s[1], 'publisher':s[2], 'frame_len':s[3], 'frame_signals':s[4:]}
    def ldf_frame_signal(self,s):
        return {'name':s[0],'bit_offset':s[1]}
    def ldf_frame_name(self,s):
        return s[0][0:] 
    def ldf_frame_id(self,s):
        return ParseIntOrHex(s[0])
    def ldf_frame_len(self,s):
        return ParseIntOrHex(s[0])
    def ldf_signal_size(self,s):
        return ParseIntOrHex(s[0])
    def ldf_signal_bit_offset(self,s):
        return ParseIntOrHex(s[0])
    def ldf_signal_name(self,s):
        return s[0][0:]

    def ldf_signal_default_value(self,s):
        s = s[0]
        s = s.replace('{','').replace('}','').split(',')
        o = []
        for x in s:
            o.append(ParseIntOrHex(x))
        return o

    # start = dict 
    def start(self,s):
        return s[0]

    def ldf_node_atributes(self,s):
        return
        # return {"ldf_node_atributes" : "NOT_IMPLEMENTED"}
    def ldf_node_atributes_node(self,s):
        return
        # return {"ldf_node_atributes_node" : "NOT_IMPLEMENTED"}

    def ldf_schedule_table(self,s):
        return
        # return {"ldf_schedule_table" : "NOT_IMPLEMENTED"}
    def ldf_signal_representation(self,s):
        return
        # return {"ldf_signal_representation" : "NOT_IMPLEMENTED"}
    def ldf_signal_representation_node(self,s):
        return
        # return {"ldf_signal_representation_node" : "NOT_IMPLEMENTED"}
    def ldf_signal_encoding_types(self,s):
        return
        # return {"ldf_signal_encoding_types" : "NOT_IMPLEMENTED"}
    def ldf_diagnostic(self,s):
        return
        # return {"ldf_diagnostic" : "NOT_IMPLEMENTED"}
    def ldf_diagnostic_frames(self,s):
        return
        # return {"ldf_diagnostic_frames" : "NOT_IMPLEMENTED"}
    def ldf_header(self,s):
        return
        # return {"ldf_header" : "NOT_IMPLEMENTED"}


def parseLDF(file):
    json_parser = Lark(open("ldf.lark"),parser="lalr")

    f=open(file, "r").read()
    tree = json_parser.parse(f)
    # print(tree.pretty())
    
    json_data = TreeToJson().transform(tree)
    ldf = {}
    for a in json_data:
        if (a != None):
            ldf.update(a)

    out_ldf = LDF(ldf['nodes'],ldf['frames'],ldf['signals']) 
    

    return out_ldf
