from lark import Lark, Transformer
from ucanlintools.LINFrame import *

def ParseIntOrHex(x):
    try:
        return (int(x))
    except ValueError:
        return (int(x,16)) 



class LDF:
    """LDF parsing class.    
    
    Parameters
        ----------
        nodes : lin nodes
            The name of the animal
        frames : lin frames with id and signals description
        
    """

    def __init__(self,nodes, frames, signals):
        self.nodes = nodes
        lin_frames  = []
        for f in frames:
            for fs in f['frame_signals']:
                for s in signals:
                    if (fs['name'] == s['signal_name']):
                        fs.update(s)
                        del fs['signal_name']
            lin_frames.append(LINFrame(f['frame_id'], f['frame_len'], f['frame_name'], f['frame_signals'], f['publisher'] ) )                        
        self.frames = lin_frames
        
    
    def get_message_by_name(self, name):
        """Get Message by message name
        
        Returns
        ----------
        LINFrame object
        """
        for f in self.frames:
            if (f.name == name):
                return f
        return
    def get_message_by_id(self, fid):
        """Get Message by message id
        
        Returns
        ----------
        LINFrame object
        """
        for f in self.frames:
            if (f.id == fid):
                return f
        return


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
    """Parse LDF file
        
    Returns
    ----------
    LDF object
    """
    # json_parser = Lark(open("..\ucanlintools\ldf.lark"),parser="lalr")
    json_parser = Lark(''' 
    start: ldf_container

?ldf_container: ldf_header [(ldf_nodes | ldf_signals | ldf_frames | ldf_diagnostic | ldf_diagnostic_frames | ldf_node_atributes | ldf_schedule_table | ldf_signal_encoding_types | ldf_signal_representation)*]

?ldf_nodes : "Nodes" "{" [ldf_node_master] [ldf_node_slaves] "}" 
?ldf_signals : "Signals" "{" [ldf_signal (ldf_signal)*] "}"  
?ldf_frames : "Frames" "{" [ldf_frame (ldf_frame)*] "}" 

?ldf_diagnostic : "Diagnostic_signals" "{" [(ANY_SEMICOLON_TERMINATED_LINE)*] "}"
?ldf_diagnostic_frames : "Diagnostic_frames" "{" [(ldf_diagnostic_master_req | ldf_diagnostic_slave_resp)*] "}"

?ldf_diagnostic_master_req: "MasterReq:" [C_INT] "{" [(ANY_SEMICOLON_TERMINATED_LINE)*] "}"
?ldf_diagnostic_slave_resp: "SlaveResp:" [C_INT] "{" [(ANY_SEMICOLON_TERMINATED_LINE)*] "}"

?ldf_node_atributes: "Node_attributes" "{" ldf_node_atributes_node? "}"
?ldf_node_atributes_node: ANY_OPENED_BLOCK [ANY_SEMICOLON_TERMINATED_LINE*] ANY_OPENED_BLOCK [ANY_SEMICOLON_TERMINATED_LINE*] "}" "}"

?ldf_schedule_table: "Schedule_tables" "{" [ldf_schedule_table_node*] "}" 
?ldf_schedule_table_node: ANY_OPENED_BLOCK [ANY_SEMICOLON_TERMINATED_LINE*] "}"

?ldf_signal_encoding_types: "Signal_encoding_types" "{" [ldf_signal_encoding_types_node*] "}" 
?ldf_signal_encoding_types_node: ANY_OPENED_BLOCK [(ANY_SEMICOLON_TERMINATED_LINE*)] ["}"] [ANY_CLOSED_BLOCK]

?ldf_signal_representation: "Signal_representation" "{" [ldf_signal_representation_node*] "}" 
?ldf_signal_representation_node: [(ANY_COLON_TERMINATED_LINE | ANY_SEMICOLON_TERMINATED_LINE)*]

?ldf_node_master: "Master:" ldf_node_name "," /.*;/  
?ldf_node_slaves: "Slaves:" ldf_node_name? ";" 

ldf_node : ldf_signal_name  ":" ldf_node_name ";" 
ldf_signal :  ldf_signal_name ":" ldf_signal_size "," ldf_signal_default_value "," ldf_node_name "," ldf_node_name ";" 
ldf_frame : ldf_frame_name  ":" ldf_frame_id "," ldf_node_name "," ldf_frame_len ["{" (ldf_frame_signal)* "}"] 


ldf_frame_signal: ldf_signal_name "," ldf_signal_bit_offset ";" 
ldf_frame_name: CNAME 
ldf_frame_id : C_INT 
ldf_frame_len : C_INT 

ldf_signal_default_value: C_INITIALIZER_LIST|C_INT 
ldf_signal_size: C_INT 
ldf_signal_bit_offset: C_INT 
ldf_signal_name: CNAME 

ldf_node_name: CNAME 

ANY_OPENED_BLOCK: /.*{/
ANY_CLOSED_BLOCK: /.*}/

ANY_SEMICOLON_TERMINATED_LINE: /.*;/
ANY_COLON_TERMINATED_LINE: /.*,/



C_INITIALIZER_LIST: ("{"|"{ ") C_INT ([","|", "]C_INT)* ("}"|" }")
C_INT: ("0x"HEXDIGIT+) | ("-"? HEXDIGIT+) 

ldf_header: (ldf_header_lin | ldf_header_channel)*  
ldf_header_lin : "LIN_"/.*;/
ldf_header_channel : "Channel_name"/.*;/

%import common._STRING_INNER

%import common.HEXDIGIT 
%import common.INT
%import common.WORD
%import common.CNAME
%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER
%import common.WS
%import common.WS_INLINE
%ignore WS
%ignore WS_INLINE
    
    
    
    ''',parser="lalr")

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
