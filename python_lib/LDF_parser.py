from lark import Lark
json_parser = Lark(open("ldf.lark"),parser="lalr")

f=open("D:\\example.ldf", "r").read()
tree = json_parser.parse(f)
print(tree)