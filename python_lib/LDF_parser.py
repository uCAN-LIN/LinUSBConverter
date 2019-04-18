from lark import Lark
from lark import Transformer

def ParseIntOrHex(x):
    try:
        return (int(x))
    except ValueError:
        return (int(x,16)) 

class LdfTransformer(Transformer):
    def ldf_signal(self, data):
        n,s,d,nm,ns = data
        return n,s,d,nm,ns 
    def ldf_frame(self, data):
        n,i,nn,l,*signals = data
        return n,i,nn,l,list(signals)
    def ldf_frame_signal(self,data):
        n,bo = data
        return n, bo

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

    # def ldf_node(self,s):
        # return s

    def ldf_nodes(self,s):
        return {'nodes':s}
    def ldf_signals(self,s):
        return {'signals': s}
    def ldf_frames(self,s):
        return {'frames': s}
    def ldf_container(self,s):
        return {'ldf': s}
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

    start = list   

    

json_parser = Lark(open("ldf.lark"),parser="lalr")

# f=open("/mnt/d/example.ldf", "r").read()

f=open("D:\\example.ldf", "r").read()
tree = json_parser.parse(f)
print(tree.pretty())

json_data = TreeToJson().transform(tree)

LdfTransformer().transform(tree)

